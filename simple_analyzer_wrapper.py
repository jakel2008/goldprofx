#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
واجهة بسيطة للمحلل المتقدم
"""

from analysis_engine import AnalysisEngine

# رموز الأزواج
SYMBOL_MAP = {
    'EURUSD': 'EURUSD=X',
    'GBPUSD': 'GBPUSD=X',
    'USDJPY': 'USDJPY=X',
    'XAUUSD': 'GC=F',  # Gold
    'BTCUSD': 'BTC-USD',
    'ETHUSD': 'ETH-USD',
    'AUDUSD': 'AUDUSD=X',
    'USDCAD': 'USDCAD=X',
    'USDCHF': 'USDCHF=X',
    'NZDUSD': 'NZDUSD=X'
}

def full_analysis(symbol, timeframe='1d'):
    """
    تحليل شامل لزوج معين
    
    Args:
        symbol: رمز الزوج (EURUSD, GBPUSD, إلخ)
        timeframe: الإطار الزمني (1d, 1h, إلخ)
    
    Returns:
        dict: نتائج التحليل
    """
    try:
        # تحويل الرمز
        symbol = symbol.upper().replace('/', '').replace('-', '')
        ticker = SYMBOL_MAP.get(symbol)
        
        if not ticker:
            # محاولة استخدام الرمز كما هو مع =X
            ticker = f"{symbol}=X"
        
        # إنشاء محرك التحليل
        engine = AnalysisEngine()
        
        # تنفيذ التحليل
        result = engine.analyze_symbol(symbol, ticker, timeframe)
        
        if result:
            # تحويل الإجماع لصيغة موحدة
            consensus = result.get('consensus', {})
            signal = consensus.get('signal', 'hold').upper()
            strength = consensus.get('strength', 0)
            
            # تجميع نتائج الاستراتيجيات
            strategies = {}
            for strategy_name, strategy_data in result.get('strategies_results', {}).items():
                strategies[strategy_name] = {
                    'signal': strategy_data.get('signal', 'hold'),
                    'confidence': strategy_data.get('confidence', 0)
                }
            
            return {
                'success': True,
                'symbol': result['symbol'],
                'timeframe': result['timeframe'],
                'consensus': signal,
                'consensus_strength': strength,
                'current_price': result.get('current_price', 0),
                'buy_votes': consensus.get('buy_votes', 0),
                'sell_votes': consensus.get('sell_votes', 0),
                'strategies': strategies,
                'timestamp': result.get('timestamp', '')
            }
        else:
            return {
                'success': False,
                'error': 'فشل التحليل - لم يتم إرجاع نتائج'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'خطأ في التحليل: {str(e)}'
        }

# للاختبار
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("🧪 اختبار المحلل البسيط")
    print("="*60)
    
    result = full_analysis('EURUSD', '1d')
    
    if result.get('success'):
        print(f"✅ نجح التحليل!")
        print(f"   الزوج: {result['symbol']}")
        print(f"   الإجماع: {result['consensus']}")
        print(f"   القوة: {result['consensus_strength']}%")
        print(f"   السعر: {result['current_price']:.5f}")
        print(f"\n📊 الاستراتيجيات:")
        for name, data in result['strategies'].items():
            print(f"   {name}: {data['signal']} ({data['confidence']}%)")
    else:
        print(f"❌ فشل: {result.get('error')}")
