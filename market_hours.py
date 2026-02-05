# -*- coding: utf-8 -*-
"""
نظام إدارة أوقات الأسواق
يحدد متى يكون كل سوق مفتوح أو مغلق
"""

from datetime import datetime, time, timedelta
import pytz

class MarketHours:
    """إدارة أوقات فتح وإغلاق الأسواق"""
    
    def __init__(self):
        self.utc = pytz.UTC
        self.ny_tz = pytz.timezone('America/New_York')
        self.london_tz = pytz.timezone('Europe/London')
        self.tokyo_tz = pytz.timezone('Asia/Tokyo')
    
    def is_forex_open(self):
        """
        فحص إذا كان سوق الفوركس مفتوح
        الفوركس: الأحد 22:00 GMT - الجمعة 22:00 GMT
        """
        now_utc = datetime.now(self.utc)
        weekday = now_utc.weekday()  # 0=Monday, 6=Sunday
        hour = now_utc.hour
        
        # السبت: مغلق
        if weekday == 5:
            return False
        
        # الجمعة: مفتوح حتى 22:00 GMT
        if weekday == 4 and hour >= 22:
            return False
        
        # الأحد: مفتوح بعد 22:00 GMT
        if weekday == 6 and hour < 22:
            return False
        
        return True
    
    def is_us_stock_market_open(self):
        """
        فحص سوق الأسهم الأمريكية
        الإثنين-الجمعة: 09:30-16:00 EST
        """
        now_ny = datetime.now(self.ny_tz)
        weekday = now_ny.weekday()
        
        # نهاية الأسبوع: مغلق
        if weekday >= 5:
            return False
        
        # ساعات التداول: 9:30 صباحاً - 4:00 مساءً
        market_open = time(9, 30)
        market_close = time(16, 0)
        current_time = now_ny.time()
        
        return market_open <= current_time <= market_close
    
    def is_crypto_market_open(self):
        """
        سوق العملات الرقمية: مفتوح 24/7
        """
        return True
    
    def is_commodity_market_open(self, commodity='GOLD'):
        """
        فحص أسواق السلع (ذهب، نفط، فضة)
        تقريباً نفس أوقات الفوركس مع اختلافات طفيفة
        """
        # الذهب والفضة: تقريباً 24/5 مثل الفوركس
        if commodity in ['GOLD', 'SILVER', 'XAUUSD', 'XAGUSD']:
            return self.is_forex_open()
        
        # النفط: الأحد-الجمعة مع أوقات محددة
        if commodity in ['CRUDE', 'BRENT', 'OIL']:
            now_utc = datetime.now(self.utc)
            weekday = now_utc.weekday()
            
            # السبت: مغلق
            if weekday == 5:
                return False
            
            # الجمعة: يغلق مبكراً
            if weekday == 4 and now_utc.hour >= 20:
                return False
            
            return True
        
        return self.is_forex_open()
    
    def get_market_status(self, symbol):
        """
        الحصول على حالة السوق لرمز معين
        Returns: dict مع حالة السوق والوقت المتبقي
        """
        symbol = symbol.upper()
        
        # العملات الرقمية
        if symbol in ['BTCUSD', 'ETHUSD', 'XRPUSD', 'ADAUSD', 'SOLUSD', 'DOGEUSD']:
            return {
                'is_open': True,
                'market_type': 'crypto',
                'next_event': 'مفتوح 24/7',
                'can_trade': True
            }
        
        # المؤشرات الأمريكية
        if symbol in ['SPX', 'DJI', 'NDX', 'RUT']:
            is_open = self.is_us_stock_market_open()
            return {
                'is_open': is_open,
                'market_type': 'us_stocks',
                'next_event': self._get_next_us_market_event(),
                'can_trade': is_open
            }
        
        # السلع
        if symbol in ['XAUUSD', 'XAGUSD', 'CRUDE', 'BRENT', 'NATGAS']:
            commodity = 'GOLD' if 'XAU' in symbol else 'SILVER' if 'XAG' in symbol else 'OIL'
            is_open = self.is_commodity_market_open(commodity)
            return {
                'is_open': is_open,
                'market_type': 'commodity',
                'next_event': self._get_next_forex_event(),
                'can_trade': is_open
            }
        
        # أزواج الفوركس
        is_open = self.is_forex_open()
        return {
            'is_open': is_open,
            'market_type': 'forex',
            'next_event': self._get_next_forex_event(),
            'can_trade': is_open
        }
    
    def _get_next_forex_event(self):
        """حساب الحدث التالي للفوركس"""
        now_utc = datetime.now(self.utc)
        weekday = now_utc.weekday()
        
        if self.is_forex_open():
            # السوق مفتوح، حساب وقت الإغلاق
            if weekday == 4:  # الجمعة
                close_time = now_utc.replace(hour=22, minute=0, second=0, microsecond=0)
                if now_utc < close_time:
                    delta = close_time - now_utc
                    hours = delta.seconds // 3600
                    return f"يغلق خلال {hours} ساعة"
            return "مفتوح حتى الجمعة 22:00 GMT"
        else:
            # السوق مغلق، حساب وقت الافتتاح
            if weekday == 5:  # السبت
                return "يفتح الأحد 22:00 GMT"
            elif weekday == 6:  # الأحد
                open_time = now_utc.replace(hour=22, minute=0, second=0, microsecond=0)
                if now_utc < open_time:
                    delta = open_time - now_utc
                    hours = delta.seconds // 3600
                    return f"يفتح خلال {hours} ساعة"
            return "يفتح قريباً"
    
    def _get_next_us_market_event(self):
        """حساب الحدث التالي لسوق الأسهم الأمريكية"""
        now_ny = datetime.now(self.ny_tz)
        weekday = now_ny.weekday()
        
        if self.is_us_stock_market_open():
            close_time = now_ny.replace(hour=16, minute=0, second=0, microsecond=0)
            delta = close_time - now_ny
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            return f"يغلق خلال {hours}س {minutes}د"
        else:
            if weekday >= 5:  # نهاية الأسبوع
                return "يفتح الإثنين 09:30 EST"
            else:
                return "يفتح الساعة 09:30 EST"
    
    def should_suspend_trade(self, symbol, trade_timestamp):
        """
        تحديد إذا كان يجب تعليق الصفقة
        Args:
            symbol: رمز الأصل
            trade_timestamp: وقت فتح الصفقة
        Returns:
            bool, str: (يجب التعليق, السبب)
        """
        status = self.get_market_status(symbol)
        
        # العملات الرقمية: لا تعليق
        if status['market_type'] == 'crypto':
            return False, "سوق مفتوح 24/7"
        
        # السوق مغلق
        if not status['is_open']:
            return True, f"السوق مغلق - {status['next_event']}"
        
        # الصفقات القديمة (أكثر من 5 أيام)
        try:
            if isinstance(trade_timestamp, str):
                trade_time = datetime.fromisoformat(trade_timestamp.replace('Z', '+00:00'))
            else:
                trade_time = trade_timestamp
            
            now = datetime.now(self.utc)
            age = now - trade_time.replace(tzinfo=self.utc)
            
            if age.days >= 5:
                return True, f"صفقة قديمة ({age.days} يوم)"
        except:
            pass
        
        return False, "صفقة نشطة"
    
    def get_weekly_reset_time(self):
        """
        الحصول على وقت إعادة تعيين الأسبوع
        Returns: datetime التالي لافتتاح الأسبوع
        """
        now_utc = datetime.now(self.utc)
        
        # إيجاد الأحد القادم الساعة 22:00 GMT
        days_until_sunday = (6 - now_utc.weekday()) % 7
        if days_until_sunday == 0 and now_utc.hour >= 22:
            days_until_sunday = 7
        
        next_sunday = now_utc + timedelta(days=days_until_sunday)
        reset_time = next_sunday.replace(hour=22, minute=0, second=0, microsecond=0)
        
        return reset_time


# مثال للاستخدام
if __name__ == "__main__":
    import os
    os.system('chcp 65001 > nul')
    
    mh = MarketHours()
    
    print("🕐 فحص أوقات الأسواق")
    print("="*60)
    
    symbols = ['EURUSD', 'BTCUSD', 'XAUUSD', 'SPX', 'CRUDE']
    
    for symbol in symbols:
        status = mh.get_market_status(symbol)
        icon = "✅" if status['is_open'] else "❌"
        print(f"\n{icon} {symbol}")
        print(f"   النوع: {status['market_type']}")
        print(f"   الحالة: {'مفتوح' if status['is_open'] else 'مغلق'}")
        print(f"   التالي: {status['next_event']}")
