# Wallet 262972266 TP3 Execution Plan

Generated at: 2026-07-04 18:10 local time (UTC+03)

## Source Data Reviewed

- MT5 wallet: `accounts/account2_bitcoin/wallet.json`
- Account: `262972266`
- Server: `Exness-MT5Trial16`
- Wallet magic: `88012`
- Strategy performance report: `reports/wallet_262972266_strategy_review.md`
- Position-level CSV: `reports/wallet_262972266_strategy_review_trades.csv`
- Applied strategy file: `accounts/account2_bitcoin/strategy_gold_tp3_focus_v1.json`
- Active runtime config: `accounts/account2_bitcoin/config.json`
- Previous config backup: `accounts/account2_bitcoin/config.backup_before_tp3_focus_2026-07-04.json`

## Best Strategy From Report

The best net strategy for this wallet was `GOLD_PRO_TP3`.

| Strategy | Positions | Wins | Losses | Flat | Net P/L |
| --- | --- | --- | --- | --- | --- |
| GOLD_PRO_TP3 | 275 | 204 | 69 | 2 | +3239.05 |
| GOLD_PRO_TP2 | 252 | 182 | 68 | 2 | +2929.50 |
| GOLD_PRO_TP1 | 115 | 55 | 59 | 1 | +1470.28 |
| GOLD_PRO_SIGNAL | 396 | 246 | 115 | 35 | -203.31 |

The strongest strategy-symbol pair was `GOLD_PRO_TP3` on `XAUUSDm`.

| Strategy | Symbol | Positions | Wins | Losses | Net P/L |
| --- | --- | --- | --- | --- | --- |
| GOLD_PRO_TP3 | XAUUSDm | 47 | 39 | 8 | +2735.19 |
| GOLD_PRO_TP2 | XAUUSDm | 49 | 40 | 9 | +2483.93 |
| GOLD_PRO_TP1 | XAUUSDm | 40 | 32 | 8 | +1464.80 |

## Best Days And Times

The source report timestamps were produced in local machine time (UTC+03). Runtime sessions use UTC.

Best `GOLD_PRO_TP3 + XAUUSDm` days:

| Local Day | Positions | Wins | Losses | Win Rate | Net P/L |
| --- | --- | --- | --- | --- | --- |
| Tuesday | 43 | 36 | 7 | 83.7% | +2463.40 |
| Monday | 1 | 1 | 0 | 100.0% | +155.77 |
| Wednesday | 3 | 2 | 1 | 66.7% | +116.02 |

Best local hours for `GOLD_PRO_TP3 + XAUUSDm`:

| Local Hour | UTC Hour | Positions | Wins | Losses | Win Rate | Net P/L |
| --- | --- | --- | --- | --- | --- | --- |
| 18:00 | 15:00 | 15 | 15 | 0 | 100.0% | +1139.41 |
| 23:00 | 20:00 | 6 | 6 | 0 | 100.0% | +448.22 |
| 21:00 | 18:00 | 5 | 5 | 0 | 100.0% | +427.23 |
| 22:00 | 19:00 | 4 | 4 | 0 | 100.0% | +296.08 |
| 20:00 | 17:00 | 4 | 4 | 0 | 100.0% | +293.32 |

Avoided windows:

| Local Hour | Reason |
| --- | --- |
| 17:00 | `GOLD_PRO_TP3 + XAUUSDm` net was -61.79 with 4 losses out of 6. |
| Thursday | XAUUSD overall was negative in the report. |
| Friday | XAUUSD overall was slightly negative and noisy despite high trade count. |

## Applied Runtime Strategy

Applied strategy name: `wallet2_xauusd_tp3_focus_v1`

Key settings:

- `symbols`: `XAUUSD` only. The MT5 bridge resolves this to broker symbol `XAUUSDm` when needed.
- `split_tp`: `true`
- `tp_execution_mode`: `tp3_only`
- `fixed_volume`: `0.01`
- `max_open_positions`: `1`
- `max_trades_per_cycle`: `1`
- `one_position_per_symbol`: `true`
- `cooldown_minutes_per_symbol`: `12`
- `pending_entry`: `false`
- `market_reprice_entry`: `true`
- `gold_scalping_strategy_enabled`: `true`
- `gold_trend_filter_enabled`: `true`
- `force_gold_trading_now`: `false`
- `daily_loss_limit_usd`: `30.0`
- `daily_profit_lock_usd`: `120.0`
- `max_consecutive_losses`: `3`

