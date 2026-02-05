"""
محرك إحصائيات الصفقات المتقدم
Advanced Trade Statistics Engine
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

class TradeStatistics:
    def __init__(self, db_path="trades_database.db"):
        self.db_path = Path(__file__).parent / db_path
        self.init_database()
    
    def init_database(self):
        """إنشاء قاعدة بيانات الصفقات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                stop_loss REAL,
                take_profit_1 REAL,
                take_profit_2 REAL,
                take_profit_3 REAL,
                entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                exit_time TIMESTAMP,
                status TEXT DEFAULT 'open',
                profit_loss REAL DEFAULT 0,
                profit_percentage REAL DEFAULT 0,
                volume REAL DEFAULT 1.0,
                strategy TEXT,
                timeframe TEXT,
                risk_reward_ratio REAL,
                notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE NOT NULL,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                break_even_trades INTEGER DEFAULT 0,
                total_profit REAL DEFAULT 0,
                total_loss REAL DEFAULT 0,
                net_profit REAL DEFAULT 0,
                win_rate REAL DEFAULT 0,
                avg_win REAL DEFAULT 0,
                avg_loss REAL DEFAULT 0,
                profit_factor REAL DEFAULT 0,
                best_trade REAL DEFAULT 0,
                worst_trade REAL DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_trade(self, trade_data: Dict) -> int:
        """إضافة صفقة جديدة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trades (
                symbol, direction, entry_price, stop_loss, 
                take_profit_1, take_profit_2, take_profit_3,
                volume, strategy, timeframe, risk_reward_ratio, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_data.get('symbol'),
            trade_data.get('direction'),
            trade_data.get('entry_price'),
            trade_data.get('stop_loss'),
            trade_data.get('take_profit_1'),
            trade_data.get('take_profit_2'),
            trade_data.get('take_profit_3'),
            trade_data.get('volume', 1.0),
            trade_data.get('strategy', 'ICT'),
            trade_data.get('timeframe', '1H'),
            trade_data.get('risk_reward_ratio', 0),
            trade_data.get('notes', '')
        ))
        
        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return trade_id
    
    def close_trade(self, trade_id: int, exit_price: float, notes: str = "") -> Dict:
        """إغلاق صفقة وحساب الربح/الخسارة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جلب بيانات الصفقة
        cursor.execute('SELECT * FROM trades WHERE id = ?', (trade_id,))
        trade = cursor.fetchone()
        
        if not trade:
            conn.close()
            return {'success': False, 'error': 'Trade not found'}
        
        entry_price = trade[3]
        direction = trade[2]
        volume = trade[14]
        
        # حساب الربح/الخسارة
        if direction.lower() == 'buy':
            profit_loss = (exit_price - entry_price) * volume
            profit_percentage = ((exit_price - entry_price) / entry_price) * 100
        else:  # sell
            profit_loss = (entry_price - exit_price) * volume
            profit_percentage = ((entry_price - exit_price) / entry_price) * 100
        
        # تحديد الحالة
        if profit_loss > 0:
            status = 'win'
        elif profit_loss < 0:
            status = 'loss'
        else:
            status = 'break_even'
        
        # تحديث الصفقة
        cursor.execute('''
            UPDATE trades 
            SET exit_price = ?, exit_time = ?, status = ?, 
                profit_loss = ?, profit_percentage = ?, notes = ?
            WHERE id = ?
        ''', (exit_price, datetime.now(), status, profit_loss, profit_percentage, notes, trade_id))
        
        conn.commit()
        conn.close()
        
        # تحديث الملخص اليومي
        self.update_daily_summary()
        
        return {
            'success': True,
            'trade_id': trade_id,
            'profit_loss': profit_loss,
            'profit_percentage': profit_percentage,
            'status': status
        }
    
    def get_statistics(self, days: int = 30) -> Dict:
        """الحصول على الإحصائيات الشاملة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # التاريخ البدائي
        start_date = datetime.now() - timedelta(days=days)
        
        # إجمالي الصفقات
        cursor.execute('''
            SELECT COUNT(*), status, SUM(profit_loss), AVG(profit_percentage)
            FROM trades 
            WHERE exit_time >= ? AND status != 'open'
            GROUP BY status
        ''', (start_date,))
        
        results = cursor.fetchall()
        
        stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'break_even_trades': 0,
            'total_profit': 0,
            'total_loss': 0,
            'net_profit': 0,
            'win_rate': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'profit_factor': 0,
            'avg_win_percentage': 0,
            'avg_loss_percentage': 0
        }
        
        for row in results:
            count, status, total_pl, avg_pct = row
            stats['total_trades'] += count
            
            if status == 'win':
                stats['winning_trades'] = count
                stats['total_profit'] = total_pl or 0
                stats['avg_win_percentage'] = avg_pct or 0
            elif status == 'loss':
                stats['losing_trades'] = count
                stats['total_loss'] = abs(total_pl or 0)
                stats['avg_loss_percentage'] = abs(avg_pct or 0)
            elif status == 'break_even':
                stats['break_even_trades'] = count
        
        # حساب المؤشرات
        if stats['total_trades'] > 0:
            stats['win_rate'] = (stats['winning_trades'] / stats['total_trades']) * 100
            stats['net_profit'] = stats['total_profit'] - stats['total_loss']
        
        if stats['winning_trades'] > 0:
            stats['avg_win'] = stats['total_profit'] / stats['winning_trades']
        
        if stats['losing_trades'] > 0:
            stats['avg_loss'] = stats['total_loss'] / stats['losing_trades']
        
        if stats['total_loss'] > 0:
            stats['profit_factor'] = stats['total_profit'] / stats['total_loss']
        
        # أفضل وأسوأ صفقة
        cursor.execute('''
            SELECT MAX(profit_loss), MIN(profit_loss)
            FROM trades 
            WHERE exit_time >= ? AND status != 'open'
        ''', (start_date,))
        
        best, worst = cursor.fetchone()
        stats['best_trade'] = best or 0
        stats['worst_trade'] = worst or 0
        
        # إحصائيات حسب العملة
        cursor.execute('''
            SELECT symbol, 
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'win' THEN 1 ELSE 0 END) as wins,
                   SUM(profit_loss) as net_profit
            FROM trades 
            WHERE exit_time >= ? AND status != 'open'
            GROUP BY symbol
            ORDER BY net_profit DESC
        ''', (start_date,))
        
        stats['by_symbol'] = []
        for row in cursor.fetchall():
            symbol, total, wins, net = row
            win_rate = (wins / total * 100) if total > 0 else 0
            stats['by_symbol'].append({
                'symbol': symbol,
                'total_trades': total,
                'winning_trades': wins,
                'win_rate': win_rate,
                'net_profit': net or 0
            })
        
        # إحصائيات حسب الاستراتيجية
        cursor.execute('''
            SELECT strategy, 
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'win' THEN 1 ELSE 0 END) as wins,
                   SUM(profit_loss) as net_profit
            FROM trades 
            WHERE exit_time >= ? AND status != 'open'
            GROUP BY strategy
            ORDER BY net_profit DESC
        ''', (start_date,))
        
        stats['by_strategy'] = []
        for row in cursor.fetchall():
            strategy, total, wins, net = row
            win_rate = (wins / total * 100) if total > 0 else 0
            stats['by_strategy'].append({
                'strategy': strategy,
                'total_trades': total,
                'winning_trades': wins,
                'win_rate': win_rate,
                'net_profit': net or 0
            })
        
        conn.close()
        return stats
    
    def get_open_trades(self) -> List[Dict]:
        """الحصول على الصفقات المفتوحة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, symbol, direction, entry_price, stop_loss,
                   take_profit_1, take_profit_2, take_profit_3,
                   entry_time, volume, strategy, timeframe
            FROM trades 
            WHERE status = 'open'
            ORDER BY entry_time DESC
        ''')
        
        trades = []
        for row in cursor.fetchall():
            trades.append({
                'id': row[0],
                'symbol': row[1],
                'direction': row[2],
                'entry_price': row[3],
                'stop_loss': row[4],
                'take_profit_1': row[5],
                'take_profit_2': row[6],
                'take_profit_3': row[7],
                'entry_time': row[8],
                'volume': row[9],
                'strategy': row[10],
                'timeframe': row[11]
            })
        
        conn.close()
        return trades
    
    def update_daily_summary(self):
        """تحديث الملخص اليومي"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        # حساب إحصائيات اليوم
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'win' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN status = 'loss' THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN status = 'break_even' THEN 1 ELSE 0 END) as break_even,
                SUM(CASE WHEN status = 'win' THEN profit_loss ELSE 0 END) as total_profit,
                SUM(CASE WHEN status = 'loss' THEN ABS(profit_loss) ELSE 0 END) as total_loss,
                MAX(CASE WHEN status = 'win' THEN profit_loss ELSE 0 END) as best_trade,
                MIN(CASE WHEN status = 'loss' THEN profit_loss ELSE 0 END) as worst_trade
            FROM trades 
            WHERE DATE(exit_time) = ? AND status != 'open'
        ''', (today,))
        
        row = cursor.fetchone()
        total, wins, losses, break_even, total_profit, total_loss, best, worst = row
        
        if total and total > 0:
            win_rate = (wins / total) * 100 if wins else 0
            net_profit = (total_profit or 0) - (total_loss or 0)
            avg_win = (total_profit / wins) if wins > 0 else 0
            avg_loss = (total_loss / losses) if losses > 0 else 0
            profit_factor = (total_profit / total_loss) if total_loss > 0 else 0
            
            cursor.execute('''
                INSERT OR REPLACE INTO daily_summary (
                    date, total_trades, winning_trades, losing_trades, break_even_trades,
                    total_profit, total_loss, net_profit, win_rate,
                    avg_win, avg_loss, profit_factor, best_trade, worst_trade
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (today, total, wins or 0, losses or 0, break_even or 0,
                  total_profit or 0, total_loss or 0, net_profit,
                  win_rate, avg_win, avg_loss, profit_factor, best or 0, worst or 0))
            
            conn.commit()
        
        conn.close()
    
    def get_daily_summaries(self, days: int = 30) -> List[Dict]:
        """الحصول على الملخصات اليومية"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = datetime.now().date() - timedelta(days=days)
        
        cursor.execute('''
            SELECT * FROM daily_summary 
            WHERE date >= ?
            ORDER BY date DESC
        ''', (start_date,))
        
        summaries = []
        for row in cursor.fetchall():
            summaries.append({
                'date': row[1],
                'total_trades': row[2],
                'winning_trades': row[3],
                'losing_trades': row[4],
                'break_even_trades': row[5],
                'total_profit': row[6],
                'total_loss': row[7],
                'net_profit': row[8],
                'win_rate': row[9],
                'avg_win': row[10],
                'avg_loss': row[11],
                'profit_factor': row[12],
                'best_trade': row[13],
                'worst_trade': row[14]
            })
        
        conn.close()
        return summaries

    def export_to_json(self, filename: str = None):
        """تصدير البيانات إلى JSON"""
        if not filename:
            filename = f"trades_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            'export_date': datetime.now().isoformat(),
            'statistics_30_days': self.get_statistics(30),
            'open_trades': self.get_open_trades(),
            'daily_summaries': self.get_daily_summaries(30)
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filename

# مثيل عام
trade_stats = TradeStatistics()
