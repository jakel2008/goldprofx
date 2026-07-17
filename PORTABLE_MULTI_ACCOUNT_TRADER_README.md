# GOLD PRO Multi-Account Trader Portable Setup

Use this when moving the multi-account trader to another Windows PC or VPS.

## What The Package Contains

- `multi_account_trader_gui.py` and optional `multi_account_trader_gui.exe`
- `continuous_auto_trader.py` and optional `continuous_auto_trader.exe`
- `run_multi_account_traders.py`
- `mt5_bridge.py`
- `forex_analyzer.py`
- `my-forex-app/services/advanced_analyzer_engine.py`
- `multi_account_config.json`
- `accounts/` with config and wallet templates
- `accounts/xauusd_tp3_focus_template.json`
- reports explaining strategy choice and auto risk sizing
- launchers and setup scripts

## First-Time Setup On Another Windows Machine

1. Install MetaTrader 5 terminal(s).
2. For simultaneous multi-account trading, install or copy a separate MT5 terminal folder per account.
3. Extract the package folder.
4. If using source mode, run:

```bat
SETUP_PYTHON_ENV.bat
```

5. Start the GUI:

```bat
START_DESKTOP_APP.bat
```

If the EXE launcher is not available, use:

```bat
START_DESKTOP_APP_FROM_SOURCE.bat
```

## Wallet Setup

For each account in `accounts/<account_id>/wallet.json`, fill:

- `login`
- `password`
- `server`
- `path` to that account's `terminal64.exe`
- unique `magic`

Do not reuse the same MT5 terminal path for two accounts that must run at the same time.

## Strategy Preset

The tested strategy is available in the GUI preset list as:

```text
🏆 XAUUSD TP3 Focus (Best Report)
```

It applies:

- XAUUSD only
- TP3 only
- automatic lot sizing from account equity
- MT5-only data source
- Monday-Wednesday 15:00-21:00 UTC trading session

## Start Multi-Account Engine

From GUI: save/test accounts, then start accounts.

From command line:

```bat
START_MULTI_ACCOUNT_TRADER_FROM_SOURCE.bat
```

Or:

```powershell
python run_multi_account_traders.py --registry multi_account_config.json
```

## Verify Runtime

```powershell
Get-CimInstance Win32_Process |
Where-Object { $_.CommandLine -like '*continuous_auto_trader.py*' } |
Select-Object ProcessId,CreationDate,CommandLine |
Format-List
```

Expected trade evidence in logs:

- `tp_execution_mode`: `tp3_only`
- MT5 comment: `GOLD_PRO_TP3`
- source: `MT5`

## Notes

- GitHub is not a VPS. Use Windows VPS/RDP for 24/7 operation.
- If the PC/VPS is fully off, the bot cannot open new trades. Existing broker-side SL/TP remain on MT5 broker servers.
- Wallet passwords are removed from the package by default unless packaging is run with `--include-wallet-secrets`.
