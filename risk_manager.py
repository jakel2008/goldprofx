# -*- coding: utf-8 -*-
"""
نظام إدارة المخاطر المتقدم
Advanced Risk Management System
"""

class RiskManager:
    """إدارة مخاطر احترافية"""
    
    def __init__(self, account_balance=10000, risk_percent=2.0):
        """
        account_balance: رصيد الحساب
        risk_percent: نسبة المخاطرة لكل صفقة (% من الرصيد)
        """
        self.account_balance = account_balance
        self.risk_percent = risk_percent
        self.max_daily_loss = 6.0  # أقصى خسارة يومية 6%
        self.max_open_trades = 5
        self.max_risk_per_pair = 3.0  # أقصى مخاطرة لزوج واحد
        
    def calculate_position_size(self, entry, stop_loss, pip_value=10):
        """
        حساب حجم الصفقة المناسب
        
        Args:
            entry: نقطة الدخول
            stop_loss: نقطة وقف الخسارة
            pip_value: قيمة النقطة بالدولار (افتراضي 10$ للوت 1.0)
        
        Returns:
            حجم الصفقة باللوت
        """
        risk_amount = (self.account_balance * self.risk_percent) / 100
        risk_pips = abs(entry - stop_loss) * 10000  # تحويل لنقاط
        
        if risk_pips == 0:
            return 0
        
        position_size = risk_amount / (risk_pips * pip_value / 100)
        
        # حد أدنى وأقصى
        position_size = max(0.01, min(position_size, 2.0))
        
        return round(position_size, 2)
    
    def calculate_risk_reward(self, entry, stop_loss, take_profit):
        """حساب نسبة المخاطرة/العائد"""
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)
        
        if risk == 0:
            return 0
        
        return round(reward / risk, 2)
    
    def is_trade_allowed(self, current_daily_loss, open_trades_count):
        """
        فحص إذا كان يمكن فتح صفقة جديدة
        
        Args:
            current_daily_loss: نسبة الخسارة الحالية اليوم
            open_trades_count: عدد الصفقات المفتوحة حالياً
        
        Returns:
            (مسموح, السبب)
        """
        # فحص الخسارة اليومية
        if abs(current_daily_loss) >= self.max_daily_loss:
            return False, f"تم الوصول لأقصى خسارة يومية ({self.max_daily_loss}%)"
        
        # فحص عدد الصفقات المفتوحة
        if open_trades_count >= self.max_open_trades:
            return False, f"تم الوصول لأقصى عدد صفقات مفتوحة ({self.max_open_trades})"
        
        return True, "مسموح بفتح الصفقة"
    
    def calculate_trailing_stop(self, entry, current_price, direction, atr, step=0.5):
        """
        حساب trailing stop loss ذكي
        
        Args:
            entry: نقطة الدخول
            current_price: السعر الحالي
            direction: buy أو sell
            atr: متوسط المدى الحقيقي
            step: خطوة تحريك SL (مضاعف ATR)
        
        Returns:
            مستوى trailing stop الجديد
        """
        if direction == 'buy':
            # للشراء: نحرك SL للأعلى فقط
            profit_pips = (current_price - entry) * 10000
            
            if profit_pips > atr * 10000 * 2:  # ربح 2 ATR
                # نحرك SL للتعادل + خطوة
                trailing_sl = entry + (atr * step)
            elif profit_pips > atr * 10000 * 4:  # ربح 4 ATR
                # نحرك SL لنصف الطريق
                trailing_sl = entry + ((current_price - entry) * 0.5)
            else:
                trailing_sl = entry - (atr * 1.5)  # SL الأصلي
            
            return trailing_sl
        
        else:  # sell
            # للبيع: نحرك SL للأسفل فقط
            profit_pips = (entry - current_price) * 10000
            
            if profit_pips > atr * 10000 * 2:
                trailing_sl = entry - (atr * step)
            elif profit_pips > atr * 10000 * 4:
                trailing_sl = entry - ((entry - current_price) * 0.5)
            else:
                trailing_sl = entry + (atr * 1.5)
            
            return trailing_sl
    
    def calculate_partial_close_levels(self, entry, tp1, tp2, tp3):
        """
        حساب نسب الإغلاق الجزئي
        
        Returns:
            قائمة بمستويات الإغلاق والنسب
        """
        return [
            {'level': tp1, 'close_percent': 30, 'action': 'move_sl_to_breakeven'},
            {'level': tp2, 'close_percent': 40, 'action': 'trail_stop'},
            {'level': tp3, 'close_percent': 30, 'action': 'close_all'}
        ]
    
    def diversification_check(self, current_pairs):
        """
        فحص التنويع في الصفقات
        
        Args:
            current_pairs: قائمة الأزواج المفتوحة حالياً
        
        Returns:
            (مقبول, التحذير)
        """
        # فحص التركيز على زوج واحد
        pair_counts = {}
        for pair in current_pairs:
            base_pair = pair.split('/')[0]  # مثلاً EUR من EUR/USD
            pair_counts[base_pair] = pair_counts.get(base_pair, 0) + 1
        
        # إذا كان هناك أكثر من 3 صفقات على نفس العملة
        for currency, count in pair_counts.items():
            if count >= 3:
                return False, f"تركيز عالي على {currency} ({count} صفقات)"
        
        return True, "تنويع جيد"
    
    def generate_risk_report(self, trades):
        """إنشاء تقرير المخاطر"""
        if not trades:
            return "لا توجد صفقات مفتوحة"
        
        total_risk = sum(t.get('risk_percent', 0) for t in trades)
        pairs = [t.get('symbol', 'unknown') for t in trades]
        
        diversification_ok, div_msg = self.diversification_check(pairs)
        
        report = f"""
╔══════════════════════════════════════════════════════════╗
║                📊 تقرير إدارة المخاطر                    ║
╚══════════════════════════════════════════════════════════╝

🔍 الوضع الحالي:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• رصيد الحساب: ${self.account_balance:,.2f}
• عدد الصفقات المفتوحة: {len(trades)}/{self.max_open_trades}
• إجمالي المخاطرة: {total_risk:.2f}%
• نسبة المخاطرة لكل صفقة: {self.risk_percent}%

📈 التنويع:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{div_msg}

⚠️ الحدود:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• أقصى خسارة يومية: {self.max_daily_loss}%
• أقصى صفقات مفتوحة: {self.max_open_trades}
• أقصى مخاطرة لزوج واحد: {self.max_risk_per_pair}%

💡 التوصيات:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        if total_risk > 8:
            report += "⚠️ المخاطرة الإجمالية مرتفعة! تجنب فتح صفقات جديدة\n"
        elif total_risk > 5:
            report += "✅ المخاطرة متوسطة، كن حذراً عند فتح صفقات جديدة\n"
        else:
            report += "✅ المخاطرة ضمن الحدود الآمنة\n"
        
        if not diversification_ok:
            report += "⚠️ تركيز عالي على عملة واحدة! قم بالتنويع\n"
        
        report += "\n" + "="*60 + "\n"
        
        return report


class SmartTradingPlan:
    """خطة تداول ذكية متكاملة"""
    
    @staticmethod
    def create_full_plan(signal, risk_manager):
        """إنشاء خطة تداول كاملة"""
        
        # حساب حجم الصفقة
        position_size = risk_manager.calculate_position_size(
            signal['entry'],
            signal['stop_loss']
        )
        
        # حساب نسب R:R لكل هدف
        rr1 = risk_manager.calculate_risk_reward(
            signal['entry'], signal['stop_loss'], signal['tp1']
        )
        rr2 = risk_manager.calculate_risk_reward(
            signal['entry'], signal['stop_loss'], signal['tp2']
        )
        rr3 = risk_manager.calculate_risk_reward(
            signal['entry'], signal['stop_loss'], signal['tp3']
        )
        
        # مستويات الإغلاق الجزئي
        partial_levels = risk_manager.calculate_partial_close_levels(
            signal['entry'], signal['tp1'], signal['tp2'], signal['tp3']
        )
        
        # الأرباح المتوقعة
        risk_amount = (risk_manager.account_balance * risk_manager.risk_percent) / 100
        potential_profits = {
            'tp1': risk_amount * rr1 * 0.3,  # 30% عند TP1
            'tp2': risk_amount * rr2 * 0.4,  # 40% عند TP2
            'tp3': risk_amount * rr3 * 0.3,  # 30% عند TP3
        }
        
        total_potential = sum(potential_profits.values())
        
        plan = f"""
{'='*60}
🎯 <b>خطة التداول الذكية المتكاملة</b>
{'='*60}

