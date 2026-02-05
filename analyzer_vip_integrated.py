"""
نسخة محدثة من المحلل التلقائي تستخدم البوت الموحد VIP
"""

import sys
import os

# إضافة المسار للاستيراد
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auto_pairs_analyzer import (
    analyze_pair, 
    generate_pair_report,
    PAIRS_TO_ANALYZE
)
from unified_vip_bot import send_broadcast_signal
from quality_scorer import add_quality_score
from datetime import datetime
import time


def run_analysis_with_vip():
    """
    تشغيل التحليل وإرسال التوصيات للمشتركين VIP فقط
    """
    print(f"\n{'='*60}")
    print(f"🚀 بدء التحليل VIP - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    results = []
    
    for symbol, interval in PAIRS_TO_ANALYZE:
        print(f"\n📈 تحليل {symbol}...")
        
        try:
            # تحليل الزوج
            analysis = analyze_pair(symbol, interval)
            
            if analysis and analysis.get('entry') and analysis.get('stop_loss'):
                # إضافة تقييم الجودة
                analysis_with_quality = add_quality_score(analysis)
                quality_score = analysis_with_quality.get('quality_score', 0)
                quality_level = analysis_with_quality.get('quality_level', 'LOW')
                
                print(f"   ✅ {symbol}: {analysis['recommendation']}")
                print(f"   📊 جودة: {quality_level} ({quality_score}/100)")
                
                # تحضير بيانات التوصية
                signal_data = {
                    'symbol': symbol,
                    'rec': analysis['recommendation'],
                    'entry': analysis['entry'],
                    'sl': analysis['stop_loss'],
                    'tp1': analysis['take_profit'],
                    'tp2': analysis.get('take_profit_2', analysis['take_profit']),
                    'tp3': analysis.get('take_profit_3', analysis['take_profit']),
                    'tf': interval,
                    'rr': analysis.get('risk_reward', 2.0)
                }
                
                # إرسال للمشتركين حسب الجودة
                sent_count = send_broadcast_signal(signal_data, quality_score)
                
                print(f"   📤 تم الإرسال لـ {sent_count} مشترك")
                
                results.append({
                    'symbol': symbol,
                    'quality': quality_score,
                    'sent_to': sent_count
                })
                
                # تأخير بسيط بين الأزواج
                time.sleep(1)
            else:
                print(f"   ⚪ {symbol}: لا توجد توصية")
                
        except Exception as e:
            print(f"   ❌ خطأ في تحليل {symbol}: {e}")
    
    # ملخص
    print(f"\n{'='*60}")
    print(f"✅ انتهى التحليل")
    print(f"📊 إجمالي التوصيات: {len(results)}")
    
    if results:
        print(f"\nالتوصيات المرسلة:")
        for r in results:
            print(f"   • {r['symbol']}: جودة {r['quality']}/100 → {r['sent_to']} مشترك")
    else:
        print("لا توجد توصيات اليوم")
    
    print(f"{'='*60}\n")
    
    return results


if __name__ == "__main__":
    run_analysis_with_vip()
