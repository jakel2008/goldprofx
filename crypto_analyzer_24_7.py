# -*- coding: utf-8 -*-
"""
محلل العملات الرقمية 24/7
Crypto Analyzer - Works Around The Clock
"""

import sys
import os
import time
from datetime import datetime
import schedule

sys.path.insert(0, os.path.dirname(__file__))

# إعدادات العملات الرقمية
CRYPTO_PAIRS = [
    'BTCUSD',   # Bitcoin
    'ETHUSD',   # Ethereum
    'XRPUSD',   # Ripple
    'ADAUSD',   # Cardano
    'SOLUSD',   # Solana
    'DOGEUSD',  # Dogecoin
    'BNBUSD',   # Binance Coin
    'MATICUSD', # Polygon
]

def analyze_crypto():
    """تحليل جميع العملات الرقمية"""
    try:
        from auto_pairs_analyzer import run_daily_analysis
        print(f"\n{'='*60}")
        print(f"🔄 تحليل العملات الرقمية - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}\n")
        
        run_daily_analysis()
        
        print(f"\n✅ تم إكمال التحليل - {datetime.now().strftime('%H:%M:%S')}\n")
    except Exception as e:
        print(f"❌ خطأ في التحليل: {e}")

def main():
    """تشغيل المحلل 24/7"""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║        📊 محلل العملات الرقمية 24/7                     ║")
    print("║           Crypto Market Never Sleeps!                    ║")
    print("╚══════════════════════════════════════════════════════════╝\n")
    
    # تحليل فوري عند البدء
    print("🚀 تشغيل التحليل الأولي...")
    analyze_crypto()
    
    # جدولة التحليل كل 15 دقيقة للعملات الرقمية
    schedule.every(15).minutes.do(analyze_crypto)
    
    print("\n⏰ الجدولة:")
    print("   • تحليل كل 15 دقيقة")
    print("   • العملات:", ', '.join(CRYPTO_PAIRS))
    print("   • يعمل 24/7 بدون توقف\n")
    print("Press Ctrl+C to stop...\n")
    
    # حلقة التشغيل المستمر
    while True:
        try:
            schedule.run_pending()
            time.sleep(30)  # فحص كل 30 ثانية
        except KeyboardInterrupt:
            print("\n\n⏹️  تم إيقاف المحلل")
            break
        except Exception as e:
            print(f"⚠️ خطأ: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
