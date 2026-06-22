# MT5 Setup Guide

This project now includes a full MT5 bridge backend with live data and execution APIs.

## 1) Install dependency

Use the same Python environment that runs the web app:

```powershell
pip install MetaTrader5
```

## 2) Configure environment

Set these variables before starting the server:

- `MT5_ENABLED=true`
- `MT5_ALLOW_TRADING=false` (keep false first)
- `MT5_LOGIN=12345678`
- `MT5_PASSWORD=your_password`
- `MT5_SERVER=YourBroker-Server`
- `MT5_PATH=C:/Program Files/MetaTrader 5/terminal64.exe`
- `MT5_MAGIC=88001` (optional)
- `MT5_DEVIATION=20` (optional)
- `MT5_DEFAULT_VOLUME=0.01` (optional)

Notes:
- Keep `MT5_ALLOW_TRADING=false` during testing.
- Turn on real execution only after dry-run checks are successful.

## 3) Available admin APIs

All endpoints below require admin session.

- `GET /api/admin/mt5/status`
- `POST /api/admin/mt5/connect`
- `POST /api/admin/mt5/disconnect`
- `GET /api/admin/mt5/live?symbols=XAUUSD,BTCUSD,EURUSD`
- `GET /api/admin/mt5/snapshot?symbols=XAUUSD,BTCUSD`
- `GET /api/admin/mt5/rates?symbol=XAUUSD&timeframe=M5&count=300`
- `GET /api/admin/mt5/history?hours=24`
- `POST /api/admin/mt5/order`
- `POST /api/admin/mt5/execute-signal`

## 4) Order API example

```json
{
  "symbol": "XAUUSD",
  "side": "buy",
  "volume": 0.01,
  "sl": 2320.0,
  "tp": 2350.0,
  "dry_run": true,
  "comment": "manual test"
}
```

## 5) Execute-signal API example

Supports your signal schema (`symbol/pair`, `signal_type/trade_type/signal`, `sl/stop_loss`, `tp1..tp3`).

```json
{
  "symbol": "BTCUSD",
  "signal_type": "buy",
  "stop_loss": 61500,
  "take_profit_1": 62800,
  "take_profit_2": 63200,
  "take_profit_3": 63800,
  "volume": 0.03,
  "split_tp": true,
  "dry_run": true
}
```

When `split_tp=true`, volume is split across TP levels.

## 6) Safe activation sequence

1. Connect and verify:
   - `POST /api/admin/mt5/connect`
   - `GET /api/admin/mt5/status`
2. Validate live feed:
   - `GET /api/admin/mt5/live?symbols=XAUUSD,BTCUSD,EURUSD`
3. Validate dry-run execution:
   - `POST /api/admin/mt5/order` with `dry_run=true`
   - `POST /api/admin/mt5/execute-signal` with `dry_run=true`
4. Enable trading:
   - set `MT5_ALLOW_TRADING=true`
   - restart web app
5. Send first real order with small volume.

## 7) Data coverage from MT5

The bridge supports fetching:
- account info
- open positions
- pending orders
- tick/live quotes for multi-symbol
- OHLC rates (M1/M5/M15/M30/H1/H4/D1)
- history (deals/orders)
