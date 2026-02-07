## Copilot instructions (GOLD PRO)

### Big picture (what “runs” here)
- This is a Python monorepo for trading signals: analyzers generate JSON signals, a Telegram broadcaster pushes them to subscribers, and a Flask web app provides UI/admin.
- Canonical web entrypoint (used day-to-day): [web_app_complete.py](../web_app_complete.py) (Flask + templates/, auth via [user_manager.py](../user_manager.py)).
- Canonical broadcaster entrypoint (per VS Code tasks): [signal_broadcaster.py](../signal_broadcaster.py) (reads `signals/*.json` → formats → sends via Telegram Bot API).
- There are multiple legacy web variants (see [web_app.py](../web_app.py), [web_app_fixed.py](../web_app_fixed.py), [web_app_old.py](../web_app_old.py)); default to [web_app_complete.py](../web_app_complete.py) unless asked otherwise.

### Core data flow (signals)
- Producers: analyzers like [analysis_engine.py](../analysis_engine.py), [recommendations_engine.py](../recommendations_engine.py), and [analyze_all_pairs.py](../analyze_all_pairs.py) fetch market data via `yfinance` + `ta` and write JSON under `signals/`, `analysis/`, `recommendations/`.
- Consumer: [signal_broadcaster.py](../signal_broadcaster.py) scans `signals/*.json`, computes a stable ID using normalized prices + SHA1 over `symbol|direction|entry|sl|tp1|tp2|tp3`, and de-dupes via `sent_signals.json` (keeps last 1000).
- Formatting: broadcaster uses [signal_formatter.py](../signal_formatter.py) (`format_signal_message`) which expects numeric prices and formats to 5 decimals for Telegram Markdown.
- Note: the web UI primarily loads “today’s signals” from SQLite (`vip_signals.db`, table `signals`) inside [web_app_complete.py](../web_app_complete.py). The broadcaster does **not** read from that DB; it reads JSON files in `signals/`.

### Signals JSON conventions (important)
- Many scripts accept multiple field names; keep compatibility when adding new producers:
  - Symbol: `symbol` or `pair`
  - Direction/type: `signal_type` or `trade_type` or `signal`
  - Prices: `entry_price`/`entry`, `stop_loss`/`sl`, `take_profit_1..3` or `tp1..3`

### Web app patterns
- Heavy deps are intentionally lazy-imported to keep server startup fast (e.g., `yfinance` inside `get_live_price()` and `recommendations_engine.ALL_AVAILABLE_PAIRS` inside `_get_all_available_pairs()` in [web_app_complete.py](../web_app_complete.py)). Preserve this pattern.
- Auth/session: `session_token` in Flask session, validated by `user_manager.verify_session()` ([user_manager.py](../user_manager.py)). `is_admin` is derived from `users.is_admin` or `users.role`.
- Absolute access: developer username `jakel2008` bypasses plan filtering (“see all”).
- Developer identity: the absolute developer account is `jakel2008` (email `mahmoodalqaise750@gmail.com`).
- Adding admins: set `users.is_admin=1` or `users.role='admin'` (admin privileges).
- Developer-level access: only users with `users.role='developer'` should be treated as “absolute” (equivalent to `jakel2008` access); set via `UserManager.set_user_role()` in [user_manager.py](../user_manager.py).
- No other exceptions: do not add additional username-based bypasses unless explicitly requested.

### Databases (SQLite) used in practice
- `vip_subscriptions.db`: subscriber records for broadcasting (table `users`, with `status`, `plan`, and `chat_id`). Managed via [vip_subscription_system.py](../vip_subscription_system.py) (`SubscriptionManager`).
- `users.db`: web-app accounts + sessions + admin subscription requests (used by [user_manager.py](../user_manager.py) and [email_service.py](../email_service.py)).
- `vip_signals.db`: web UI reads/tracks signals and updates status/targets based on live prices (used by `load_signals()` in [web_app_complete.py](../web_app_complete.py)).
- `goldpro_system.db` / `activations.db`: present for other/legacy flows (see [db_migrate.py](../db_migrate.py)); avoid building new features on these unless you confirm the running entrypoint.

### Telegram integration
- Env vars used across sender/broadcaster: `MM_TELEGRAM_BOT_TOKEN`, `MM_TELEGRAM_CHAT_ID`.
- Some scripts still contain hardcoded token defaults; do not add new hardcoded secrets—prefer env vars and config files.
- Multi-bot support exists via `bots_config.json` and helpers in [telegram_sender.py](../telegram_sender.py) (HTML parse mode), while [signal_broadcaster.py](../signal_broadcaster.py) sends Markdown directly.

### Windows + VS Code workflow (how this repo is typically run)
- Web server: run the VS Code task `restart-web-server` (kills port 5000 listener then starts [web_app_complete.py](../web_app_complete.py) with its configured venv).
- Broadcaster: run the VS Code task `broadcast-signals` (long-running process for [signal_broadcaster.py](../signal_broadcaster.py)).
- Many scripts call `chcp 65001` on Windows to avoid UTF-8 console issues; keep this pattern when adding CLI scripts.

### Output/encoding conventions
- When writing JSON meant for humans/UIs, the repo commonly uses `encoding='utf-8'` + `ensure_ascii=False` and stores artifacts under `signals/`, `analysis/`, `recommendations/`.
