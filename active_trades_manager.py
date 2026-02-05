# -*- coding: utf-8 -*-
"""
نظام إدارة وعرض الصفقات النشطة
Active Trades Management System
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

class ActiveTradesManager:
    """مدير الصفقات النشطة"""
    
    def __init__(self, trades_file="active_trades.json"):
        self.trades_file = Path(__file__).parent / trades_file
        self.ensure_file_exists()
    
    def ensure_file_exists(self):
        """التأكد من وجود الملف"""
        if not self.trades_file.exists():
            self.save_trades([])
    
    def load_trades(self) -> List[Dict]:
        """تحميل الصفقات"""
        try:
            with open(self.trades_file, 'r', encoding='utf-8') as f:
                trades = json.load(f)
                return trades if isinstance(trades, list) else []
        except:
            return []
    
    def save_trades(self, trades: List[Dict]):
        """حفظ الصفقات"""
        try:
            with open(self.trades_file, 'w', encoding='utf-8') as f:
                json.dump(trades, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"خطأ في حفظ الصفقات: {e}")
    
    def add_trade(self, trade_data: Dict) -> str:
        """إضافة صفقة جديدة"""
        trades = self.load_trades()
        
        # إنشاء معرف فريد
        trade_id = f"{trade_data['symbol']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        trade = {
            'id': trade_id,
            'symbol': trade_data['symbol'],
            'direction': trade_data['direction'],  # buy or sell
            'entry_price': trade_data['entry_price'],
            'current_price': trade_data.get('current_price', trade_data['entry_price']),
            'stop_loss': trade_data.get('stop_loss'),
            'take_profit_1': trade_data.get('take_profit_1'),
            'take_profit_2': trade_data.get('take_profit_2'),
            'take_profit_3': trade_data.get('take_profit_3'),
            'entry_time': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat(),
            'status': 'active',  # active, tp1_hit, tp2_hit, tp3_hit, sl_hit, closed
            'profit_loss': 0.0,
            'profit_loss_percentage': 0.0,
            'volume': trade_data.get('volume', 1.0),
            'strategy': trade_data.get('strategy', 'ICT'),
            'timeframe': trade_data.get('timeframe', '1H'),
            'quality_score': trade_data.get('quality_score', 0),
            'notes': trade_data.get('notes', '')
        }
        
        trades.append(trade)
        self.save_trades(trades)
        
        return trade_id
    
    def update_trade(self, trade_id: str, updates: Dict) -> bool:
        """تحديث صفقة"""
        trades = self.load_trades()
        
        for trade in trades:
            if trade['id'] == trade_id:
                trade.update(updates)
                trade['last_update'] = datetime.now().isoformat()
                self.save_trades(trades)
                return True
        
        return False
    
    def update_current_price(self, trade_id: str, current_price: float) -> Dict:
        """تحديث السعر الحالي وحساب الربح/الخسارة"""
        trades = self.load_trades()
        
        for trade in trades:
            if trade['id'] == trade_id and trade['status'] == 'active':
                trade['current_price'] = current_price
                
                # حساب الربح/الخسارة
                entry = trade['entry_price']
                direction = trade['direction'].lower()
                
                if direction == 'buy':
                    pnl = current_price - entry
                    pnl_pct = ((current_price - entry) / entry) * 100
                else:  # sell
                    pnl = entry - current_price
                    pnl_pct = ((entry - current_price) / entry) * 100
                
                trade['profit_loss'] = pnl
                trade['profit_loss_percentage'] = pnl_pct
                
                # فحص الأهداف ووقف الخسارة
                if direction == 'buy':
                    if trade.get('take_profit_3') and current_price >= trade['take_profit_3']:
                        trade['status'] = 'tp3_hit'
                    elif trade.get('take_profit_2') and current_price >= trade['take_profit_2']:
                        trade['status'] = 'tp2_hit'
                    elif trade.get('take_profit_1') and current_price >= trade['take_profit_1']:
                        trade['status'] = 'tp1_hit'
                    elif trade.get('stop_loss') and current_price <= trade['stop_loss']:
                        trade['status'] = 'sl_hit'
                else:  # sell
                    if trade.get('take_profit_3') and current_price <= trade['take_profit_3']:
                        trade['status'] = 'tp3_hit'
                    elif trade.get('take_profit_2') and current_price <= trade['take_profit_2']:
                        trade['status'] = 'tp2_hit'
                    elif trade.get('take_profit_1') and current_price <= trade['take_profit_1']:
                        trade['status'] = 'tp1_hit'
                    elif trade.get('stop_loss') and current_price >= trade['stop_loss']:
                        trade['status'] = 'sl_hit'
                
                trade['last_update'] = datetime.now().isoformat()
                
                self.save_trades(trades)
                return trade
        
        return None
    
    def get_active_trades(self) -> List[Dict]:
        """الحصول على الصفقات النشطة فقط"""
        trades = self.load_trades()
        return [t for t in trades if t['status'] in ['active', 'tp1_hit', 'tp2_hit']]
    
    def get_all_trades(self) -> List[Dict]:
        """الحصول على جميع الصفقات"""
        return self.load_trades()
    
    def close_trade(self, trade_id: str, close_price: float, reason: str = '') -> bool:
        """إغلاق صفقة"""
        trades = self.load_trades()
        
        for trade in trades:
            if trade['id'] == trade_id:
                trade['status'] = 'closed'
                trade['close_price'] = close_price
                trade['close_time'] = datetime.now().isoformat()
                trade['close_reason'] = reason
                
                # حساب الربح/الخسارة النهائي
                entry = trade['entry_price']
                direction = trade['direction'].lower()
                
                if direction == 'buy':
                    pnl = close_price - entry
                    pnl_pct = ((close_price - entry) / entry) * 100
                else:
                    pnl = entry - close_price
                    pnl_pct = ((entry - close_price) / entry) * 100
                
                trade['profit_loss'] = pnl
                trade['profit_loss_percentage'] = pnl_pct
                
                self.save_trades(trades)
                
                # نقل إلى قاعدة بيانات الصفقات المغلقة
                try:
                    from trade_statistics import TradeStatistics
                    stats = TradeStatistics()
                    stats.add_trade({
                        'symbol': trade['symbol'],
                        'direction': trade['direction'],
                        'entry_price': trade['entry_price'],
                        'exit_price': close_price,
                        'stop_loss': trade.get('stop_loss'),
                        'take_profit_1': trade.get('take_profit_1'),
                        'take_profit_2': trade.get('take_profit_2'),
                        'take_profit_3': trade.get('take_profit_3'),
                        'profit_loss': pnl,
                        'profit_percentage': pnl_pct,
                        'volume': trade.get('volume', 1.0),
                        'strategy': trade.get('strategy', 'ICT'),
                        'timeframe': trade.get('timeframe', '1H'),
                        'notes': f"{reason} | {trade.get('notes', '')}"
                    })
                except:
                    pass
                
                return True
        
        return False
    
    def get_trade_summary(self) -> Dict:
        """الحصول على ملخص الصفقات"""
        trades = self.load_trades()
        active_trades = [t for t in trades if t['status'] in ['active', 'tp1_hit', 'tp2_hit']]
        
        total_pnl = sum(t.get('profit_loss', 0) for t in active_trades)
        
        buy_trades = [t for t in active_trades if t['direction'] == 'buy']
        sell_trades = [t for t in active_trades if t['direction'] == 'sell']
        
        winning_trades = [t for t in active_trades if t.get('profit_loss', 0) > 0]
        losing_trades = [t for t in active_trades if t.get('profit_loss', 0) < 0]
        
        return {
            'total_active': len(active_trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'total_pnl': total_pnl,
            'avg_pnl': total_pnl / len(active_trades) if active_trades else 0
        }
    
    def generate_html_display(self) -> str:
        """إنشاء عرض HTML للصفقات"""
        trades = self.get_active_trades()
        summary = self.get_trade_summary()
        
        html = f"""
        <div class="trades-summary">
            <div class="row mb-3">
                <div class="col-md-3">
                    <div class="metric-card">
                        <h4>{summary['total_active']}</h4>
                        <p>الصفقات النشطة</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card">
                        <h4 class="text-success">{summary['winning_trades']}</h4>
                        <p>رابحة</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card">
                        <h4 class="text-danger">{summary['losing_trades']}</h4>
                        <p>خاسرة</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card">
                        <h4 class="{'text-success' if summary['total_pnl'] > 0 else 'text-danger'}">
                            ${summary['total_pnl']:.2f}
                        </h4>
                        <p>إجمالي الربح/الخسارة</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="trades-list">
        """
        
        for trade in trades:
            direction_icon = '🔼' if trade['direction'] == 'buy' else '🔽'
            direction_class = 'text-success' if trade['direction'] == 'buy' else 'text-danger'
            pnl_class = 'text-success' if trade.get('profit_loss', 0) > 0 else 'text-danger'
            
            html += f"""
            <div class="trade-card mb-3">
                <div class="row">
                    <div class="col-md-2">
                        <h5 class="{direction_class}">{direction_icon} {trade['symbol']}</h5>
                        <small class="text-muted">{trade.get('timeframe', '1H')}</small>
                    </div>
                    <div class="col-md-2">
                        <p class="mb-0"><strong>الدخول:</strong> {trade['entry_price']}</p>
                        <p class="mb-0"><strong>الحالي:</strong> {trade.get('current_price', trade['entry_price'])}</p>
                    </div>
                    <div class="col-md-3">
                        <p class="mb-0"><small>TP1: {trade.get('take_profit_1', 'N/A')}</small></p>
                        <p class="mb-0"><small>TP2: {trade.get('take_profit_2', 'N/A')}</small></p>
                        <p class="mb-0"><small>SL: {trade.get('stop_loss', 'N/A')}</small></p>
                    </div>
                    <div class="col-md-2">
                        <p class="mb-0 {pnl_class}">
                            <strong>{trade.get('profit_loss', 0):.2f}</strong>
                        </p>
                        <small>({trade.get('profit_loss_percentage', 0):.2f}%)</small>
                    </div>
                    <div class="col-md-2">
                        <span class="badge bg-info">{trade['status']}</span>
                        <br><small>{datetime.fromisoformat(trade['entry_time']).strftime('%Y-%m-%d %H:%M')}</small>
                    </div>
                    <div class="col-md-1">
                        <button class="btn btn-sm btn-danger" onclick="closeTrade('{trade['id']}')">
                            إغلاق
                        </button>
                    </div>
                </div>
            </div>
            """
        
        html += "</div>"
        
        return html

# مثال الاستخدام
if __name__ == "__main__":
    manager = ActiveTradesManager()
    
    # إضافة صفقة تجريبية
    trade_id = manager.add_trade({
        'symbol': 'EUR/USD',
        'direction': 'buy',
        'entry_price': 1.0850,
        'stop_loss': 1.0820,
        'take_profit_1': 1.0900,
        'take_profit_2': 1.0950,
        'take_profit_3': 1.1000,
        'volume': 1.0,
        'strategy': 'ICT',
        'timeframe': '1H',
        'quality_score': 85
    })
    
    print(f"✅ تم إضافة صفقة: {trade_id}")
    
    # عرض الملخص
    summary = manager.get_trade_summary()
    print(f"\n📊 ملخص الصفقات:")
    print(f"   الصفقات النشطة: {summary['total_active']}")
    print(f"   الرابحة: {summary['winning_trades']}")
    print(f"   الخاسرة: {summary['losing_trades']}")
