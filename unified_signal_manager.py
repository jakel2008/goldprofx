# -*- coding: utf-8 -*-
"""
نظام المزامنة المركزي
يوحد البيانات بين الويب والبوت ويرسل التوصيات لكليهما معاً
"""

import os
import json
import sqlite3
from datetime import datetime
import requests

class UnifiedSignalManager:
    """مدير الإشارات الموحد للويب والبوت"""
    
    def __init__(self):
        self.signals_dir = "signals"
        self.recommendations_dir = "recommendations"
        self.web_db = "vip_signals.db"
        self.vip_db = "vip_subscriptions.db"
        
        # إعدادات التليجرام
        self.bot_token = os.environ.get("MM_TELEGRAM_BOT_TOKEN", "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A")
        
        # إنشاء المجلدات
        for dir_path in [self.signals_dir, self.recommendations_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        
        # إنشاء قاعدة بيانات الويب إذا لم تكن موجودة
        self._init_web_database()
    
    def _init_web_database(self):
        """إنشاء قاعدة بيانات الويب وجداولها"""
        conn = sqlite3.connect(self.web_db)
        c = conn.cursor()
        
        # جدول الإشارات
        c.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT UNIQUE,
                symbol TEXT NOT NULL,
                signal_type TEXT,
                entry_price REAL,
                stop_loss REAL,
                take_profit_1 REAL,
                take_profit_2 REAL,
                take_profit_3 REAL,
                quality_score INTEGER,
                recommendation TEXT,
                timeframe TEXT,
                timestamp TEXT,
                status TEXT DEFAULT 'active',
                result TEXT DEFAULT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول المستخدمين
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE,
                username TEXT,
                plan TEXT,
                status TEXT,
                synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def publish_signal(self, signal_data):
        """
        نشر إشارة موحدة للويب والبوت معاً
        Args:
            signal_data: dict يحتوي على بيانات الإشارة
        Returns:
            dict: تقرير النشر
        """
        timestamp = datetime.now()
        # استخدام pair أو symbol
        symbol = signal_data.get('pair', signal_data.get('symbol', 'UNKNOWN'))
        signal_id = f"{symbol}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # إضافة معلومات إضافية
        signal_data['signal_id'] = signal_id
        signal_data['pair'] = symbol  # توحيد الاسم
        signal_data['timestamp'] = timestamp.isoformat()
        signal_data['published_at'] = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        report = {
            'signal_id': signal_id,
            'web_saved': False,
            'telegram_sent': 0,
            'telegram_failed': 0,
            'file_saved': False,
            'errors': []
        }
        
        # 1. حفظ في قاعدة بيانات الويب
        try:
            self._save_to_web_db(signal_data)
            report['web_saved'] = True
        except Exception as e:
            report['errors'].append(f"Web DB Error: {str(e)}")
        
        # 2. حفظ كملف JSON
        try:
            self._save_signal_file(signal_data, signal_id)
            report['file_saved'] = True
        except Exception as e:
            report['errors'].append(f"File Save Error: {str(e)}")
        
        # 3. إرسال للمشتركين عبر التليجرام
        telegram_report = self._send_to_telegram(signal_data)
        report['telegram_sent'] = telegram_report['sent']
        report['telegram_failed'] = telegram_report['failed']
        
        return report
    
    def _save_to_web_db(self, signal_data):
        """حفظ الإشارة في قاعدة بيانات الويب"""
        conn = sqlite3.connect(self.web_db)
        c = conn.cursor()
        
        # إنشاء جدول الإشارات إذا لم يكن موجوداً
        c.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT UNIQUE,
                symbol TEXT NOT NULL,
                signal_type TEXT,
                entry_price REAL,
                stop_loss REAL,
                take_profit_1 REAL,
                take_profit_2 REAL,
                take_profit_3 REAL,
                quality_score INTEGER,
                recommendation TEXT,
                timeframe TEXT,
                timestamp TEXT,
                status TEXT DEFAULT 'active',
                result TEXT DEFAULT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # إدراج الإشارة
        symbol = signal_data.get('pair', signal_data.get('symbol', 'UNKNOWN'))
        new_signal_type = signal_data.get('signal') or signal_data.get('rec') or signal_data.get('recommendation', 'N/A')
        
        # فحص وإغلاق الصفقات المعاكسة النشطة التي وصلت TP1 أو أكثر
        try:
            c.execute('''
                SELECT signal_id, signal_type, tp1_locked, tp2_locked, tp3_locked, result
                FROM signals 
                WHERE symbol=? AND status='active' AND result='win'
            ''', (symbol,))
            
            existing_signals = c.fetchall()
            for existing in existing_signals:
                existing_type = existing[1]
                # فحص إذا كانت الصفقة معاكسة
                if (new_signal_type.lower() == 'buy' and existing_type.lower() == 'sell') or \
                   (new_signal_type.lower() == 'sell' and existing_type.lower() == 'buy'):
                    # إغلاق الصفقة المعاكسة
                    c.execute('''
                        UPDATE signals 
                        SET status='closed' 
                        WHERE signal_id=?
                    ''', (existing[0],))
                    print(f"✅ تم إغلاق الصفقة المعاكسة {existing[0]} ({existing_type}) لإفساح المجال للصفقة الجديدة ({new_signal_type})")
        except Exception as e:
            print(f"⚠️ خطأ في فحص الصفقات المعاكسة: {e}")
        
        c.execute('''
            INSERT OR REPLACE INTO signals 
            (signal_id, symbol, signal_type, entry_price, stop_loss, 
             take_profit_1, take_profit_2, take_profit_3, quality_score, 
             recommendation, timeframe, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            signal_data['signal_id'],
            symbol,
            new_signal_type,
            signal_data.get('entry') or signal_data.get('entry_price'),
            signal_data.get('sl') or signal_data.get('stop_loss'),
            signal_data.get('tp1') or (signal_data.get('take_profit', [None])[0] if isinstance(signal_data.get('take_profit'), list) else signal_data.get('take_profit')),
            signal_data.get('tp2') or (signal_data.get('take_profit', [None, None])[1] if isinstance(signal_data.get('take_profit'), list) and len(signal_data.get('take_profit', [])) > 1 else None),
            signal_data.get('tp3') or (signal_data.get('take_profit', [None, None, None])[2] if isinstance(signal_data.get('take_profit'), list) and len(signal_data.get('take_profit', [])) > 2 else None),
            signal_data.get('quality_score', 0),
            signal_data.get('recommendation', ''),
            signal_data.get('tf') or signal_data.get('timeframe', '5m'),
            signal_data['timestamp']
        ))
        
        conn.commit()
        conn.close()
    
    def _save_signal_file(self, signal_data, signal_id):
        """حفظ الإشارة كملف JSON"""
        filename = f"{signal_id}.json"
        filepath = os.path.join(self.signals_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(signal_data, f, indent=2, ensure_ascii=False)
    
    def _send_to_telegram(self, signal_data):
        """إرسال الإشارة لجميع المشتركين النشطين"""
        report = {'sent': 0, 'failed': 0}
        
        # جلب المشتركين النشطين
        users = self._get_active_subscribers()
        
        # تنسيق الرسالة
        message = self._format_telegram_message(signal_data)
        
        for user in users:
            try:
                self._send_telegram_message(user['user_id'], message)
                report['sent'] += 1
            except Exception as e:
                report['failed'] += 1
                print(f"فشل الإرسال لـ {user['user_id']}: {e}")
        
        return report
    
    def _get_active_subscribers(self):
        """جلب المشتركين النشطين من قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.vip_db)
            c = conn.cursor()
            
            c.execute('''
                SELECT user_id, plan, username 
                FROM users 
                WHERE status = 'active'
            ''')
            
            users = []
            for row in c.fetchall():
                users.append({
                    'user_id': row[0],
                    'plan': row[1],
                    'username': row[2]
                })
            
            conn.close()
            return users
        except:
            return []
    
    def _format_telegram_message(self, signal_data):
        """تنسيق رسالة التليجرام"""
        symbol = signal_data.get('pair', signal_data.get('symbol', 'UNKNOWN'))
        signal_type = signal_data.get('signal') or signal_data.get('rec') or signal_data.get('recommendation', 'N/A')
        entry = signal_data.get('entry') or signal_data.get('entry_price', 'N/A')
        sl = signal_data.get('sl') or signal_data.get('stop_loss', 'N/A')
        
        # التعامل مع TP كقائمة أو قيم منفصلة
        if 'take_profit' in signal_data and isinstance(signal_data['take_profit'], list):
            tp_list = signal_data['take_profit']
            tp1 = tp_list[0] if len(tp_list) > 0 else 'N/A'
            tp2 = tp_list[1] if len(tp_list) > 1 else 'N/A'
            tp3 = tp_list[2] if len(tp_list) > 2 else 'N/A'
        else:
            tp1 = signal_data.get('tp1', 'N/A')
            tp2 = signal_data.get('tp2', 'N/A')
            tp3 = signal_data.get('tp3', 'N/A')
        
        quality = signal_data.get('quality_score', 0)
        timeframe = signal_data.get('tf') or signal_data.get('timeframe', '5m')
        
        # تحديد الأيقونة حسب نوع الإشارة
        if 'buy' in str(signal_type).lower() or 'شراء' in str(signal_type):
            icon = "🟢"
        elif 'sell' in str(signal_type).lower() or 'بيع' in str(signal_type):
            icon = "🔴"
        else:
            icon = "⚪"
        
        message = f"""
{icon} **توصية جديدة - {symbol}**
{'═'*35}

📊 **النوع:** {signal_type}
⏱️ **الإطار الزمني:** {timeframe}
⭐ **الجودة:** {quality}/100

💰 **الدخول:** {entry}
🛑 **وقف الخسارة:** {sl}

🎯 **الأهداف:**
   TP1: {tp1}
   TP2: {tp2}
   TP3: {tp3}

🕐 **الوقت:** {signal_data['published_at']}

{'═'*35}
✅ GOLD PRO VIP Signals
        """
        
        return message.strip()
    
    def _send_telegram_message(self, chat_id, text):
        """إرسال رسالة تليجرام"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def sync_databases(self):
        """
        مزامنة قواعد البيانات - نقل البيانات من VIP إلى Web
        """
        print("🔄 بدء المزامنة...")
        
        # مزامنة المستخدمين
        users_synced = self._sync_users()
        
        # مزامنة الإشارات من الملفات إلى قاعدة البيانات
        signals_synced = self._sync_signals_to_db()
        
        print(f"✅ تمت المزامنة:")
        print(f"   • المستخدمين: {users_synced}")
        print(f"   • الإشارات: {signals_synced}")
        
        return {
            'users_synced': users_synced,
            'signals_synced': signals_synced
        }
    
    def _sync_users(self):
        """مزامنة بيانات المستخدمين بين القاعدتين"""
        try:
            # قراءة من VIP DB
            vip_conn = sqlite3.connect(self.vip_db)
            vip_c = vip_conn.cursor()
            
            vip_c.execute('SELECT user_id, username, plan, status FROM users')
            users = vip_c.fetchall()
            vip_conn.close()
            
            # كتابة إلى Web DB
            web_conn = sqlite3.connect(self.web_db)
            web_c = web_conn.cursor()
            
            # إنشاء جدول المستخدمين إذا لم يكن موجوداً
            web_c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE,
                    username TEXT,
                    plan TEXT,
                    status TEXT,
                    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            count = 0
            for user in users:
                web_c.execute('''
                    INSERT OR REPLACE INTO users (user_id, username, plan, status, synced_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                ''', user)
                count += 1
            
            web_conn.commit()
            web_conn.close()
            
            return count
        except Exception as e:
            print(f"خطأ في مزامنة المستخدمين: {e}")
            return 0
    
    def _sync_signals_to_db(self):
        """مزامنة ملفات الإشارات إلى قاعدة البيانات"""
        if not os.path.exists(self.signals_dir):
            return 0
        
        count = 0
        for filename in os.listdir(self.signals_dir):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(self.signals_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    signal_data = json.load(f)
                
                # إضافة signal_id إذا لم يكن موجوداً
                if 'signal_id' not in signal_data:
                    signal_data['signal_id'] = filename.replace('.json', '')
                
                if 'timestamp' not in signal_data:
                    signal_data['timestamp'] = datetime.now().isoformat()
                
                self._save_to_web_db(signal_data)
                count += 1
            except Exception as e:
                print(f"خطأ في معالجة {filename}: {e}")
        
        return count
    
    def get_unified_statistics(self):
        """الحصول على إحصائيات موحدة من جميع المصادر"""
        stats = {
            'total_signals': 0,
            'successful_signals': 0,
            'failed_signals': 0,
            'active_signals': 0,
            'success_rate': 0.0,
            'total_users': 0,
            'active_users': 0,
            'signals_today': 0,
            'users_by_plan': {},
            'recent_signals': []
        }
        
        # إحصائيات الإشارات
        try:
            conn = sqlite3.connect(self.web_db)
            c = conn.cursor()
            
            # إجمالي الإشارات
            c.execute('SELECT COUNT(*) FROM signals')
            stats['total_signals'] = c.fetchone()[0]
            
            # الإشارات الناجحة (حققت أي هدف)
            c.execute("SELECT COUNT(*) FROM signals WHERE result IN ('tp1', 'tp2', 'tp3', 'success')")
            stats['successful_signals'] = c.fetchone()[0]
            
            # الإشارات الفاشلة (ضربت الستوب)
            c.execute("SELECT COUNT(*) FROM signals WHERE result IN ('sl', 'failed')")
            stats['failed_signals'] = c.fetchone()[0]
            
            # الإشارات النشطة
            c.execute("SELECT COUNT(*) FROM signals WHERE status = 'active'")
            stats['active_signals'] = c.fetchone()[0]
            
            # حساب معدل النجاح
            if stats['total_signals'] > 0:
                total_closed = stats['successful_signals'] + stats['failed_signals']
                if total_closed > 0:
                    stats['success_rate'] = (stats['successful_signals'] / total_closed) * 100
            
            # إشارات اليوم
            c.execute('''
                SELECT COUNT(*) FROM signals 
                WHERE DATE(created_at) = DATE('now')
            ''')
            stats['signals_today'] = c.fetchone()[0]
            
            # آخر 5 إشارات
            c.execute('''
                SELECT signal_id, symbol, signal_type, quality_score, timestamp
                FROM signals
                ORDER BY created_at DESC
                LIMIT 5
            ''')
            
            for row in c.fetchall():
                stats['recent_signals'].append({
                    'id': row[0],
                    'symbol': row[1],
                    'type': row[2],
                    'quality': row[3],
                    'time': row[4]
                })
            
            conn.close()
        except Exception as e:
            print(f"⚠️ خطأ في إحصائيات الإشارات: {e}")
            pass
        
        # إحصائيات المستخدمين
        try:
            conn = sqlite3.connect(self.vip_db)
            c = conn.cursor()
            
            # إجمالي المستخدمين
            c.execute('SELECT COUNT(*) FROM users')
            stats['total_users'] = c.fetchone()[0]
            
            # المستخدمين النشطين
            c.execute("SELECT COUNT(*) FROM users WHERE status = 'active'")
            stats['active_users'] = c.fetchone()[0]
            
            # توزيع حسب الخطة
            c.execute('SELECT plan, COUNT(*) FROM users GROUP BY plan')
            for row in c.fetchall():
                stats['users_by_plan'][row[0]] = row[1]
            
            conn.close()
        except:
            pass
        
        return stats


if __name__ == "__main__":
    import os
    os.system('chcp 65001 > nul')
    
    manager = UnifiedSignalManager()
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           🔄 نظام المزامنة الموحد                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # مزامنة القواعد
    manager.sync_databases()
    
    print("\n📊 الإحصائيات الموحدة:")
    stats = manager.get_unified_statistics()
    
    print(f"   • إجمالي الإشارات: {stats['total_signals']}")
    print(f"   • إشارات اليوم: {stats['signals_today']}")
    print(f"   • إجمالي المستخدمين: {stats['total_users']}")
    print(f"   • المستخدمين النشطين: {stats['active_users']}")
    
    if stats['users_by_plan']:
        print(f"\n📈 توزيع المستخدمين:")
        for plan, count in stats['users_by_plan'].items():
            print(f"   • {plan}: {count}")
