# -*- coding: utf-8 -*-
"""
نظام إدارة الصفقات الذكي
يدير الصفقات حسب أوقات الأسواق ويجدد التوصيات
"""

import os
import json
from datetime import datetime, timedelta
from market_hours import MarketHours

class SmartTradeManager:
    """مدير الصفقات الذكي"""
    
    def __init__(self):
        self.active_trades_file = "active_trades.json"
        self.suspended_trades_file = "suspended_trades.json"
        self.signals_dir = "signals"
        self.market_hours = MarketHours()
    
    def load_active_trades(self):
        """تحميل الصفقات النشطة"""
        if os.path.exists(self.active_trades_file):
            try:
                with open(self.active_trades_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_active_trades(self, trades):
        """حفظ الصفقات النشطة"""
        with open(self.active_trades_file, 'w', encoding='utf-8') as f:
            json.dump(trades, f, indent=2, ensure_ascii=False)
    
    def load_suspended_trades(self):
        """تحميل الصفقات المعلقة"""
        if os.path.exists(self.suspended_trades_file):
            try:
                with open(self.suspended_trades_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_suspended_trades(self, trades):
        """حفظ الصفقات المعلقة"""
        with open(self.suspended_trades_file, 'w', encoding='utf-8') as f:
            json.dump(trades, f, indent=2, ensure_ascii=False)
    
    def suspend_closed_market_trades(self):
        """
        تعليق الصفقات للأسواق المغلقة
        Returns: dict مع إحصائيات التعليق
        """
        active_trades = self.load_active_trades()
        suspended = self.load_suspended_trades()
        
        stats = {
            'suspended_count': 0,
            'active_count': 0,
            'crypto_active': 0,
            'details': []
        }
        
        new_active = []
        
        for trade_id in active_trades:
            # استخراج معلومات الصفقة من الاسم
            parts = trade_id.split('_')
            if len(parts) >= 2:
                symbol = parts[0]
                timestamp_str = '_'.join(parts[1:])
                
                # فحص حالة السوق
                should_suspend, reason = self.market_hours.should_suspend_trade(
                    symbol, timestamp_str
                )
                
                if should_suspend:
                    # تعليق الصفقة
                    suspended[trade_id] = {
                        'symbol': symbol,
                        'suspended_at': datetime.now().isoformat(),
                        'reason': reason,
                        'original_timestamp': timestamp_str
                    }
                    stats['suspended_count'] += 1
                    stats['details'].append(f"⏸️  {symbol}: {reason}")
                else:
                    # الإبقاء على الصفقة نشطة
                    new_active.append(trade_id)
                    stats['active_count'] += 1
                    
                    # تتبع العملات الرقمية
                    if symbol in ['BTCUSD', 'ETHUSD', 'XRPUSD', 'ADAUSD', 'SOLUSD', 'DOGEUSD']:
                        stats['crypto_active'] += 1
        
        # حفظ التحديثات
        self.save_active_trades(new_active)
        self.save_suspended_trades(suspended)
        
        return stats
    
    def reactivate_market_open_trades(self):
        """
        إعادة تنشيط الصفقات عند افتتاح الأسواق
        Returns: dict مع إحصائيات إعادة التنشيط
        """
        suspended = self.load_suspended_trades()
        active_trades = self.load_active_trades()
        
        stats = {
            'reactivated_count': 0,
            'still_suspended': 0,
            'deleted_old': 0,
            'details': []
        }
        
        new_suspended = {}
        
        for trade_id, trade_info in suspended.items():
            symbol = trade_info['symbol']
            
            # فحص حالة السوق
            market_status = self.market_hours.get_market_status(symbol)
            
            # حساب عمر الصفقة
            suspended_at = datetime.fromisoformat(trade_info['suspended_at'])
            age_days = (datetime.now() - suspended_at).days
            
            # حذف الصفقات القديمة جداً (أكثر من 7 أيام)
            if age_days > 7:
                stats['deleted_old'] += 1
                stats['details'].append(f"🗑️  {symbol}: حذف صفقة قديمة ({age_days} يوم)")
                continue
            
            # إعادة تنشيط إذا كان السوق مفتوح
            if market_status['is_open']:
                active_trades.append(trade_id)
                stats['reactivated_count'] += 1
                stats['details'].append(f"▶️  {symbol}: إعادة تنشيط - السوق مفتوح")
            else:
                # الإبقاء معلقة
                new_suspended[trade_id] = trade_info
                stats['still_suspended'] += 1
        
        # حفظ التحديثات
        self.save_active_trades(active_trades)
        self.save_suspended_trades(new_suspended)
        
        return stats
    
    def cleanup_old_signals(self, max_age_days=7):
        """
        تنظيف الإشارات القديمة من مجلد signals
        Returns: int عدد الملفات المحذوفة
        """
        if not os.path.exists(self.signals_dir):
            return 0
        
        deleted_count = 0
        now = datetime.now()
        
        for filename in os.listdir(self.signals_dir):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(self.signals_dir, filename)
            
            try:
                # فحص عمر الملف
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                age = now - file_time
                
                if age.days > max_age_days:
                    os.remove(filepath)
                    deleted_count += 1
            except:
                pass
        
        return deleted_count
    
    def weekly_reset(self):
        """
        إعادة تعيين أسبوعية للصفقات
        يُنفذ كل أحد عند افتتاح الأسبوع
        Returns: dict تقرير إعادة التعيين
        """
        print("\n" + "="*70)
        print("🔄 إعادة تعيين أسبوعية - افتتاح الأسبوع")
        print("="*70 + "\n")
        
        # 1. إعادة تنشيط الصفقات المعلقة
        reactivate_stats = self.reactivate_market_open_trades()
        
        print(f"▶️  إعادة التنشيط:")
        print(f"   • تم تنشيط: {reactivate_stats['reactivated_count']}")
        print(f"   • لا تزال معلقة: {reactivate_stats['still_suspended']}")
        print(f"   • تم حذفها (قديمة): {reactivate_stats['deleted_old']}")
        
        # 2. تنظيف الإشارات القديمة
        deleted_signals = self.cleanup_old_signals(max_age_days=7)
        print(f"\n🗑️  تنظيف الإشارات القديمة: {deleted_signals} ملف")
        
        # 3. إحصائيات السوق
        active_count = len(self.load_active_trades())
        suspended_count = len(self.load_suspended_trades())
        
        print(f"\n📊 الإحصائيات:")
        print(f"   • صفقات نشطة: {active_count}")
        print(f"   • صفقات معلقة: {suspended_count}")
        
        print("\n" + "="*70)
        print("✅ اكتملت إعادة التعيين الأسبوعية")
        print("="*70 + "\n")
        
        return {
            'reactivated': reactivate_stats['reactivated_count'],
            'suspended': reactivate_stats['still_suspended'],
            'deleted': reactivate_stats['deleted_old'] + deleted_signals,
            'active_trades': active_count,
            'suspended_trades': suspended_count
        }
    
    def daily_maintenance(self):
        """
        صيانة يومية للصفقات
        يُنفذ كل يوم عند افتتاح السوق
        """
        print("\n" + "="*70)
        print("🔧 الصيانة اليومية")
        print("="*70 + "\n")
        
        # 1. تعليق صفقات الأسواق المغلقة
        suspend_stats = self.suspend_closed_market_trades()
        
        print(f"⏸️  تعليق الصفقات:")
        print(f"   • تم تعليق: {suspend_stats['suspended_count']}")
        print(f"   • نشطة: {suspend_stats['active_count']}")
        print(f"   • عملات رقمية (24/7): {suspend_stats['crypto_active']}")
        
        if suspend_stats['details']:
            print(f"\n📋 التفاصيل:")
            for detail in suspend_stats['details'][:10]:  # أول 10
                print(f"   {detail}")
        
        # 2. إعادة تنشيط ما يمكن
        reactivate_stats = self.reactivate_market_open_trades()
        
        if reactivate_stats['reactivated_count'] > 0:
            print(f"\n▶️  إعادة تنشيط: {reactivate_stats['reactivated_count']} صفقة")
        
        print("\n" + "="*70)
        print("✅ اكتملت الصيانة اليومية")
        print("="*70 + "\n")
        
        return {
            'suspended': suspend_stats['suspended_count'],
            'active': suspend_stats['active_count'],
            'reactivated': reactivate_stats['reactivated_count']
        }
    
    def get_trade_status_report(self):
        """
        الحصول على تقرير شامل لحالة الصفقات
        """
        active = self.load_active_trades()
        suspended = self.load_suspended_trades()
        
        # تصنيف حسب نوع السوق
        by_market = {
            'forex': [],
            'crypto': [],
            'stocks': [],
            'commodities': []
        }
        
        for trade_id in active:
            symbol = trade_id.split('_')[0]
            
            if symbol in ['BTCUSD', 'ETHUSD', 'XRPUSD', 'ADAUSD', 'SOLUSD', 'DOGEUSD']:
                by_market['crypto'].append(symbol)
            elif symbol in ['SPX', 'DJI', 'NDX', 'RUT']:
                by_market['stocks'].append(symbol)
            elif symbol in ['XAUUSD', 'XAGUSD', 'CRUDE', 'BRENT', 'NATGAS']:
                by_market['commodities'].append(symbol)
            else:
                by_market['forex'].append(symbol)
        
        return {
            'total_active': len(active),
            'total_suspended': len(suspended),
            'by_market': by_market,
            'active_ids': active[:10],  # أول 10
            'suspended_info': list(suspended.values())[:10]
        }


if __name__ == "__main__":
    os.system('chcp 65001 > nul')
    
    manager = SmartTradeManager()
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           🧠 نظام إدارة الصفقات الذكي                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # عرض التقرير
    report = manager.get_trade_status_report()
    
    print(f"📊 تقرير الصفقات:")
    print(f"   إجمالي النشطة: {report['total_active']}")
    print(f"   إجمالي المعلقة: {report['total_suspended']}")
    print(f"\n📈 حسب السوق:")
    print(f"   • فوركس: {len(report['by_market']['forex'])}")
    print(f"   • عملات رقمية: {len(report['by_market']['crypto'])}")
    print(f"   • أسهم: {len(report['by_market']['stocks'])}")
    print(f"   • سلع: {len(report['by_market']['commodities'])}")
