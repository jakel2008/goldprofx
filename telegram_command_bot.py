import json
import os
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path

import requests

try:
    from vip_subscription_system import SubscriptionManager  # type: ignore
except Exception:
    SubscriptionManager = None  # type: ignore


class TelegramCommandBot:
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir or Path(__file__).parent)
        self.bots_config_file = self.base_dir / 'bots_config.json'
        self.state_file = self.base_dir / 'telegram_command_bot_state.json'
        self.users_db = self.base_dir / 'users.db'
        self.subscriptions_db = self.base_dir / 'vip_subscriptions.db'
        self.poll_interval = max(1, int(os.environ.get('TELEGRAM_COMMAND_POLL_INTERVAL', '2')))
        self.request_timeout = max(10, int(os.environ.get('TELEGRAM_COMMAND_TIMEOUT', '30')))
        self.admin_ids = {x.strip() for x in str(os.environ.get('TELEGRAM_ADMIN_IDS', '')).split(',') if x.strip()}
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self.state = {
            'running': False,
            'last_poll_at': None,
            'last_update_id': None,
            'last_error': None,
            'updates_processed': 0,
            'commands_processed': 0,
            'started_at': None
        }
        self.subscription_manager = SubscriptionManager() if SubscriptionManager else None

    def _load_offset(self):
        try:
            if self.state_file.exists():
                data = json.loads(self.state_file.read_text(encoding='utf-8') or '{}')
                offset = data.get('offset')
                if isinstance(offset, int) and offset >= 0:
                    return offset
        except Exception:
            pass
        return None

    def _save_offset(self, offset):
        try:
            self.state_file.write_text(json.dumps({'offset': int(offset), 'updated_at': datetime.now().isoformat()}, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception:
            pass

    def _load_bots_config(self):
        try:
            if not self.bots_config_file.exists():
                return {'bots': []}
            return json.loads(self.bots_config_file.read_text(encoding='utf-8') or '{}')
        except Exception:
            return {'bots': []}

    def _get_bot_token(self):
        env_token = str(os.environ.get('MM_TELEGRAM_BOT_TOKEN', '')).strip()
        if env_token:
            return env_token
        cfg = self._load_bots_config()
        bots = cfg.get('bots', []) if isinstance(cfg, dict) else []
        active = [b for b in bots if isinstance(b, dict) and str(b.get('status', '')).lower() == 'active']
        if not active:
            return ''
        default_bot = next((b for b in active if b.get('is_default')), None)
        selected = default_bot or active[0]
        return str(selected.get('token') or '').strip()

    def _api_get(self, token, method, params=None):
        url = f'https://api.telegram.org/bot{token}/{method}'
        return requests.get(url, params=params or {}, timeout=self.request_timeout)

    def _api_post(self, token, method, payload=None):
        url = f'https://api.telegram.org/bot{token}/{method}'
        return requests.post(url, json=payload or {}, timeout=self.request_timeout)

    def send_message(self, token, chat_id, text):
        try:
            resp = self._api_post(token, 'sendMessage', {'chat_id': str(chat_id), 'text': text, 'parse_mode': 'HTML'})
            data = resp.json()
            return bool(data.get('ok'))
        except Exception:
            return False

    def _is_admin_user(self, telegram_user_id):
        if str(telegram_user_id) in self.admin_ids:
            return True
        try:
            if not self.users_db.exists():
                return False
            conn = sqlite3.connect(self.users_db)
            c = conn.cursor()
            c.execute('PRAGMA table_info(users)')
            cols = {r[1] for r in c.fetchall()}
            if 'is_admin' not in cols:
                conn.close()
                return False
            c.execute('SELECT is_admin FROM users WHERE id = ?', (int(telegram_user_id),))
            row = c.fetchone()
            conn.close()
            return bool(row and int(row[0]) == 1)
        except Exception:
            return False

    def _link_user_chat(self, telegram_user_id, username, chat_id):
        try:
            if not self.subscriptions_db.exists():
                return 0
            conn = sqlite3.connect(self.subscriptions_db)
            c = conn.cursor()
            c.execute('PRAGMA table_info(users)')
            cols = {r[1] for r in c.fetchall()}
            if 'chat_id' not in cols and 'telegram_id' not in cols:
                conn.close()
                return 0
            updates = []
            vals = []
            if 'chat_id' in cols:
                updates.append('chat_id = ?')
                vals.append(str(chat_id))
            if 'telegram_id' in cols:
                updates.append('telegram_id = ?')
                vals.append(int(telegram_user_id))
            linked = 0
            q = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
            c.execute(q, tuple(vals + [int(telegram_user_id)]))
            linked += c.rowcount if c.rowcount else 0
            if username:
                q2 = f"UPDATE users SET {', '.join(updates)} WHERE lower(username)=lower(?)"
                c.execute(q2, tuple(vals + [str(username).strip()]))
                linked += c.rowcount if c.rowcount else 0
            conn.commit()
            conn.close()
            return linked
        except Exception:
            return 0

    def _ensure_user_in_users_db(self, telegram_user_id, username):
        try:
            if not self.users_db.exists():
                return False
            conn = sqlite3.connect(self.users_db)
            c = conn.cursor()
            c.execute('PRAGMA table_info(users)')
            cols = {r[1] for r in c.fetchall()}
            if 'id' not in cols:
                conn.close()
                return False

            c.execute('SELECT id FROM users WHERE id = ?', (int(telegram_user_id),))
            row = c.fetchone()
            if row:
                if username and 'username' in cols:
                    c.execute('UPDATE users SET username = COALESCE(NULLIF(username, ""), ?) WHERE id = ?', (str(username).strip(), int(telegram_user_id)))
                conn.commit()
                conn.close()
                return True

            insert_cols = ['id']
            insert_vals = [int(telegram_user_id)]
            if 'username' in cols:
                insert_cols.append('username')
                insert_vals.append(str(username).strip() if username else f'user_{telegram_user_id}')
            if 'email' in cols:
                insert_cols.append('email')
                insert_vals.append(f'tg_{telegram_user_id}@telegram.local')
            if 'full_name' in cols:
                insert_cols.append('full_name')
                insert_vals.append(str(username).strip() if username else f'Telegram {telegram_user_id}')
            if 'password' in cols:
                insert_cols.append('password')
                insert_vals.append('telegram_login')
            if 'plan' in cols:
                insert_cols.append('plan')
                insert_vals.append('free')
            if 'is_admin' in cols:
                insert_cols.append('is_admin')
                insert_vals.append(1 if str(telegram_user_id) in self.admin_ids else 0)
            if 'is_active' in cols:
                insert_cols.append('is_active')
                insert_vals.append(1)
            if 'created_at' in cols:
                insert_cols.append('created_at')
                insert_vals.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            placeholders = ', '.join(['?'] * len(insert_cols))
            c.execute(f"INSERT INTO users ({', '.join(insert_cols)}) VALUES ({placeholders})", tuple(insert_vals))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def _get_user_plan_info(self, telegram_user_id, username, chat_id):
        try:
            if not self.subscriptions_db.exists():
                return None
            conn = sqlite3.connect(self.subscriptions_db)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('PRAGMA table_info(users)')
            cols = {r[1] for r in c.fetchall()}
            where_parts = []
            params = []
            if 'user_id' in cols:
                where_parts.append('user_id = ?')
                params.append(int(telegram_user_id))
            if 'telegram_id' in cols:
                where_parts.append('telegram_id = ?')
                params.append(int(telegram_user_id))
            if 'chat_id' in cols:
                where_parts.append('chat_id = ?')
                params.append(str(chat_id))
            if username and 'username' in cols:
                where_parts.append('lower(username) = lower(?)')
                params.append(str(username))
            if not where_parts:
                conn.close()
                return None
            q = f"SELECT user_id, username, plan, status, subscription_end FROM users WHERE {' OR '.join(where_parts)} ORDER BY user_id DESC LIMIT 1"
            c.execute(q, tuple(params))
            row = c.fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception:
            return None

    def _plans_text(self):
        if not self.subscription_manager:
            return '⚠️ نظام الاشتراكات غير متاح حالياً.'
        plans = getattr(self.subscription_manager, 'PLANS', {}) or {}
        if not plans:
            return '⚠️ لا توجد خطط متاحة حالياً.'
        lines = ['📦 <b>الخطط المتاحة</b>']
        for name, meta in plans.items():
            lines.append(f"- <b>{name}</b>: ${meta.get('price', 0)} | {meta.get('duration_days', 0)} يوم | {meta.get('signals_per_day', 0)} إشارة/يوم")
        return '\n'.join(lines)

    def _handle_command(self, token, chat_id, telegram_user_id, username, text):
        self.state['commands_processed'] += 1
        parts = text.strip().split()
        cmd = (parts[0] if parts else '').split('@')[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if cmd == '/start':
            saved_user = self._ensure_user_in_users_db(telegram_user_id, username)
            linked = self._link_user_chat(telegram_user_id, username, chat_id)
            msg = (
                '✅ أهلاً بك في بوت GOLD PRO\n'
                'الأوامر: /plans /myplan /admin_test /admin_extend <user_id> <days>\n'
                f"تم حفظ المستخدم: {'نعم' if saved_user else 'لا'}\\n"
                f'تم ربط الحسابات: {linked}'
            )
            self.send_message(token, chat_id, msg)
            return
        if cmd == '/plans':
            self.send_message(token, chat_id, self._plans_text())
            return
        if cmd == '/myplan':
            info = self._get_user_plan_info(telegram_user_id, username, chat_id)
            if not info:
                self.send_message(token, chat_id, '⚠️ لم يتم العثور على اشتراك مرتبط بحسابك.')
                return
            msg = (
                '👤 <b>بيانات اشتراكك</b>\n'
                f"ID: {info.get('user_id')}\n"
                f"Username: {info.get('username')}\n"
                f"Plan: {info.get('plan')}\n"
                f"Status: {info.get('status')}\n"
                f"Ends: {info.get('subscription_end') or 'غير محدد'}"
            )
            self.send_message(token, chat_id, msg)
            return
        if cmd == '/admin_test':
            if not self._is_admin_user(telegram_user_id):
                self.send_message(token, chat_id, '⛔ هذا الأمر للأدمن فقط.')
                return
            total_users = 0
            active_users = 0
            try:
                if self.subscriptions_db.exists():
                    conn = sqlite3.connect(self.subscriptions_db)
                    c = conn.cursor()
                    c.execute('SELECT COUNT(*) FROM users')
                    total_users = c.fetchone()[0] or 0
                    c.execute("SELECT COUNT(*) FROM users WHERE status = 'active'")
                    active_users = c.fetchone()[0] or 0
                    conn.close()
            except Exception:
                pass
            self.send_message(token, chat_id, f'✅ Admin OK\nTotal users: {total_users}\nActive users: {active_users}')
            return
        if cmd == '/admin_extend':
            if not self._is_admin_user(telegram_user_id):
                self.send_message(token, chat_id, '⛔ هذا الأمر للأدمن فقط.')
                return
            if len(args) < 2:
                self.send_message(token, chat_id, 'الاستخدام: /admin_extend <user_id> <days>')
                return
            if not self.subscription_manager:
                self.send_message(token, chat_id, '⚠️ نظام الاشتراكات غير متاح.')
                return
            try:
                target_user_id = int(args[0])
                days = int(args[1])
                ok, message = self.subscription_manager.extend_subscription(target_user_id, days)
                self.send_message(token, chat_id, ('✅ ' if ok else '⚠️ ') + str(message))
            except Exception as e:
                self.send_message(token, chat_id, f'⚠️ خطأ: {e}')
            return
        if cmd.startswith('/admin_'):
            self.send_message(token, chat_id, '⚠️ الأمر الإداري غير مدعوم حالياً في البوت.')

    def _process_update(self, token, update):
        msg = update.get('message') or {}
        if not isinstance(msg, dict):
            return
        text = str(msg.get('text') or '').strip()
        if not text.startswith('/'):
            return
        sender = msg.get('from') or {}
        chat = msg.get('chat') or {}
        telegram_user_id = sender.get('id')
        username = str(sender.get('username') or '').strip()
        chat_id = chat.get('id')
        if telegram_user_id is None or chat_id is None:
            return
        self._handle_command(token, chat_id, int(telegram_user_id), username, text)

    def _loop(self):
        offset = self._load_offset()
        while self._running:
            try:
                token = self._get_bot_token()
                if not token:
                    self.state['last_error'] = 'missing_bot_token'
                    time.sleep(self.poll_interval)
                    continue
                params = {'timeout': 20, 'allowed_updates': json.dumps(['message'])}
                if isinstance(offset, int):
                    params['offset'] = offset
                resp = self._api_get(token, 'getUpdates', params=params)
                data = resp.json() if resp.status_code == 200 else {}
                self.state['last_poll_at'] = datetime.now().isoformat()
                if not data.get('ok'):
                    self.state['last_error'] = str(data.get('description') or f'http_{resp.status_code}')
                    time.sleep(self.poll_interval)
                    continue
                self.state['last_error'] = None
                updates = data.get('result') or []
                if updates:
                    for upd in updates:
                        self._process_update(token, upd)
                        update_id = upd.get('update_id')
                        if isinstance(update_id, int):
                            offset = update_id + 1
                            self.state['last_update_id'] = update_id
                            self.state['updates_processed'] += 1
                    if isinstance(offset, int):
                        self._save_offset(offset)
                time.sleep(self.poll_interval)
            except Exception as e:
                self.state['last_error'] = str(e)
                time.sleep(self.poll_interval)
        self.state['running'] = False

    def start(self):
        with self._lock:
            if self._running:
                return False, 'already running'
            self._running = True
            self.state['running'] = True
            self.state['started_at'] = datetime.now().isoformat()
            self._thread = threading.Thread(target=self._loop, daemon=True, name='telegram-command-bot')
            self._thread.start()
            return True, 'started'

    def stop(self):
        with self._lock:
            if not self._running:
                return False, 'already stopped'
            self._running = False
            return True, 'stopping'

    def get_status(self):
        s = dict(self.state)
        s['running'] = bool(self._running)
        return s