📊 <b>معلومات الصفقة:</b>
• الزوج: {signal['symbol']}
• الاتجاه: {'شراء 🔼' if signal['direction'] == 'buy' else 'بيع 🔽'}
• جودة الإشارة: {signal['quality_score']}/100
• مستوى الثقة: {signal.get('confidence', 0)*100:.0f}%

💰 <b>إدارة رأس المال:</b>
• حجم الصفقة: {position_size} لوت
• المخاطرة: ${risk_amount:.2f} ({risk_manager.risk_percent}%)
• الربح المتوقع: ${total_potential:.2f}

📍 <b>مستويات التداول:</b>
🟢 الدخول: {signal['entry']:.5f}
🔴 وقف الخسارة: {signal['stop_loss']:.5f}

💚 <b>أهداف الربح (مع الإغلاق الجزئي):</b>
🎯 TP1: {signal['tp1']:.5f} (R:R 1:{rr1})
   → أغلق 30% وحرك SL للتعادل
   → ربح محتمل: ${potential_profits['tp1']:.2f}

🎯 TP2: {signal['tp2']:.5f} (R:R 1:{rr2})
   → أغلق 40% وفعّل Trailing Stop
   → ربح محتمل: ${potential_profits['tp2']:.2f}

🎯 TP3: {signal['tp3']:.5f} (R:R 1:{rr3})
   → أغلق الباقي 30%
   → ربح محتمل: ${potential_profits['tp3']:.2f}

