# نظام التحسين التلقائي
# Auto-Optimization System

import json
import sqlite3
from datetime import datetime, timedelta
import numpy as np

class PerformanceOptimizer:
    """نظام تحسين تلقائي بناءً على الأداء"""
    
    def __init__(self, db_path='performance_data.db'):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """إنشاء قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                direction TEXT,
                entry REAL,
                stop_loss REAL,
                tp1 REAL,
                tp2 REAL,
                tp3 REAL,
                quality_score INTEGER,
                confidence REAL,
                timeframe TEXT,
                result TEXT,
                profit_pips REAL,
                timestamp DATETIME
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS optimization_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parameter TEXT,
                old_value REAL,
                new_value REAL,
                reason TEXT,
                timestamp DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def record_signal(self, signal, result, profit_pips):
        """تسجيل إشارة ونتيجتها"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO signals (
                symbol, direction, entry, stop_loss, tp1, tp2, tp3,
                quality_score, confidence, timeframe, result, profit_pips, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            signal['symbol'],
            signal['direction'],
            signal['entry'],
            signal['stop_loss'],
            signal['tp1'],
            signal['tp2'],
            signal['tp3'],
            signal['quality_score'],
            signal['confidence'],
            'multi',
            result,
            profit_pips,
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
    def analyze_performance(self, days=7):
        """تحليل الأداء لفترة معينة"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        c.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
                AVG(profit_pips) as avg_pips,
                symbol,
                direction,
                timeframe
            FROM signals
            WHERE timestamp >= ?
            GROUP BY symbol, direction, timeframe
        ''', (start_date,))
        
        results = c.fetchall()
        conn.close()
        
        analysis = {}
        for row in results:
            total, wins, avg_pips, symbol, direction, tf = row
            win_rate = (wins / total * 100) if total > 0 else 0
            
            key = f"{symbol}_{direction}_{tf}"
            analysis[key] = {
                'total_signals': total,
                'win_rate': win_rate,
                'avg_pips': avg_pips or 0,
                'symbol': symbol,
                'direction': direction,
                'timeframe': tf
            }
        
        return analysis
    
    def optimize_parameters(self):
        """تحسين المعاملات بناءً على الأداء"""
        analysis = self.analyze_performance(days=7)
        
        recommendations = []
        
        for key, data in analysis.items():
            # إذا كان معدل النجاح منخفض جداً
            if data['win_rate'] < 50 and data['total_signals'] >= 5:
                recommendations.append({
                    'action': 'increase_threshold',
                    'symbol': data['symbol'],
                    'current_threshold': 75,
                    'recommended_threshold': 80,
                    'reason': f"معدل النجاح منخفض ({data['win_rate']:.1f}%)"
                })
            
            # إذا كان الأداء ممتاز
            elif data['win_rate'] > 75 and data['total_signals'] >= 5:
                recommendations.append({
                    'action': 'maintain',
                    'symbol': data['symbol'],
                    'reason': f"أداء ممتاز ({data['win_rate']:.1f}%)"
                })
        
        return recommendations
    
    def generate_optimization_report(self):
        """إنشاء تقرير التحسين"""
        analysis = self.analyze_performance(days=7)
        recommendations = self.optimize_parameters()
        
        report = """
╔══════════════════════════════════════════════════════════╗
║           📊 تقرير التحسين التلقائي                      ║
╚══════════════════════════════════════════════════════════╝

🔍 تحليل الأداء (آخر 7 أيام):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        if analysis:
            for key, data in sorted(analysis.items(), key=lambda x: x[1]['win_rate'], reverse=True):
                report += f"\n{data['symbol']} ({data['direction']} - {data['timeframe']}):\n"
                report += f"  • إجمالي الإشارات: {data['total_signals']}\n"
                report += f"  • معدل النجاح: {data['win_rate']:.1f}%\n"
                report += f"  • متوسط الأرباح: {data['avg_pips']:.2f} نقطة\n"
        else:
            report += "\n⚠️ لا توجد بيانات كافية بعد\n"
        
        report += "\n\n💡 التوصيات:\n"
        report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        if recommendations:
            for rec in recommendations:
                report += f"\n• {rec['symbol']}: {rec['reason']}\n"
                if rec['action'] == 'increase_threshold':
                    report += f"  → رفع الحد الأدنى للجودة من {rec['current_threshold']} إلى {rec['recommended_threshold']}\n"
                elif rec['action'] == 'maintain':
                    report += f"  → الاستمرار على الإعدادات الحالية ✅\n"
        else:
            report += "\n✅ جميع الإعدادات مثالية حالياً\n"
        
        report += "\n" + "="*60 + "\n"
        
        return report


if __name__ == "__main__":
    optimizer = PerformanceOptimizer()
    print(optimizer.generate_optimization_report())
