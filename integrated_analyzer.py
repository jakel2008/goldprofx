# -*- coding: utf-8 -*-
"""
محلل متقدم مدمج مع AI
Integrated Advanced Analyzer with AI
"""

import sys
import os
import json
from datetime import datetime
from advanced_signal_engine import AdvancedSignalEngine
from quality_scorer import QualityScorer

# إعدادات Telegram
BOT_TOKEN = os.environ.get("MM_TELEGRAM_BOT_TOKEN", "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A")
CHAT_ID = os.environ.get("MM_TELEGRAM_CHAT_ID", "-4732119341")

# الأزواج للتحليل
PAIRS_CONFIG = [
    {"symbol": "EUR/USD", "yf_symbol": "EURUSD=X"},
    {"symbol": "GBP/USD", "yf_symbol": "GBPUSD=X"},
    {"symbol": "USD/JPY", "yf_symbol": "USDJPY=X"},
    {"symbol": "XAU/USD", "yf_symbol": "GC=F"},
    {"symbol": "BTC/USD", "yf_symbol": "BTC-USD"},
    {"symbol": "ETH/USD", "yf_symbol": "ETH-USD"},
    {"symbol": "XRP/USD", "yf_symbol": "XRP-USD"},
    {"symbol": "ADA/USD", "yf_symbol": "ADA-USD"},
    {"symbol": "SOL/USD", "yf_symbol": "SOL-USD"},
    {"symbol": "DOGE/USD", "yf_symbol": "DOGE-USD"},
    {"symbol": "EUR/GBP", "yf_symbol": "EURGBP=X"},
    {"symbol": "AUD/USD", "yf_symbol": "AUDUSD=X"},
    {"symbol": "USD/CAD", "yf_symbol": "USDCAD=X"}
]

class IntegratedAnalyzer:
    """محلل متكامل يجمع بين المحركين"""
    
    def __init__(self):
        self.advanced_engine = AdvancedSignalEngine()
        self.quality_scorer = QualityScorer()
        self.signals_sent = []
        
    def send_telegram(self, message):
        """إرسال رسالة عبر Telegram"""
        try:
            import requests
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            
            data = {
                'chat_id': CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                print("✅ تم إرسال الإشارة بنجاح")
                return True
            else:
                print(f"❌ فشل الإرسال: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ خطأ في الإرسال: {e}")
            return False
    
    def save_signal(self, signal):
        """حفظ الإشارة في ملف"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"signals/AI_Signal_{signal['symbol'].replace('/', '')}_{timestamp}.json"
            
            os.makedirs('signals', exist_ok=True)
            
            signal_data = {
                'symbol': signal['symbol'],
                'direction': signal['direction'],
                'quality_score': signal['quality_score'],
                'confidence': signal['confidence'],
                'entry': float(signal['entry']),
                'stop_loss': float(signal['stop_loss']),
                'tp1': float(signal['tp1']),
                'tp2': float(signal['tp2']),
                'tp3': float(signal['tp3']),
                'rr_ratio': float(signal['rr_ratio']),
                'timestamp': signal['timestamp'].isoformat(),
                'timeframes': {k: {**v, 'direction': v['direction']} for k, v in signal['timeframes'].items()}
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(signal_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 تم حفظ الإشارة: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ خطأ في الحفظ: {e}")
            return False
    
    def analyze_all_pairs(self):
        """تحليل جميع الأزواج"""
        print("\n" + "="*60)
        print("🧠 بدء التحليل المتقدم بالذكاء الاصطناعي")
        print("="*60)
        
        total_analyzed = 0
        high_quality_signals = 0
        
        for pair in PAIRS_CONFIG:
            symbol = pair['symbol']
            yf_symbol = pair['yf_symbol']
            
            print(f"\n📊 تحليل {symbol}...")
            
            try:
                # إنشاء إشارة متقدمة
                signal = self.advanced_engine.generate_signal(symbol, yf_symbol)
                
                total_analyzed += 1
                
                if signal:
                    quality = signal['quality_score']
                    confidence = signal['confidence']
                    
                    print(f"   ✅ إشارة عالية الجودة: {quality}/100 (ثقة: {confidence*100:.0f}%)")
                    
                    # إرسال عبر Telegram
                    message = self.advanced_engine.format_signal_message(signal)
                    
                    if self.send_telegram(message):
                        high_quality_signals += 1
                        self.save_signal(signal)
                        self.signals_sent.append(signal)
                else:
                    print(f"   ⚠️ لا توجد إشارة قوية حالياً")
                    
            except Exception as e:
                print(f"   ❌ خطأ: {e}")
        
        # ملخص التحليل
        print("\n" + "="*60)
        print("📊 ملخص التحليل:")
        print(f"   إجمالي الأزواج المحللة: {total_analyzed}")
        print(f"   إشارات عالية الجودة: {high_quality_signals}")
        print(f"   معدل التصفية: {((total_analyzed - high_quality_signals) / total_analyzed * 100):.1f}%")
        print("="*60)
        
        return {
            'total_analyzed': total_analyzed,
            'high_quality_signals': high_quality_signals,
            'signals': self.signals_sent
        }
    
    def run_continuous_analysis(self, interval_minutes=20):
        """تشغيل التحليل المستمر"""
        import time
        
        print(f"\n🔄 بدء التحليل المستمر كل {interval_minutes} دقيقة")
        
        while True:
            try:
                self.analyze_all_pairs()
                
                print(f"\n⏰ الانتظار {interval_minutes} دقيقة حتى التحليل القادم...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("\n\n⛔ تم إيقاف التحليل بواسطة المستخدم")
                break
            except Exception as e:
                print(f"\n❌ خطأ في الحلقة الرئيسية: {e}")
                time.sleep(60)  # انتظار دقيقة قبل المحاولة مرة أخرى


if __name__ == "__main__":
    analyzer = IntegratedAnalyzer()
    
    # تحليل واحد أو مستمر
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        analyzer.run_continuous_analysis(interval_minutes=20)
    else:
        analyzer.analyze_all_pairs()