{'─'*60}
💡 <b>استراتيجية الإدارة:</b>

1️⃣ <b>عند الدخول:</b>
   • تأكد من السيولة الكافية
   • ضع SL فوراً
   • لا تغير الخطة عاطفياً

2️⃣ <b>عند وصول TP1:</b>
   • أغلق 30% من الصفقة
   • حرك SL لنقطة الدخول (التعادل)
   • الآن أنت بأمان! ✅

3️⃣ <b>عند وصول TP2:</b>
   • أغلق 40% إضافية
   • حرك SL لمنتصف المسافة
   • فعّل Trailing Stop

4️⃣ <b>عند وصول TP3:</b>
   • أغلق الباقي 30%
   • احتفل بالنجاح! 🎉

{'─'*60}
⚠️ <b>تحذيرات هامة:</b>

❌ لا تحرك SL بعيداً عن الخطة
❌ لا تضيف للصفقة إذا كانت خاسرة
❌ لا تُغلق مبكراً خوفاً
✅ التزم بالخطة = النجاح

{'='*60}
🕐 <b>تم الإنشاء:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return plan


if __name__ == "__main__":
    from datetime import datetime
    
    # مثال على استخدام النظام
    risk_mgr = RiskManager(account_balance=10000, risk_percent=2.0)
    
    # مثال إشارة
    test_signal = {
        'symbol': 'EUR/USD',
        'direction': 'buy',
        'entry': 1.0850,
        'stop_loss': 1.0820,
        'tp1': 1.0900,
        'tp2': 1.0950,
        'tp3': 1.1000,
        'quality_score': 85,
        'confidence': 0.85
    }
    
    # إنشاء خطة كاملة
    plan = SmartTradingPlan.create_full_plan(test_signal, risk_mgr)
    print(plan)
    
    # تقرير المخاطر
    print("\n" + risk_mgr.generate_risk_report([test_signal]))
