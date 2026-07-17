# XAUUSD TP3 Focus Applied To Multi-Account Wallets

Generated at: 2026-07-04

## What Was Applied

All enabled accounts listed in `multi_account_config.json` were updated to use the shared `XAUUSD TP3 Focus` strategy template.

Shared template:

- `accounts/xauusd_tp3_focus_template.json`

Multi-account GUI preset:

- `🏆 XAUUSD TP3 Focus (Best Report)` in `multi_account_trader_gui.py`
- Selecting this preset applies `tp_execution_mode=tp3_only` and keeps the strategy separate from the older gold presets.

Core strategy settings applied:

- `symbols`: `XAUUSD` only
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
- `trading_sessions_utc`: Monday-Wednesday, `15:00-21:00` UTC
- `daily_loss_limit_usd`: `30.0`
- `daily_profit_lock_usd`: `120.0`
- `max_consecutive_losses`: `3`

## Data Source

`run_multi_account_traders.py` now passes these environment variables to each trader process:

- `AUTO_TRADER_USE_MT5_MARKET_DATA=1`
- `AUTO_TRADER_REQUIRE_MT5_MARKET_DATA=1`
- `ENABLE_MT5_MARKET_DATA=1`
- `MT5_MARKET_DATA_MODE=mt5_only`

This makes the strategy analyze market data from the same MT5 wallet/terminal used for execution.

## Updated Accounts

| Account ID | Strategy Name | Config | Backup |
| --- | --- | --- | --- |
| account1_gold | account1_gold_xauusd_tp3_focus_v1 | `accounts/account1_gold/config.json` | `accounts/account1_gold/config.backup_before_xauusd_tp3_focus_2026-07-04.json` |
| account2_bitcoin | account2_bitcoin_xauusd_tp3_focus_v1 | `accounts/account2_bitcoin/config.json` | `accounts/account2_bitcoin/config.backup_before_xauusd_tp3_focus_2026-07-04.json` |
| account3 | account3_xauusd_tp3_focus_v1 | `accounts/account3/config.json` | `accounts/account3/config.backup_before_xauusd_tp3_focus_2026-07-04.json` |
| account4 | account4_xauusd_tp3_focus_v1 | `accounts/account4/config.json` | `accounts/account4/config.backup_before_xauusd_tp3_focus_2026-07-04.json` |
| account5 | account5_xauusd_tp3_focus_v1 | `accounts/account5/config.json` | `accounts/account5/config.backup_before_xauusd_tp3_focus_2026-07-04.json` |
| account6 | account6_xauusd_tp3_focus_v1 | `accounts/account6/config.json` | `accounts/account6/config.backup_before_xauusd_tp3_focus_2026-07-04.json` |
| account7 | account7_xauusd_tp3_focus_v1 | `accounts/account7/config.json` | `accounts/account7/config.backup_before_xauusd_tp3_focus_2026-07-04.json` |
| account8 | account8_xauusd_tp3_focus_v1 | `accounts/account8/config.json` | `accounts/account8/config.backup_before_xauusd_tp3_focus_2026-07-04.json` |
| account9 | account9_xauusd_tp3_focus_v1 | `accounts/account9/config.json` | `accounts/account9/config.backup_before_xauusd_tp3_focus_2026-07-04.json` |
| account10 | account10_xauusd_tp3_focus_v1 | `accounts/account10/config.json` | `accounts/account10/config.backup_before_xauusd_tp3_focus_2026-07-04.json` |

## Runtime Readiness Check

The configs are applied to all accounts, but only accounts with complete wallet credentials can actually run.

Currently runnable accounts:

- `account1_gold`
- `account2_bitcoin`

Accounts currently skipped by `run_multi_account_traders.py` because `wallet.json` is missing MT5 login/server details:

- `account3`
- `account4`
- `account5`
- `account6`
- `account7`
- `account8`
- `account9`
- `account10`

To make these accounts live, complete each wallet file with:

- `login`
- `password`
- `server`
- unique MT5 `path` for that account

Important: each simultaneously running account must use a separate MT5 terminal path. `run_multi_account_traders.py` skips accounts that share the same terminal path.

## Start Command

```powershell
& "D:\GOLD PRO\.venv-3\Scripts\python.exe" "D:\GOLD PRO\run_multi_account_traders.py" --registry "D:\GOLD PRO\multi_account_config.json"
```

## Verification Command

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*continuous_auto_trader.py*' } | Select-Object ProcessId,CreationDate,CommandLine | Format-List
```

Expected trade evidence in each account log:

- `tp_execution_mode`: `tp3_only`
- MT5 order comment: `GOLD_PRO_TP3`
- symbol: `XAUUSD` resolved by broker as needed, such as `XAUUSDm`

## Rollback

Each account has its own backup file. To rollback one account, copy its backup over `config.json`.

Example:

```powershell
Copy-Item "D:\GOLD PRO\accounts\account3\config.backup_before_xauusd_tp3_focus_2026-07-04.json" "D:\GOLD PRO\accounts\account3\config.json" -Force
```