Trading session applied:

```json
[
  {
    "start": "15:00",
    "end": "21:00",
    "weekdays": [0, 1, 2]
  }
]
```

This means Monday-Wednesday, 15:00-21:00 UTC, equivalent to 18:00-00:00 local machine time (UTC+03).

## Data Source Control

The analyzer path used by `continuous_auto_trader.py` is `my-forex-app/services/advanced_analyzer_engine.py`.

Verified behavior:

- When `MT5_WALLET_CONFIG` is set, the analyzer enables MT5 market data by default through `AUTO_TRADER_USE_MT5_MARKET_DATA=1`.
- It also requires MT5 data by default through `AUTO_TRADER_REQUIRE_MT5_MARKET_DATA=1`.
- `run_multi_account_traders.py` now explicitly passes:
  - `AUTO_TRADER_USE_MT5_MARKET_DATA=1`
  - `AUTO_TRADER_REQUIRE_MT5_MARKET_DATA=1`
  - `ENABLE_MT5_MARKET_DATA=1`
  - `MT5_MARKET_DATA_MODE=mt5_only`

This keeps analysis and execution tied to the same MT5 wallet/terminal rather than Yahoo or another external source.

## Execution Checklist

Before starting:

1. Confirm MT5 terminal in `accounts/account2_bitcoin/wallet.json` is open and logged into account `262972266`.
2. Confirm AutoTrading is enabled in MT5.
3. Confirm no existing manual/open positions conflict with `XAUUSDm`.
4. Confirm current UTC time is inside Monday-Wednesday `15:00-21:00` if live execution is desired immediately.
5. Run a one-cycle validation first with the account config.

One-cycle validation command:

```powershell
$env:MT5_WALLET_CONFIG = "D:\GOLD PRO\accounts\account2_bitcoin\wallet.json"
$env:AUTO_TRADER_ACCOUNT_ID = "account2_bitcoin"
$env:AUTO_TRADER_USE_MT5_MARKET_DATA = "1"
$env:AUTO_TRADER_REQUIRE_MT5_MARKET_DATA = "1"
$env:ENABLE_MT5_MARKET_DATA = "1"
$env:MT5_MARKET_DATA_MODE = "mt5_only"
& "D:\GOLD PRO\.venv-3\Scripts\python.exe" "D:\GOLD PRO\continuous_auto_trader.py" --config "D:\GOLD PRO\accounts\account2_bitcoin\config.json" --state "D:\GOLD PRO\accounts\account2_bitcoin\runtime_state.json" --wallet-config "D:\GOLD PRO\accounts\account2_bitcoin\wallet.json" --account-id account2_bitcoin --once
```

Start command for managed multi-account runtime:

```powershell
& "D:\GOLD PRO\.venv-3\Scripts\python.exe" "D:\GOLD PRO\run_multi_account_traders.py" --registry "D:\GOLD PRO\multi_account_config.json"
```

## Monitoring After Start

Watch this log:

- `accounts/account2_bitcoin/trader.out.log`

Expected evidence when a trade fires:

- `event`: `execute_signal`
- `symbol`: `XAUUSD`
- `tp_execution_mode`: `tp3_only`
- MT5 order comment should be `GOLD_PRO_TP3`

Stop conditions:

- Daily closed loss reaches `-30.0 USD`.
- Daily profit reaches `+120.0 USD`.
- Consecutive losses reach `3`, unless daily P/L is already above `+20.0 USD`.
- Session is outside Monday-Wednesday `15:00-21:00 UTC`.

## Rollback

To rollback to the previous configuration:

```powershell
Copy-Item "D:\GOLD PRO\accounts\account2_bitcoin\config.backup_before_tp3_focus_2026-07-04.json" "D:\GOLD PRO\accounts\account2_bitcoin\config.json" -Force
```
