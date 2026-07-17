# Auto Risk Sizing Applied

Generated at: 2026-07-04

## Goal

Trade volume, per-trade loss, daily loss, and daily profit lock are now based on each wallet's actual account value instead of a fixed lot size.

## Code Changes

Updated `continuous_auto_trader.py`:

- `calc_risk_volume(...)` now receives `use_equity` explicitly from config.
- `max_risk_usd_per_trade=0.0` now means no fixed USD cap; the cap is based on account equity percentage.
- Added percentage-based daily controls:
  - `daily_loss_limit_percent_of_equity`
  - `daily_profit_lock_percent_of_equity`
  - `ignore_consecutive_losses_if_daily_pnl_above_percent_of_equity`
- Execution logs now include sizing evidence:
  - `risk_basis`
  - `account_value_used`
  - `calculated_risk_amount`
  - `loss_per_lot`

Updated `multi_account_trader_gui.py`:

- The GUI preset `🏆 XAUUSD TP3 Focus (Best Report)` now uses automatic sizing.
- The risk percent field now writes both:
  - `risk_percent`
  - `max_risk_percent_of_equity`

## Applied Strategy Values

Applied to the shared template and all enabled multi-account configs:

- `fixed_volume`: `0.0`
- `use_equity_for_risk`: `true`
- `risk_percent`: `1.0`
- `max_risk_percent_of_equity`: `1.0`
- `max_risk_usd_per_trade`: `0.0`
- `daily_loss_limit_usd`: `0.0`
- `daily_loss_limit_percent_of_equity`: `3.0`
- `daily_profit_lock_usd`: `0.0`
- `daily_profit_lock_percent_of_equity`: `6.0`
- `ignore_consecutive_losses_if_daily_pnl_above_usd`: `0.0`
- `ignore_consecutive_losses_if_daily_pnl_above_percent_of_equity`: `1.0`

## Meaning

For every trade:

1. The bot reads current MT5 account equity.
2. It calculates allowed risk = `equity * risk_percent / 100`.
3. It calculates loss per 1 lot from entry-to-stop distance and broker tick value.
4. It computes lot size = allowed risk / loss per 1 lot.
5. It normalizes the lot to broker min/step/max.
6. It blocks the trade if the normalized lot would exceed the configured risk cap.

Daily controls:

- Daily loss stop = `equity * 3%`.
- Daily profit lock = `equity * 6%`.
- Consecutive-loss ignore floor = `equity * 1%`.

## Validation Snapshot

Validated with a dry sizing check using a 10 USD XAUUSD stop distance:

| Account | Equity | Risk % | Risk Amount | Calculated Lot | Estimated Loss | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| account1_gold | 109.14 | 1.0% | 1.09 | 0.01 | 10.00 | Broker min lot is larger than strict 1% risk, so live logic will skip trades that exceed the risk cap. |
| account2_bitcoin | 8638.95 | 1.0% | 86.39 | 0.08 | 80.00 | Dynamic lot is within risk cap. |

## Backups

A backup was created before applying automatic risk to each account:

- `accounts/account1_gold/config.backup_before_auto_risk_2026-07-04.json`
- `accounts/account2_bitcoin/config.backup_before_auto_risk_2026-07-04.json`
- `accounts/account3/config.backup_before_auto_risk_2026-07-04.json`
- `accounts/account4/config.backup_before_auto_risk_2026-07-04.json`
- `accounts/account5/config.backup_before_auto_risk_2026-07-04.json`
- `accounts/account6/config.backup_before_auto_risk_2026-07-04.json`
- `accounts/account7/config.backup_before_auto_risk_2026-07-04.json`
- `accounts/account8/config.backup_before_auto_risk_2026-07-04.json`
- `accounts/account9/config.backup_before_auto_risk_2026-07-04.json`
- `accounts/account10/config.backup_before_auto_risk_2026-07-04.json`

## Important Operational Note

Small accounts may not be able to open XAUUSD safely at 1% risk if the broker minimum volume is `0.01` and the stop distance is wide. In that case, the bot will skip the trade instead of violating the configured risk percentage.

This is intentional risk protection.
