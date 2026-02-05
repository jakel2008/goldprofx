"""
نظام متابعة ومراقبة الصفقات المفتوحة
يقوم بإرسال تحديثات دورية حول حالة الصفقات
"""

import json
import os
from datetime import datetime
from auto_pairs_analyzer import (
    load_active_trades, 
    update_trades, 
    send_broadcast_message,
    fetch_pair_data_5m,
    build_trade_report
)

ACTIVE_TRADES_FILE = "active_trades.json"

def get_trades_status_report():
    """الحصول على تقرير شامل عن حالة الصفقات"""
    trades = load_active_trades()
    
    if not trades:
        return "📊 لا توجد صفقات نشطة حالياً"
    
    active_trades = {k: v for k, v in trades.items() if v.get('status') == 'active'}
    closed_trades = {k: v for k, v in trades.items() if v.get('status') == 'closed'}
    
    report = f"""
📊 تقرير الصفقات الشامل
الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*50}
📈 الصفقات النشطة: {len(active_trades)}

"""
    
    if active_trades:
        for trade_id, trade in active_trades.items():
            try:
                # جلب السعر الحالي
                df = fetch_pair_data_5m(trade['symbol'], period='1d')
                if df is not None and not df.empty:
                    current_price = float(df['close'].iloc[-1])
                    entry = trade['entry']
                    symbol = trade['symbol']
                    direction = trade['direction']
                    
                    # حساب المسافة من التاريخ المفتوحة
                    if direction == 'buy':
                        distance_to_tp = ((trade['take_profit'] - current_price) / entry) * 100
                        distance_to_sl = ((current_price - trade['stop_loss']) / entry) * 100
                    else:  # sell
                        distance_to_tp = ((current_price - trade['take_profit']) / entry) * 100
                        distance_to_sl = ((trade['stop_loss'] - current_price) / entry) * 100
                    
                    # تحديد حالة الصفقة
                    if distance_to_tp >= 100:
                        status_icon = "🎯"
                        status_text = "قريبة من الهدف"
                    elif distance_to_sl >= 100:
                        status_icon = "⚠️"
                        status_text = "قريبة من الخسارة"
                    else:
                        status_icon = "📍"
                        status_text = "مستمرة"
                    
                    report += f"""
{status_icon} {symbol} ({direction.upper()})
   السعر الحالي: {current_price:.5f}
   سعر الدخول: {entry:.5f}
   الهدف: {trade['take_profit']:.5f}
   الخسارة: {trade['stop_loss']:.5f}
   الحالة: {status_text}
   الحدث من الهدف: {distance_to_tp:.1f}%
   الحدث من الخسارة: {distance_to_sl:.1f}%
   وقت الفتح: {datetime.fromisoformat(trade['open_time']).strftime('%H:%M')}

"""
            except Exception as e:
                report += f"❌ خطأ في معالجة {trade['symbol']}: {e}\n"
    
    # إضافة الصفقات المغلقة
    if closed_trades:
        report += f"""
{'='*50}
✅ الصفقات المغلقة: {len(closed_trades)}

"""
        for trade_id, trade in list(closed_trades.items())[-5:]:  # آخر 5 صفقات
            result = "رابحة ✅" if trade.get('result') == 'win' else "خاسرة ❌"
            pips = trade.get('pips', 0)
            report += f"{trade['symbol']} ({trade['direction']}) - {result} ({pips:+.1f} نقطة)\n"
    
    return report


def monitor_and_report():
    """مراقبة الصفقات وإرسال التقارير"""
    print(f"\n{'='*60}")
    print(f"🔍 جاري مراقبة الصفقات - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # التحقق من الصفقات وإغلاق أي منها وصل للهدف
    print("📊 جاري التحقق من الصفقات النشطة...")
    closed_count = update_trades()
    
    if closed_count > 0:
        print(f"✅ تم إغلاق {closed_count} صفقة")
        send_broadcast_message(f"✅ تحديث: تم إغلاق {closed_count} صفقة", parse_mode=None)
    
    # الحصول على تقرير الحالة
    report = get_trades_status_report()
    print(report)
    
    # إرسال التقرير على Telegram
    send_broadcast_message(report, parse_mode=None)
    
    print(f"{'='*60}")
    print("✅ انتهت المراقبة بنجاح")
    print(f"{'='*60}\n")


def send_hourly_closed_report():
    """إرسال تقرير الصفقات المنتهية كل ساعة"""
    try:
        data = build_trade_report(hours=1)
        report = f"""
تقرير الساعة الأخيرة
الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

الصفقات النشطة: {data.get('active_count', 0)}
الصفقات المنتهية (آخر ساعة): {data.get('recent_closed_count', 0)}
الرابحة: {data.get('wins', 0)}
الخاسرة: {data.get('losses', 0)}
نسبة النجاح: {data.get('win_rate', 0)}%
"""

        recent = data.get('recent_closed', [])
        if recent:
            report += "\nآخر الصفقات المنتهية:\n"
            for t in recent[:5]:
                symbol = t.get('symbol', '-')
                result = 'رابحة' if t.get('result') == 'win' else 'خاسرة'
                pips = t.get('pips', 0)
                report += f"- {symbol}: {result} ({pips:+.1f})\n"

        send_broadcast_message(report, parse_mode=None)
        return True
    except Exception as e:
        print(f"خطأ في تقرير الساعة: {e}")
        return False


def get_quick_summary():
    """ملخص سريع عن الصفقات"""
    trades = load_active_trades()
    
    if not trades:
        return "📊 لا توجد صفقات"
    
    active = len([t for t in trades.values() if t.get('status') == 'active'])
    closed = len([t for t in trades.values() if t.get('status') == 'closed'])
    
    # حساب الأرباح والخسائر
    wins = len([t for t in trades.values() if t.get('result') == 'win'])
    losses = len([t for t in trades.values() if t.get('result') == 'loss'])
    total_pips = sum([t.get('pips', 0) for t in trades.values() if t.get('pips')])
    
    # حساب نسبة النجاح
    win_rate = (wins/(wins+losses)*100) if (wins+losses) > 0 else 0
    
    summary = f"""
📈 ملخص الصفقات الكلي

النشطة: {active}
المغلقة: {closed}

الرابحة: {wins} ✅
الخاسرة: {losses} ❌

إجمالي النقاط: {total_pips:+.1f}
نسبة النجاح: {win_rate:.1f}%

الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    return summary


if __name__ == "__main__":
    # تشغيل المراقبة
    monitor_and_report()
    
    # إرسال ملخص سريع
    quick_summary = get_quick_summary()
    print(quick_summary)
    send_broadcast_message(quick_summary, parse_mode=None)
