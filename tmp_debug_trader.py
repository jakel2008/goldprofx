from pathlib import Path
import sys, json
sys.path.insert(0, str(Path('d:/GOLD PRO/my-forex-app').resolve()))
from services.advanced_analyzer_engine import perform_full_analysis
from continuous_auto_trader import select_ranked_candidates, build_candidate, is_recommendation_allowed

config_path = Path('d:/GOLD PRO/auto_trading_user_config.json')
config = json.loads(config_path.read_text(encoding='utf-8'))
print('CONFIG symbols=', config.get('symbols'))
print('CONFIG intervals=', config.get('intervals'))
print('CONFIG min_score_gap=', config.get('min_score_gap'))
print('CONFIG allow_normal_signals=', config.get('allow_normal_signals'))
print('CONFIG allow_strong_signals=', config.get('allow_strong_signals'))
print('CONFIG strong_pending_only=', config.get('strong_pending_only'))
print('CONFIG min_rr_ratio=', config.get('min_rr_ratio'))
print('CONFIG max_stop_distance_percent=', config.get('max_stop_distance_percent'))
print('CONFIG max_target_distance_percent=', config.get('max_target_distance_percent'))
print('CONFIG pending_entry=', config.get('pending_entry'))

analyses=[]
for s in config.get('symbols', []):
    for i in config.get('intervals', []):
        res = perform_full_analysis(s, i)
        print('---', s, i)
        print('success=', res.get('success'))
        print('recommendation=', res.get('recommendation'))
        print('buy_score=', res.get('buy_score'))
        print('sell_score=', res.get('sell_score'))
        print('score_gap=', abs(int(res.get('buy_score') or 0) - int(res.get('sell_score') or 0)))
        print('entry=', res.get('entry_point'))
        print('sl=', res.get('stop_loss'))
        print('tp1=', res.get('take_profit1'))
        print('tp2=', res.get('take_profit2'))
        print('tp3=', res.get('take_profit3'))
        print('market_regime=', res.get('market_regime'))
        print('confidence=', res.get('confidence'))
        print('error=', res.get('error'))
        candidate = build_candidate(s, i, res)
        print('candidate side=', candidate.get('side'), 'rank_score=', candidate.get('rank_score'), 'score_gap=', candidate.get('score_gap'))
        analyses.append(candidate)

ranked = select_ranked_candidates(config, analyses)
print('ranked count=', len(ranked))
for idx, item in enumerate(ranked, start=1):
    print('RANK', idx, item.get('symbol'), item.get('interval'), item.get('recommendation'), item.get('score_gap'), item.get('rank_score'))
