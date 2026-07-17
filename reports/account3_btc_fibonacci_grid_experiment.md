# Account3 BTC Fibonacci Grid Experiment

Generated at: 2026-07-05

## Wallet

- Account folder: `accounts/account3`
- Login: `472144533`
- Server: `Exness-MT5Trial16`
- Magic: `88013`
- Broker BTC symbol resolved as: `BTCUSDm`
- Equity during validation: `100.0 USD`

## Strategy File

- `accounts/account3/strategy_btc_fibonacci_grid_v1.json`

The strategy is currently set to:

```json
"dry_run": true
```

So no real pending orders were sent.

## User Rules Implemented

- Use M5 candles.
- Calculate Fibonacci workspace from level `0` to level `75`.
- Split workspace into:
  - `0 -> 50`: orders in the detected direction.
  - `50 -> 75`: orders in the opposite direction.
- Pending order volume: `0.01`.
- Grid spacing: `500` broker points after spread.
- Broker point for `BTCUSDm` during validation: `0.01`, so `500` broker points = `5.00` price units.
- Spread adjustment: enabled.
- Basket close target: the penultimate reversal order in the `50 -> 75` zone.
- Direction detection: EMA9/EMA34 + 12-bar momentum on M5.

## Current Dry-Run Result

Direction selected by the bot: `buy`

Reason:

- EMA9: `62668.18282`
- EMA34: `62651.91209`
- Last close: `62701.53`
- 12-bar momentum: `+162.33`

Swing and Fibonacci levels:

| Level | Price |
| --- | --- |
| Swing low | `62370.87` |
| Swing high | `63051.08` |
| Fib 0 | `62370.87` |
| Fib 50 | `62710.98` |
| Fib 75 | `62881.03` |
| Basket close | penultimate reversal order |

Latest basket-close dry-run:

| Field | Value |
| --- | --- |
| Close mode | `penultimate_reversal_order` |
| Close target | `62865.98` |
| Source order | `BTC_FIB_GRID_50-75_103` |
| Reversal orders count | `35` |
| Target reached | `false` |

Tick at validation:

| Field | Value |
| --- | --- |
| Bid | `62701.53` |
| Ask | `62711.53` |
| Spread | `10.0` price units = `1000.0` broker points |

## Broker-Point Dry-Run Result

After changing the grid from `50.0` price units to `500` broker points:

| Field | Value |
| --- | --- |
| Broker point | `0.01` |
| 500 broker points | `5.00` price units |
| Spread adjustment | `10.0` price units |
| Orders generated | `104` |
| Dry run | `true` |

Because the spread alone is `1000` broker points, the strategy remains in dry-run until final live execution is confirmed.

The order count is no longer manually capped. It is calculated from the Fibonacci distance and `grid_step_points=500.0`.

## Pending Orders Preview

| # | Zone | Side | Raw Price | Spread Adjusted Pending Price | Volume |
| --- | --- | --- | --- | --- | --- |
| 1 | 0-50 | buy | 62370.87 | 62380.87 | 0.01 |
| 2 | 0-50 | buy | 62420.87 | 62430.87 | 0.01 |
| 3 | 0-50 | buy | 62470.87 | 62480.87 | 0.01 |
| 4 | 0-50 | buy | 62520.87 | 62530.87 | 0.01 |
| 5 | 0-50 | buy | 62570.87 | 62580.87 | 0.01 |
| 6 | 0-50 | buy | 62620.87 | 62630.87 | 0.01 |
| 7 | 0-50 | buy | 62670.87 | 62680.87 | 0.01 |
| 8 | 0-50 | buy | 62710.98 | 62720.98 | 0.01 |
| 9 | 50-75 | sell | 62710.98 | 62700.98 | 0.01 |
| 10 | 50-75 | sell | 62760.98 | 62750.98 | 0.01 |
| 11 | 50-75 | sell | 62810.98 | 62800.98 | 0.01 |
| 12 | 50-75 | sell | 62860.98 | 62850.98 | 0.01 |
| 13 | 50-75 | sell | 62881.03 | 62871.03 | 0.01 |

## Files Created

- `btc_fibonacci_grid_trader.py`
- `accounts/account3/strategy_btc_fibonacci_grid_v1.json`
- `accounts/account3/btc_fibonacci_grid_state.json`
- `START_ACCOUNT3_BTC_FIB_GRID_DRYRUN.bat`

## Safety Notes

- This strategy does not use fixed SL/TP on individual pending orders yet.
- Basket management closes all matching grid orders/positions only when the basket target is reached.
- Because this is a grid-style strategy, it should remain in `dry_run` until target/stop behavior is confirmed.
- The spacing is now implemented as broker points through `grid_step_mode=broker_points` and `grid_step_points=500.0`.
