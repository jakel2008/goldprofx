import json
import importlib
import os
import sqlite3
import shutil
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from html import escape

import requests

try:
    from vip_subscription_system import SubscriptionManager  # type: ignore
except Exception:
    SubscriptionManager = None  # type: ignore


class TelegramCommandBot:
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir or Path(__file__).parent)

        default_data_dir = Path('/var/data') if Path('/var/data').exists() else self.base_dir
        self.data_dir = Path(os.environ.get('GOLDPRO_DATA_DIR', str(default_data_dir)))
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        self.bots_config_file = Path(os.environ.get('BOTS_CONFIG_FILE', str(self.data_dir / 'bots_config.json')))
        self.state_file = Path(os.environ.get('TELEGRAM_COMMAND_STATE_FILE', str(self.data_dir / 'telegram_command_bot_state.json')))
        self.users_db = Path(os.environ.get('USERS_DB_PATH', str(self.data_dir / 'users.db')))
        self.subscriptions_db = Path(os.environ.get('VIP_SUBSCRIPTIONS_DB_PATH', str(self.data_dir / 'vip_subscriptions.db')))

        self._migrate_legacy_file(self.bots_config_file)
        self._migrate_legacy_file(self.state_file)
        self.poll_interval = max(1, int(os.environ.get('TELEGRAM_COMMAND_POLL_INTERVAL', '2')))
        self.request_timeout = max(10, int(os.environ.get('TELEGRAM_COMMAND_TIMEOUT', '30')))
        self.admin_ids = {x.strip() for x in str(os.environ.get('TELEGRAM_ADMIN_IDS', '')).split(',') if x.strip()}
        self.admin_usernames = {x.strip().lstrip('@').lower() for x in str(os.environ.get('TELEGRAM_ADMIN_USERNAMES', '')).split(',') if x.strip()}
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self.state = {
            'running': False,
            'last_poll_at': None,
            'last_update_id': None,
            'last_error': None,
            'token_source': None,
            'updates_processed': 0,
            'commands_processed': 0,
            'started_at': None
        }
        self.subscription_manager = SubscriptionManager() if SubscriptionManager else None
        self._prepared_token = None

    def _migrate_legacy_file(self, target_path):
        try:
            target = Path(str(target_path))
            legacy = self.base_dir / target.name
            if target.exists() or (not legacy.exists()):
                return
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(legacy), str(target))
        except Exception:
            pass

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
            self.state['token_source'] = 'env:MM_TELEGRAM_BOT_TOKEN'
            return env_token
        cfg = self._load_bots_config()
        bots = cfg.get('bots', []) if isinstance(cfg, dict) else []
        active = [b for b in bots if isinstance(b, dict) and str(b.get('status', '')).lower() == 'active']
        if active:
            default_bot = next((b for b in active if b.get('is_default')), None)
            selected = default_bot or active[0]
            token = str(selected.get('token') or '').strip()
            if token:
                self.state['token_source'] = 'bots_config'
                return token
        try:
            sender_mod = importlib.import_module('telegram_sender')
            token_loader = getattr(sender_mod, '_get_active_bot_tokens', None)
            if callable(token_loader):
                tokens = token_loader() or []
                token = str(tokens[0] if tokens else '').strip()
                if token:
                    self.state['token_source'] = 'telegram_sender._get_active_bot_tokens'
                    return token
            sender_token = str(getattr(sender_mod, 'BOT_TOKEN', '') or '').strip()
            if sender_token:
                self.state['token_source'] = 'telegram_sender.BOT_TOKEN'
                return sender_token
        except Exception:
            pass
        self.state['token_source'] = None
        return ''

    def _ensure_polling_ready(self, token):
        try:
            if not token:
                return False, 'missing_bot_token'
            if self._prepared_token == token:
                return True, 'already_prepared'
            info_resp = self._api_get(token, 'getWebhookInfo')
            info_data = info_resp.json() if info_resp.status_code == 200 else {}
            if not info_data.get('ok'):
                return False, str(info_data.get('description') or f'webhook_info_http_{info_resp.status_code}')
            webhook_url = str((info_data.get('result') or {}).get('url') or '').strip()
            if webhook_url:
                delete_resp = self._api_post(token, 'deleteWebhook', {'drop_pending_updates': False})
                delete_data = delete_resp.json() if delete_resp.status_code == 200 else {}
                if not delete_data.get('ok'):
                    return False, str(delete_data.get('description') or f'delete_webhook_http_{delete_resp.status_code}')
            self._prepared_token = token
            return True, 'polling_ready'
        except Exception as e:
            return False, str(e)

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

    def _is_admin_user(self, telegram_user_id, username=''):
        if str(telegram_user_id) in self.admin_ids:
            return True
        if str(username or '').strip().lstrip('@').lower() in self.admin_usernames:
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

    def _admin_commands_text(self):
        return (
            '🛠️ <b>أوامر الأدمن</b>\n'
            '/admin\n'
            '/admin_test\n'
            '/admin_stats\n'
            '/admin_users\n'
            '/admin_user &lt;user_id|username&gt;\n'
            '/admin_upgrade &lt;user_id&gt; &lt;plan&gt; [days]\n'
            '/admin_extend &lt;user_id&gt; &lt;days&gt;\n'
            '/admin_cancel &lt;user_id&gt;\n'
            '/admin_reactivate &lt;user_id&gt;\n'
            '/admin_broadcast &lt;message&gt;'
        )

    def _normalize_lookup(self, value):
        return str(value or '').strip()

    def _lookup_subscription_user(self, value):
        try:
            if not self.subscriptions_db.exists():
                return None
            lookup = self._normalize_lookup(value)
            if not lookup:
                return None
            conn = sqlite3.connect(self.subscriptions_db)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            if lookup.isdigit():
                c.execute(
                    '''
                    SELECT user_id, username, first_name, plan, status, subscription_end, email, chat_id, telegram_id
                    FROM users
                    WHERE user_id = ? AND (deleted_at IS NULL OR deleted_at = '')
                    LIMIT 1
                    ''',
                    (int(lookup),)
                )
            else:
                c.execute(
                    '''
                    SELECT user_id, username, first_name, plan, status, subscription_end, email, chat_id, telegram_id
                    FROM users
                    WHERE lower(username) = lower(?) AND (deleted_at IS NULL OR deleted_at = '')
                    LIMIT 1
                    ''',
                    (lookup,)
                )
            row = c.fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception:
            return None

    def _admin_user_text(self, value):
        row = self._lookup_subscription_user(value)
        if not row:
            return '⚠️ المستخدم غير موجود في قاعدة الاشتراكات.'
        return (
            '👤 <b>تفاصيل المستخدم</b>\n'
            f"ID: {row.get('user_id')}\n"
            f"Username: {escape(str(row.get('username') or '-'))}\n"
            f"Name: {escape(str(row.get('first_name') or '-'))}\n"
            f"Plan: {escape(str(row.get('plan') or '-'))}\n"
            f"Status: {escape(str(row.get('status') or '-'))}\n"
            f"Ends: {escape(str(row.get('subscription_end') or 'غير محدد'))}\n"
            f"Email: {escape(str(row.get('email') or '-'))}\n"
            f"Chat ID: {escape(str(row.get('chat_id') or '-'))}\n"
            f"Telegram ID: {escape(str(row.get('telegram_id') or '-'))}"
        )

    def _broadcast_to_active_users(self, token, message):
        sent = 0
        failed = 0
        try:
            if not self.subscriptions_db.exists():
                return {'sent': 0, 'failed': 0, 'total': 0, 'error': 'subscriptions_db_missing'}
            conn = sqlite3.connect(self.subscriptions_db)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(
                '''
                SELECT user_id, username, chat_id, telegram_id
                FROM users
                WHERE status IN ('active', 'trial')
                  AND (deleted_at IS NULL OR deleted_at = '')
                ORDER BY user_id ASC
                '''
            )
            rows = [dict(r) for r in c.fetchall()]
            conn.close()
            total = len(rows)
            for row in rows:
                target_chat_id = row.get('chat_id') or row.get('telegram_id') or row.get('user_id')
                if not target_chat_id:
                    failed += 1
                    continue
                if self.send_message(token, target_chat_id, message):
                    sent += 1
                else:
                    failed += 1
            return {'sent': sent, 'failed': failed, 'total': total}
        except Exception as e:
            return {'sent': sent, 'failed': failed, 'total': sent + failed, 'error': str(e)}

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

    def _general_help_text(self, is_admin=False):
        lines = [
            '📘 <b>أوامر البوت</b>',
            '/start',
            '/help',
            '/plans',
            '/myplan',
            '/upgrade',
            '/referral',
            '/analyze <symbol>',
            '/analyze_eurusd',
            '/analyze_gbpusd',
        ]
        if is_admin:
            lines.extend(['', self._admin_commands_text()])
        return '\n'.join(lines)

    def _referral_text(self, telegram_user_id, username, chat_id):
        try:
            info = self._get_user_plan_info(telegram_user_id, username, chat_id)
            target_user_id = None
            if info and info.get('user_id'):
                target_user_id = int(info.get('user_id'))
            elif telegram_user_id:
                target_user_id = int(telegram_user_id)
            if not self.subscription_manager or not target_user_id:
                return '⚠️ لا يمكن تحميل بيانات الإحالة حالياً.'
            sub = self.subscription_manager.check_subscription(target_user_id)
            if not sub.get('exists'):
                return '⚠️ لا يوجد حساب اشتراك مرتبط بك بعد. استخدم /start أولاً.'
            referral_code = sub.get('referral_code') or '-'
            return (
                '🎁 <b>كود الإحالة الخاص بك</b>\n'
                f'Code: {escape(str(referral_code))}\n'
                'أرسل هذا الكود لأي مشترك جديد عند التسجيل.'
            )
        except Exception as e:
            return f'⚠️ تعذر تحميل كود الإحالة: {escape(str(e))}'

    def _resolve_analysis_symbol(self, cmd, args):
        if cmd.startswith('/analyze_'):
            return cmd.split('/analyze_', 1)[1].strip().upper().replace('/', '')
        if args:
            return str(args[0]).strip().upper().replace('/', '')
        return ''

    def _format_analysis_text(self, symbol, result):
        if not isinstance(result, dict) or not result.get('success'):
            return f'⚠️ تعذر تحليل {escape(symbol)} حالياً.'
        recommendation = str(result.get('recommendation') or result.get('signal') or 'N/A')
        entry = result.get('entry_point')
        stop_loss = result.get('stop_loss')
        tp1 = result.get('take_profit1')
        tp2 = result.get('take_profit2')
        tp3 = result.get('take_profit3')
        confidence = result.get('confidence') or result.get('confidence_score') or result.get('score')
        lines = [
            f'📈 <b>تحليل {escape(symbol)}</b>',
            f'Recommendation: {escape(recommendation)}',
        ]
        if confidence not in (None, ''):
            lines.append(f'Confidence: {escape(str(confidence))}')
        if entry not in (None, ''):
            lines.append(f'Entry: {escape(str(entry))}')
        if stop_loss not in (None, ''):
            lines.append(f'SL: {escape(str(stop_loss))}')
        if tp1 not in (None, ''):
            lines.append(f'TP1: {escape(str(tp1))}')
        if tp2 not in (None, ''):
            lines.append(f'TP2: {escape(str(tp2))}')
        if tp3 not in (None, ''):
            lines.append(f'TP3: {escape(str(tp3))}')
        return '\n'.join(lines)

    def _analyze_symbol_text(self, symbol):
        normalized_symbol = str(symbol or '').strip().upper().replace('/', '')
        if not normalized_symbol:
            return 'الاستخدام: /analyze <symbol>\nمثال: /analyze EURUSD أو /analyze_xauusd'
        try:
            app_mod = sys.modules.get('web_app_complete')
            if app_mod is None:
                app_mod = importlib.import_module('web_app_complete')
            normalizer = getattr(app_mod, '_normalize_symbol_for_engine', None)
            if callable(normalizer):
                engine_symbol = normalizer(normalized_symbol)
            else:
                engine_symbol = normalized_symbol
            try:
                from advanced_analyzer_engine import perform_full_analysis  # type: ignore
            except ImportError:
                analyzer_path = self.base_dir / 'advanced_analyzer_engine.py'
                spec = importlib.util.spec_from_file_location('advanced_analyzer_engine', str(analyzer_path))
                analyzer_module = importlib.util.module_from_spec(spec)
                sys.modules['advanced_analyzer_engine'] = analyzer_module
                spec.loader.exec_module(analyzer_module)
                perform_full_analysis = analyzer_module.perform_full_analysis
            result = perform_full_analysis(engine_symbol, '1h', force_live=True)
            return self._format_analysis_text(normalized_symbol, result)
        except Exception as e:
            return f'⚠️ تعذر تنفيذ التحليل لـ {escape(normalized_symbol)}: {escape(str(e))}'

    def _admin_stats_text(self):
        total_users = 0
        active_users = 0
        trial_users = 0
        inactive_users = 0
        expired_users = 0
        try:
            if self.subscriptions_db.exists():
                conn = sqlite3.connect(self.subscriptions_db)
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM users WHERE deleted_at IS NULL OR deleted_at = ''")
                total_users = c.fetchone()[0] or 0
                c.execute("SELECT COUNT(*) FROM users WHERE status = 'active' AND (deleted_at IS NULL OR deleted_at = '')")
                active_users = c.fetchone()[0] or 0
                c.execute("SELECT COUNT(*) FROM users WHERE status = 'trial' AND (deleted_at IS NULL OR deleted_at = '')")
                trial_users = c.fetchone()[0] or 0
                c.execute("SELECT COUNT(*) FROM users WHERE status = 'inactive' AND (deleted_at IS NULL OR deleted_at = '')")
                inactive_users = c.fetchone()[0] or 0
                c.execute("SELECT COUNT(*) FROM users WHERE status = 'expired' AND (deleted_at IS NULL OR deleted_at = '')")
                expired_users = c.fetchone()[0] or 0
                conn.close()
        except Exception:
            pass
        return (
            '📊 <b>إحصائيات المشتركين</b>\n'
            f'Total users: {total_users}\n'
            f'Active: {active_users}\n'
            f'Trial: {trial_users}\n'
            f'Inactive: {inactive_users}\n'
            f'Expired: {expired_users}\n'
            f'Admins by ID: {", ".join(sorted(self.admin_ids)) or "-"}\n'
            f'Admins by username: {", ".join(sorted(self.admin_usernames)) or "-"}'
        )

    def _admin_users_text(self, limit=15):
        try:
            if not self.subscriptions_db.exists():
                return '⚠️ قاعدة الاشتراكات غير متاحة.'
            conn = sqlite3.connect(self.subscriptions_db)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(
                '''
                SELECT user_id, username, plan, status
                FROM users
                WHERE (deleted_at IS NULL OR deleted_at = '')
                ORDER BY user_id DESC
                LIMIT ?
                ''',
                (int(limit),)
            )
            rows = [dict(r) for r in c.fetchall()]
            conn.close()
            if not rows:
                return '⚠️ لا يوجد مستخدمون في قاعدة الاشتراكات.'
            lines = ['👥 <b>آخر المستخدمين</b>']
            for row in rows:
                lines.append(
                    f"{row.get('user_id')} | {escape(str(row.get('username') or '-'))} | {escape(str(row.get('plan') or '-'))} | {escape(str(row.get('status') or '-'))}"
                )
            return '\n'.join(lines)
        except Exception as e:
            return f'⚠️ تعذر تحميل المستخدمين: {escape(str(e))}'

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
                'الأوامر: /plans /myplan\n'
                f"تم حفظ المستخدم: {'نعم' if saved_user else 'لا'}\\n"
                f'تم ربط الحسابات: {linked}'
            )
            if self._is_admin_user(telegram_user_id, username):
                msg += '\n\n' + self._admin_commands_text()
            self.send_message(token, chat_id, msg)
            return
        if cmd == '/help':
            self.send_message(token, chat_id, self._general_help_text(self._is_admin_user(telegram_user_id, username)))
            return
        if cmd == '/plans':
            self.send_message(token, chat_id, self._plans_text())
            return
        if cmd == '/upgrade':
            self.send_message(token, chat_id, '⬆️ <b>خطط الترقية</b>\n' + self._plans_text())
            return
        if cmd == '/referral':
            self.send_message(token, chat_id, self._referral_text(telegram_user_id, username, chat_id))
            return
        if cmd == '/analyze' or cmd.startswith('/analyze_'):
            symbol = self._resolve_analysis_symbol(cmd, args)
            self.send_message(token, chat_id, self._analyze_symbol_text(symbol))
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
        if cmd == '/admin':
            if not self._is_admin_user(telegram_user_id, username):
                self.send_message(token, chat_id, '⛔ هذا الأمر للأدمن فقط.')
                return
            self.send_message(token, chat_id, self._admin_commands_text())
            return
        if cmd in ('/admin_test', '/admin_stats'):
            if not self._is_admin_user(telegram_user_id, username):
                self.send_message(token, chat_id, '⛔ هذا الأمر للأدمن فقط.')
                return
            self.send_message(token, chat_id, self._admin_stats_text())
            return
        if cmd == '/admin_user':
            if not self._is_admin_user(telegram_user_id, username):
                self.send_message(token, chat_id, '⛔ هذا الأمر للأدمن فقط.')
                return
            if len(args) < 1:
                self.send_message(token, chat_id, 'الاستخدام: /admin_user <user_id|username>')
                return
            self.send_message(token, chat_id, self._admin_user_text(args[0]))
            return
        if cmd == '/admin_users':
            if not self._is_admin_user(telegram_user_id, username):
                self.send_message(token, chat_id, '⛔ هذا الأمر للأدمن فقط.')
                return
            self.send_message(token, chat_id, self._admin_users_text())
            return
        if cmd == '/admin_upgrade':
            if not self._is_admin_user(telegram_user_id, username):
                self.send_message(token, chat_id, '⛔ هذا الأمر للأدمن فقط.')
                return
            if len(args) < 2:
                self.send_message(token, chat_id, 'الاستخدام: /admin_upgrade <user_id> <plan> [days]')
                return
            if not self.subscription_manager:
                self.send_message(token, chat_id, '⚠️ نظام الاشتراكات غير متاح.')
                return
            try:
                target_user_id = int(args[0])
                plan = str(args[1]).strip().lower()
                duration_days = int(args[2]) if len(args) > 2 else None
                ok, message = self.subscription_manager.update_subscription_plan(target_user_id, plan, duration_days)
                self.send_message(token, chat_id, ('✅ ' if ok else '⚠️ ') + str(message))
            except Exception as e:
                self.send_message(token, chat_id, f'⚠️ خطأ: {e}')
            return
        if cmd == '/admin_extend':
            if not self._is_admin_user(telegram_user_id, username):
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
        if cmd == '/admin_cancel':
            if not self._is_admin_user(telegram_user_id, username):
                self.send_message(token, chat_id, '⛔ هذا الأمر للأدمن فقط.')
                return
            if len(args) < 1:
                self.send_message(token, chat_id, 'الاستخدام: /admin_cancel <user_id>')
                return
            if not self.subscription_manager:
                self.send_message(token, chat_id, '⚠️ نظام الاشتراكات غير متاح.')
                return
            try:
                ok, message = self.subscription_manager.cancel_subscription(int(args[0]))
                self.send_message(token, chat_id, ('✅ ' if ok else '⚠️ ') + str(message))
            except Exception as e:
                self.send_message(token, chat_id, f'⚠️ خطأ: {e}')
            return
        if cmd == '/admin_reactivate':
            if not self._is_admin_user(telegram_user_id, username):
                self.send_message(token, chat_id, '⛔ هذا الأمر للأدمن فقط.')
                return
            if len(args) < 1:
                self.send_message(token, chat_id, 'الاستخدام: /admin_reactivate <user_id>')
                return
            if not self.subscription_manager:
                self.send_message(token, chat_id, '⚠️ نظام الاشتراكات غير متاح.')
                return
            try:
                ok, message = self.subscription_manager.reactivate_subscription(int(args[0]))
                self.send_message(token, chat_id, ('✅ ' if ok else '⚠️ ') + str(message))
            except Exception as e:
                self.send_message(token, chat_id, f'⚠️ خطأ: {e}')
            return
        if cmd == '/admin_broadcast':
            if not self._is_admin_user(telegram_user_id, username):
                self.send_message(token, chat_id, '⛔ هذا الأمر للأدمن فقط.')
                return
            message = text.partition(' ')[2].strip()
            if not message:
                self.send_message(token, chat_id, 'الاستخدام: /admin_broadcast <message>')
                return
            result = self._broadcast_to_active_users(token, message)
            self.send_message(
                token,
                chat_id,
                f"📣 تم تنفيذ البث\nSent: {result.get('sent', 0)}\nFailed: {result.get('failed', 0)}\nTotal: {result.get('total', 0)}" + (f"\nError: {result.get('error')}" if result.get('error') else '')
            )
            return
        if cmd.startswith('/admin_'):
            self.send_message(token, chat_id, '⚠️ الأمر الإداري غير معروف.\n\n' + self._admin_commands_text())

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
                ready, ready_msg = self._ensure_polling_ready(token)
                if not ready:
                    self.state['last_error'] = ready_msg
                    time.sleep(self.poll_interval)
                    continue
                params = {'timeout': 20, 'allowed_updates': json.dumps(['message'])}
                if isinstance(offset, int):
                    params['offset'] = offset
                resp = self._api_get(token, 'getUpdates', params=params)
                data = resp.json() if resp.status_code == 200 else {}
                self.state['last_poll_at'] = datetime.now().isoformat()
                if not data.get('ok'):
                    description = str(data.get('description') or f'http_{resp.status_code}')
                    self.state['last_error'] = description
                    if 'webhook' in description.lower() or 'terminated by other getupdates' in description.lower():
                        self._prepared_token = None
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
                self._prepared_token = None
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
