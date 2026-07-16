import os
import sys
import json
import time
import re
import math
import platform as _platform
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


_IS_WINDOWS = _platform.system() == 'Windows'

try:
    import MetaTrader5 as mt5  # type: ignore
except Exception:
    mt5 = None  # type: ignore

_MT5_UNAVAILABLE_REASON = (
    None if mt5 is not None
    else ('MetaTrader5 يعمل على Windows فقط — هذا الخادم يعمل بنظام '
           + _platform.system() + '. شغّل المتداول الآلي محلياً على جهاز Windows.'
          ) if not _IS_WINDOWS
    else 'MetaTrader5 package is not installed.'
)


_RETCODE_ERRORS: Dict[int, str] = {
    10004: "Requote — أعد المحاولة",
    10006: "الطلب مرفوض من الوسيط",
    10007: "تم إلغاء الطلب من قِبل المتداول",
    10008: "تم تقديم الأمر",
    10009: "تم التنفيذ",
    10010: "تنفيذ جزئي",
    10011: "خطأ في معالجة الطلب",
    10012: "انتهت مهلة الطلب",
    10013: "طلب غير صالح",
    10014: "حجم غير صالح",
    10015: "سعر غير صالح",
    10016: "وقف خسارة/هدف غير صالح",
    10017: "التداول معطّل على هذا الرمز",
    10018: "التداول معطّل على هذا الرمز — قد يكون السوق مغلقًا أو الرمز غير متاح للتداول الآن",
    10019: "لا يوجد رصيد كافٍ",
    10020: "الأسعار تغيرت",
    10021: "لا توجد أسعار للتنفيذ",
    10022: "تاريخ انتهاء الأمر غير صالح",
    10023: "حالة الأمر تغيرت",
    10024: "طلبات كثيرة في نفس الوقت",
    10025: "لا توجد تغييرات في الطلب",
    10026: "التداول الآلي معطّل من جهة الوسيط",
    10027: "التداول الآلي معطّل من جهة العميل — فعّل AutoTrading في MT5",
    10028: "الطلب مقفل للمعالجة",
    10029: "الأمر أو المركز مجمّد",
    10030: "نوع التنفيذ غير مدعوم",
}


def _retcode_error(retcode: int) -> str:
    return _RETCODE_ERRORS.get(int(retcode), f"خطأ MT5 retcode={retcode}")


class MT5Bridge:
    def __init__(self) -> None:
        self.enabled = False
        self.allow_trading = False
        self.allow_site_signals = False
        self.auto_execution_enabled = False
        self.auto_execution_symbols: List[str] = []
        self.login = 0
        self.password = ""
        self.server = ""
        self.path = ""
        self.magic = 88001
        self.deviation = 20
        self.default_volume = 0.01
        self.connected = False
        self._config_path = os.environ.get("MT5_WALLET_CONFIG") or os.path.join(os.getcwd(), "mt5_wallet_config.json")
        self._symbol_names_cache: List[str] = []
        self._symbol_cache_at: float = 0.0
        self._normalized_symbol_map_cache: Dict[str, str] = {}
        self._normalized_cache_at: float = 0.0
        self._load_persisted_config()

    _SYMBOL_ALIASES: Dict[str, List[str]] = {
        "XAUUSD": ["XAUUSD", "GOLD"],
        "XAGUSD": ["XAGUSD", "SILVER"],
        "USOIL": ["USOIL", "WTI", "USWTI"],
        "UKOIL": ["UKOIL", "BRENT", "UKBRENT"],
        "NDX": ["NDX", "NAS100", "USTEC", "US100", "NASDAQ"],
        "NAS100": ["NAS100", "USTEC", "NASDAQ"],
        "RUT": ["RUT", "US2000", "RUS2000", "USTWO"],
        "US30": ["US30", "DJI", "DOW"],
        "SPX": ["SPX", "SPX500", "US500", "SP500"],
        "SPX500": ["SPX500", "US500", "SP500"],
        "NATGAS": ["NATGAS", "XNGUSD", "NGAS", "NATURALGAS"],
        "CRUDE": ["CRUDE", "USOIL", "WTI", "USWTI"],
        "BRENT": ["BRENT", "UKOIL", "UKBRENT"],
        "BTCUSD": ["BTCUSD", "BTCUSD."],
        "ETHUSD": ["ETHUSD", "ETHUSD."],
    }

    _COMMON_SUFFIXES: List[str] = ["m", ".m", "_m", "pro", ".pro", "i", ".i", ".a", "_ecn", "ecn"]
    _NORMALIZE_STRIP_SUFFIXES: List[str] = ["PRO", "ECN", "RAW", "MINI", "MICRO", "M", "I", "A"]

    def _normalize_symbol_key(self, value: str) -> str:
        return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())

    def _build_normalized_symbol_map(self, force_refresh: bool = False) -> Dict[str, str]:
        now = time.time()
        if not force_refresh and self._normalized_symbol_map_cache and (now - self._normalized_cache_at) < 60:
            return dict(self._normalized_symbol_map_cache)

        names = self._symbol_names(force_refresh=force_refresh)
        out: Dict[str, str] = {}

        def _set_if_better(key: str, symbol_name: str) -> None:
            if not key:
                return
            prev = out.get(key)
            if prev is None or len(symbol_name) < len(prev):
                out[key] = symbol_name

        for name in names:
            key = self._normalize_symbol_key(name)
            _set_if_better(key, name)
            for suffix in self._NORMALIZE_STRIP_SUFFIXES:
                if len(key) > len(suffix) + 2 and key.endswith(suffix):
                    _set_if_better(key[: -len(suffix)], name)

        self._normalized_symbol_map_cache = out
        self._normalized_cache_at = now
        return dict(out)

    def _discover_terminal_paths(self) -> List[str]:
        candidates = [
            r"C:\Program Files\MetaTrader 5\terminal64.exe",
            r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
            r"C:\Program Files\ATFXGM MT5 Terminal\terminal64.exe",
            r"C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe",
            r"C:\Program Files\GTC Global Trade MetaTrader 5\terminal64.exe",
            r"C:\Program Files\MT5 Weltrade\terminal64.exe",
        ]
        found: List[str] = []
        seen = set()
        for item in candidates:
            path = self._clean_text(item)
            if not path or path in seen:
                continue
            seen.add(path)
            if os.path.exists(path):
                found.append(path)
        return found

    def inspect_terminals(self) -> Dict[str, Any]:
        if mt5 is None:
            return {"success": False, "error": "MetaTrader5 package is not installed."}

        paths = self._discover_terminal_paths()
        checks: List[Dict[str, Any]] = []
        for path in paths:
            ok = False
            err = None
            try:
                try:
                    mt5.shutdown()
                except Exception:
                    pass
                ok = bool(mt5.initialize(path=path))
                if not ok:
                    err = mt5.last_error()
            except Exception as e:
                err = str(e)
            finally:
                try:
                    mt5.shutdown()
                except Exception:
                    pass

            checks.append({
                "path": path,
                "initialize_ok": bool(ok),
                "error": None if ok else str(err),
            })

        return {
            "success": True,
            "configured_path": self.path,
            "count": len(checks),
            "terminals": checks,
        }

    def _persist_config(self) -> None:
        payload = {
            "enabled": bool(self.enabled),
            "allow_trading": bool(self.allow_trading),
            "allow_site_signals": bool(self.allow_site_signals),
            "auto_execution_enabled": bool(self.auto_execution_enabled),
            "auto_execution_symbols": list(self.auto_execution_symbols or []),
            "login": int(self.login or 0),
            "password": str(self.password or ""),
            "server": str(self.server or ""),
            "path": str(self.path or ""),
            "magic": int(self.magic or 88001),
            "deviation": int(self.deviation or 20),
            "default_volume": float(self.default_volume or 0.01),
        }
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception:
            # Keep app running even if persistence fails.
            pass

    def _load_persisted_config(self) -> None:
        try:
            if not os.path.exists(self._config_path):
                return
            with open(self._config_path, "r", encoding="utf-8") as f:
                payload = json.load(f) or {}
            if isinstance(payload, dict):
                self.configure(payload)
        except Exception:
            pass

    def _clean_text(self, value: Any) -> str:
        text = str(value or "").strip()
        # Some clients send quoted paths like "C:\\...\\terminal64.exe".
        while len(text) >= 2 and ((text[0] == '"' and text[-1] == '"') or (text[0] == "'" and text[-1] == "'")):
            text = text[1:-1].strip()
        return text

    def configure(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = dict(payload or {})

        def _to_bool(value: Any, fallback: bool) -> bool:
            if value is None:
                return fallback
            if isinstance(value, bool):
                return value
            return str(value).strip().lower() in {"1", "true", "yes", "on"}

        def _to_int(value: Any, fallback: int) -> int:
            try:
                return int(str(value))
            except Exception:
                return fallback

        def _to_float(value: Any, fallback: float) -> float:
            try:
                return float(str(value))
            except Exception:
                return fallback

        self.enabled = _to_bool(data.get("enabled"), self.enabled)
        self.allow_trading = _to_bool(data.get("allow_trading"), self.allow_trading)
        self.allow_site_signals = _to_bool(data.get("allow_site_signals"), self.allow_site_signals)
        self.auto_execution_enabled = _to_bool(data.get("auto_execution_enabled"), self.auto_execution_enabled)

        symbols_raw = data.get("auto_execution_symbols")
        if symbols_raw is not None:
            if isinstance(symbols_raw, str):
                parts = [item.strip().upper() for item in symbols_raw.split(",") if str(item).strip()]
                self.auto_execution_symbols = parts
            elif isinstance(symbols_raw, list):
                parts = [str(item).strip().upper() for item in symbols_raw if str(item).strip()]
                self.auto_execution_symbols = parts

        if data.get("login") is not None and str(data.get("login")).strip() not in ("", "0", "0.0"):
            self.login = _to_int(data.get("login"), self.login)

        if data.get("password") is not None:
            cleaned_password = self._clean_text(data.get("password"))
            # Do not wipe existing saved password when UI submits empty field on refresh.
            if cleaned_password:
                self.password = cleaned_password

        if data.get("server") is not None:
            cleaned_server = self._clean_text(data.get("server"))
            # Do not wipe a valid server with an empty string.
            if cleaned_server:
                self.server = cleaned_server

        if data.get("path") is not None:
            self.path = self._clean_text(data.get("path"))

        if data.get("magic") is not None and str(data.get("magic")).strip() != "":
            self.magic = _to_int(data.get("magic"), self.magic)

        if data.get("deviation") is not None and str(data.get("deviation")).strip() != "":
            self.deviation = _to_int(data.get("deviation"), self.deviation)

        if data.get("default_volume") is not None and str(data.get("default_volume")).strip() != "":
            self.default_volume = _to_float(data.get("default_volume"), self.default_volume)

        # Any config update invalidates an old connection state until reconnect.
        self.connected = False
        self._persist_config()

        return {
            "success": True,
            "status": self.status(),
            "password_set": bool(self.password),
        }

    def _base_status(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "allow_trading": self.allow_trading,
            "allow_site_signals": self.allow_site_signals,
            "auto_execution_enabled": self.auto_execution_enabled,
            "auto_execution_symbols": list(self.auto_execution_symbols or []),
            "module_available": mt5 is not None,
            "platform": _platform.system(),
            "windows_only_note": None if _IS_WINDOWS else "MT5 يعمل على Windows فقط. شغّل continuous_auto_trader.py على جهاز Windows محلياً.",
            "connected": self.connected,
            "login": self.login,
            "server": self.server,
            "path": self.path,
            "magic": self.magic,
            "deviation": self.deviation,
            "default_volume": self.default_volume,
        }

    def connect(self, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if overrides:
            self.configure(overrides)

        # Re-sanitize in case values came from env or legacy state.
        self.path = self._clean_text(self.path)
        self.server = self._clean_text(self.server)
        self.password = self._clean_text(self.password)

        status = self._base_status()
        if not self.enabled:
            return {"success": False, "error": "MT5 is disabled. Set MT5_ENABLED=true.", "status": status}
        if mt5 is None:
            return {"success": False, "error": "MetaTrader5 package is not installed.", "status": status}

        has_credentials = bool(self.login and self.password and self.server)
        discovered = self._discover_terminal_paths()
        paths_to_try: List[str] = []

        def _add_path(value: str) -> None:
            p = self._clean_text(value)
            if p not in paths_to_try:
                paths_to_try.append(p)

        if self.path:
            _add_path(self.path)

            # If configured path belongs to another broker, try one sensible fallback automatically.
            if self.server and "EXNESS" in self.server.upper():
                preferred = next((p for p in discovered if "MetaTrader 5\\terminal64.exe" in p), "")
                if preferred:
                    _add_path(preferred)
            elif discovered:
                _add_path(discovered[0])
        else:
            if self.server and "EXNESS" in self.server.upper():
                discovered = sorted(discovered, key=lambda p: 0 if "MetaTrader 5\\terminal64.exe" in p else 1)
            if discovered:
                _add_path(discovered[0])
            else:
                _add_path("")

        # Keep connect responsive.
        paths_to_try = paths_to_try[:2]

        attempts: List[Dict[str, Any]] = []
        chosen_path = ""
        init_done = False

        for candidate_path in paths_to_try:
            try:
                mt5.shutdown()
            except Exception:
                pass

            base_kwargs: Dict[str, Any] = {}
            if candidate_path:
                base_kwargs["path"] = candidate_path

            # Single fast strategy: initialize by path, then explicit login.
            ok_init = mt5.initialize(**base_kwargs)
            if not ok_init:
                err_init = mt5.last_error()
                attempts.append({"path": candidate_path or "<default>", "strategy": "init_then_login", "ok": False, "error": str(err_init)})

                # Optional fallback only for default terminal and authorization-like failures.
                init_code = None
                try:
                    init_code = int(err_init[0]) if isinstance(err_init, tuple) and len(err_init) >= 1 else None
                except Exception:
                    init_code = None

                if (candidate_path == "") and has_credentials and init_code in {-6, -10005}:
                    kwargs_fallback = dict(base_kwargs)
                    kwargs_fallback["login"] = self.login
                    kwargs_fallback["password"] = self.password
                    kwargs_fallback["server"] = self.server
                    ok_fb = mt5.initialize(**kwargs_fallback)
                    if ok_fb:
                        chosen_path = candidate_path
                        init_done = True
                        attempts.append({"path": "<default>", "strategy": "init_with_credentials_fallback", "ok": True})
                        break
                    err_fb = mt5.last_error()
                    attempts.append({"path": "<default>", "strategy": "init_with_credentials_fallback", "ok": False, "error": str(err_fb)})
                elif has_credentials and init_code in {-6, -10005}:
                    kwargs_fallback = dict(base_kwargs)
                    kwargs_fallback["login"] = self.login
                    kwargs_fallback["password"] = self.password
                    kwargs_fallback["server"] = self.server
                    ok_fb = mt5.initialize(**kwargs_fallback)
                    if ok_fb:
                        chosen_path = candidate_path
                        init_done = True
                        attempts.append({"path": candidate_path or "<default>", "strategy": "init_with_credentials_fallback", "ok": True})
                        break
                    err_fb = mt5.last_error()
                    attempts.append({"path": candidate_path or "<default>", "strategy": "init_with_credentials_fallback", "ok": False, "error": str(err_fb)})

                continue

            attempts.append({"path": candidate_path or "<default>", "strategy": "initialize", "ok": True})

            if has_credentials:
                login_ok = mt5.login(login=self.login, password=self.password, server=self.server)
                if not login_ok:
                    err_login = mt5.last_error()
                    attempts.append({"path": candidate_path or "<default>", "strategy": "login", "ok": False, "error": f"login failed: {err_login}"})
                    try:
                        mt5.shutdown()
                    except Exception:
                        pass
                    continue

                attempts.append({"path": candidate_path or "<default>", "strategy": "login", "ok": True})

            chosen_path = candidate_path
            init_done = True
            break

        if not init_done:
            self.connected = False
            # Prefer the most actionable error from recorded attempts (can differ from last_error()).
            last_attempt_error = None
            if attempts:
                for item in reversed(attempts):
                    if item.get("error"):
                        last_attempt_error = str(item.get("error"))
                        break

            err = mt5.last_error()
            err_text = last_attempt_error or str(err)

            hint = "Connection failed. Verify terminal path and account credentials."
            low = err_text.lower()
            if "ipc timeout" in low or "-10005" in low:
                hint = "IPC timeout while talking to terminal. Open the selected MT5 terminal manually, wait until fully loaded/logged in, then retry connect."
            elif "authorization failed" in low or "-6" in low:
                if any(item.get("strategy") == "initialize" and item.get("ok") for item in attempts) and any(item.get("strategy") == "login" and not item.get("ok") for item in attempts):
                    hint = "Terminal initialized, but login was rejected. Verify the account number, password, and exact server name in MT5."
                else:
                    hint = "Authorization failed. Verify login/password/server and ensure this terminal belongs to the same broker account."
            elif "login failed" in low:
                hint = "Login failed after terminal initialization. Verify account credentials and server name exactly as shown in MT5."

            if self.server and "EXNESS" in self.server.upper() and self.path:
                up_path = self.path.upper()
                if any(tag in up_path for tag in ["ATFX", "FTMO", "WELTRADE", "GTC"]):
                    hint = "Configured terminal path appears to be another broker terminal. For Exness server, select Exness/MetaTrader terminal path and retry."

            return {
                "success": False,
                "error": err_text,
                "hint": hint,
                "attempts": attempts[-8:],
                "status": self._base_status(),
            }

        if chosen_path and self.path != chosen_path:
            self.path = chosen_path
            self._persist_config()

        self.connected = True
        return {"success": True, "status": self.status(), "used_path": chosen_path or "<default>", "attempts": attempts[-8:]}

    def shutdown(self) -> Dict[str, Any]:
        if mt5 is not None:
            try:
                mt5.shutdown()
            except Exception:
                pass
        self.connected = False
        return {"success": True, "status": self._base_status()}

    def _ensure_connection(self) -> Optional[Dict[str, Any]]:
        if mt5 is None:
            return {"success": False, "error": "MetaTrader5 package is not installed."}
        if not self.enabled:
            return {"success": False, "error": "MT5 is disabled. Set MT5_ENABLED=true."}
        if self.connected:
            return None
        result = self.connect()
        if not result.get("success"):
            return result
        return None

    def _normalize_side(self, side: str) -> str:
        value = str(side or "").strip().lower()
        if value in {"buy", "long"}:
            return "buy"
        if value in {"sell", "short"}:
            return "sell"
        return ""

    def _symbol_names(self, force_refresh: bool = False) -> List[str]:
        if mt5 is None:
            return []
        now = time.time()
        if not force_refresh and self._symbol_names_cache and (now - self._symbol_cache_at) < 60:
            return self._symbol_names_cache
        try:
            all_symbols = mt5.symbols_get()
            names = [str(item.name) for item in (all_symbols or []) if getattr(item, "name", None)]
            self._symbol_names_cache = names
            self._symbol_cache_at = now
            return names
        except Exception:
            return self._symbol_names_cache

    def _resolve_symbol_name(self, requested_symbol: str) -> Optional[str]:
        if mt5 is None:
            return None

        requested = str(requested_symbol or "").strip().upper()
        if not requested:
            return None

        names = self._symbol_names()
        if not names:
            return None

        name_set = set(names)
        lower_map = {name.lower(): name for name in names}

        def _is_tradable_symbol(symbol_name: str) -> bool:
            info = mt5.symbol_info(symbol_name)
            if info is None:
                return False
            # trade_mode: 0=DISABLED, 1=LONGONLY, 2=SHORTONLY, 3=CLOSEONLY, 4=FULL
            trade_mode = int(getattr(info, "trade_mode", 4) or 4)
            if trade_mode in {0, 3}:
                return False
            if not info.visible:
                return bool(mt5.symbol_select(symbol_name, True))
            return True

        def _try_candidates(candidates: List[str]) -> Optional[str]:
            seen = set()
            for cand in candidates:
                c = str(cand or "").strip()
                if not c:
                    continue
                uc = c.upper()
                if uc in seen:
                    continue
                seen.add(uc)

                exact = uc if uc in name_set else lower_map.get(c.lower())
                if exact and _is_tradable_symbol(exact):
                    return exact

                prefix_hits = [name for name in names if name.upper().startswith(uc)]
                for hit in prefix_hits:
                    if _is_tradable_symbol(hit):
                        return hit
            return None

        base_candidates = [requested]
        base_candidates.extend(self._SYMBOL_ALIASES.get(requested, []))

        with_suffix = []
        for base in list(base_candidates):
            with_suffix.append(base)
            for suffix in self._COMMON_SUFFIXES:
                with_suffix.append(f"{base}{suffix}")

        resolved = _try_candidates(with_suffix)
        if resolved:
            return resolved

        # Last attempt: contains search for known alias roots.
        roots = [item.upper() for item in self._SYMBOL_ALIASES.get(requested, [requested])]
        for root in roots:
            contains_hits = [name for name in names if root in name.upper()]
            for hit in contains_hits:
                if _is_tradable_symbol(hit):
                    return hit

        # Dynamic normalization against broker symbols (symbols_get).
        norm_map = self._build_normalized_symbol_map()
        normalized_candidates = [self._normalize_symbol_key(requested)]
        normalized_candidates.extend(self._normalize_symbol_key(item) for item in self._SYMBOL_ALIASES.get(requested, []))
        for key in normalized_candidates:
            hit = norm_map.get(key)
            if not hit:
                continue
            if _is_tradable_symbol(hit):
                return hit

        return None

    def normalize_symbol(self, symbol: str) -> Dict[str, Any]:
        req = str(symbol or "").strip().upper()
        if not req:
            return {"success": False, "error": "symbol is required"}

        connection_error = self._ensure_connection()
        if connection_error:
            return connection_error

        resolved = self._resolve_symbol_name(req)
        if not resolved:
            return {
                "success": False,
                "requested_symbol": req,
                "error": "symbol not available",
            }

        return {
            "success": True,
            "requested_symbol": req,
            "normalized_symbol": resolved,
            "changed": resolved.upper() != req.upper(),
        }

    def normalize_symbols(self, symbols: List[str]) -> Dict[str, Any]:
        connection_error = self._ensure_connection()
        if connection_error:
            return connection_error

        rows: List[Dict[str, Any]] = []
        for raw in (symbols or []):
            req = str(raw or "").strip().upper()
            if not req:
                continue
            rows.append(self.normalize_symbol(req))

        return {
            "success": True,
            "count": len(rows),
            "items": rows,
        }

    def _select_symbol(self, symbol: str) -> bool:
        if mt5 is None:
            return False
        info = mt5.symbol_info(symbol)
        if info is None:
            return False
        if info.visible:
            return True
        return bool(mt5.symbol_select(symbol, True))

    def _get_tick(self, symbol: str):
        if mt5 is None:
            return None
        return mt5.symbol_info_tick(symbol)

    def status(self) -> Dict[str, Any]:
        status = self._base_status()
        if mt5 is None:
            return status
        try:
            terminal_info = mt5.terminal_info()
            account_info = mt5.account_info()
            status.update(
                {
                    "terminal": terminal_info._asdict() if terminal_info else None,
                    "account": account_info._asdict() if account_info else None,
                    "last_error": mt5.last_error(),
                }
            )
        except Exception as e:
            status["error"] = str(e)
        return status

    def get_live_ticks(self, symbols: List[str]) -> Dict[str, Any]:
        connection_error = self._ensure_connection()
        if connection_error:
            return connection_error

        rows: List[Dict[str, Any]] = []
        errors: List[Dict[str, str]] = []

        for symbol in symbols[:120]:
            req_sym = str(symbol or "").strip().upper()
            if not req_sym:
                continue
            try:
                sym = self._resolve_symbol_name(req_sym)
                if not sym:
                    errors.append({"symbol": req_sym, "error": "symbol not found/visible"})
                    continue
                tick = self._get_tick(sym)
                if tick is None:
                    errors.append({"symbol": req_sym, "resolved_symbol": sym, "error": "tick unavailable"})
                    continue
                rows.append(
                    {
                        "symbol": sym,
                        "requested_symbol": req_sym,
                        "bid": float(tick.bid),
                        "ask": float(tick.ask),
                        "last": float(tick.last),
                        "volume": int(tick.volume),
                        "time": int(tick.time),
                        "time_msc": int(getattr(tick, "time_msc", 0) or 0),
                        "spread_points": float(tick.ask - tick.bid),
                    }
                )
            except Exception as e:
                errors.append({"symbol": req_sym, "error": str(e)})

        return {
            "success": True,
            "count": len(rows),
            "requested": len(symbols[:120]),
            "ticks": rows,
            "errors": errors,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def get_snapshot(self, symbols: List[str]) -> Dict[str, Any]:
        connection_error = self._ensure_connection()
        if connection_error:
            return connection_error

        if mt5 is None:
            return {"success": False, "error": "MetaTrader5 package is not installed."}

        ticks = self.get_live_ticks(symbols)
        positions = mt5.positions_get()
        orders = mt5.orders_get()
        account_info = mt5.account_info()

        return {
            "success": True,
            "account": account_info._asdict() if account_info else None,
            "positions": [p._asdict() for p in (positions or [])],
            "orders": [o._asdict() for o in (orders or [])],
            "ticks": ticks.get("ticks", []),
            "tick_errors": ticks.get("errors", []),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def get_rates(self, symbol: str, timeframe: str = "M1", count: int = 200) -> Dict[str, Any]:
        connection_error = self._ensure_connection()
        if connection_error:
            return connection_error

        if mt5 is None:
            return {"success": False, "error": "MetaTrader5 package is not installed."}

        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
        }
        tf = tf_map.get(str(timeframe or "M1").upper(), mt5.TIMEFRAME_M1)
        sym = str(symbol or "").strip().upper()
        if not sym:
            return {"success": False, "error": "symbol is required"}

        resolved_symbol = self._resolve_symbol_name(sym)
        if not resolved_symbol:
            return {"success": False, "error": f"symbol not available: {sym}"}

        bars = mt5.copy_rates_from_pos(resolved_symbol, tf, 0, max(1, min(int(count or 200), 2000)))
        if bars is None:
            return {"success": False, "error": f"rates unavailable: {mt5.last_error()}"}

        payload: List[Dict[str, Any]] = []
        for bar in bars:
            payload.append(
                {
                    "time": int(bar["time"]),
                    "open": float(bar["open"]),
                    "high": float(bar["high"]),
                    "low": float(bar["low"]),
                    "close": float(bar["close"]),
                    "tick_volume": int(bar["tick_volume"]),
                    "spread": int(bar["spread"]),
                    "real_volume": int(bar["real_volume"]),
                }
            )

        return {
            "success": True,
            "symbol": resolved_symbol,
            "requested_symbol": sym,
            "timeframe": str(timeframe).upper(),
            "count": len(payload),
            "bars": payload,
        }

    def send_order(
        self,
        symbol: str,
        side: str,
        volume: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: str = "GOLD_PRO",
        dry_run: bool = True,
        pending: bool = False,
        entry_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        connection_error = self._ensure_connection()
        if connection_error:
            return connection_error

        if mt5 is None:
            return {"success": False, "error": "MetaTrader5 package is not installed."}

        norm_side = self._normalize_side(side)
        if not norm_side:
            return {"success": False, "error": "side must be buy or sell"}

        sym = str(symbol or "").strip().upper()
        if not sym:
            return {"success": False, "error": "symbol is required"}

        resolved_symbol = self._resolve_symbol_name(sym)
        if not resolved_symbol:
            return {"success": False, "error": f"symbol not available: {sym}"}

        tick = self._get_tick(resolved_symbol)
        if tick is None:
            return {"success": False, "error": f"no tick for symbol: {sym}"}

        use_volume = float(volume or self.default_volume)
        info = mt5.symbol_info(resolved_symbol)
        if info is not None:
            # trade_mode: 0=DISABLED, 1=LONGONLY, 2=SHORTONLY, 3=CLOSEONLY, 4=FULL
            trade_mode = int(getattr(info, "trade_mode", 4) or 4)
            if trade_mode == 0:
                return {
                    "success": False,
                    "error": f"التداول معطّل على الرمز {resolved_symbol} من قِبَل الوسيط (trade_mode=DISABLED). جرّب رمزًا بديلًا أو تواصل مع الوسيط.",
                    "symbol": resolved_symbol,
                    "trade_mode": trade_mode,
                }
            if trade_mode == 3:
                return {
                    "success": False,
                    "error": f"الرمز {resolved_symbol} مسموح فقط بإغلاق الصفقات الحالية (CLOSEONLY). لا يمكن فتح صفقات جديدة.",
                    "symbol": resolved_symbol,
                    "trade_mode": trade_mode,
                }
            if trade_mode == 1 and norm_side == "sell":
                return {
                    "success": False,
                    "error": f"الرمز {resolved_symbol} لا يسمح إلا بصفقات الشراء (LONGONLY).",
                    "symbol": resolved_symbol,
                    "trade_mode": trade_mode,
                }
            if trade_mode == 2 and norm_side == "buy":
                return {
                    "success": False,
                    "error": f"الرمز {resolved_symbol} لا يسمح إلا بصفقات البيع (SHORTONLY).",
                    "symbol": resolved_symbol,
                    "trade_mode": trade_mode,
                }

            vol_min = float(getattr(info, "volume_min", 0.0) or 0.0)
            vol_step = float(getattr(info, "volume_step", 0.0) or 0.0)
            vol_max = float(getattr(info, "volume_max", 0.0) or 0.0)
            requested_volume = use_volume
            if vol_min > 0 and use_volume < vol_min:
                use_volume = vol_min
            if vol_step > 0:
                base_volume = vol_min if vol_min > 0 else 0.0
                if use_volume <= base_volume:
                    use_volume = base_volume if base_volume > 0 else vol_step
                else:
                    step_count = math.ceil(((use_volume - base_volume) / vol_step) - 1e-12)
                    use_volume = base_volume + (step_count * vol_step)
                use_volume = round(use_volume, 8)
            if vol_min > 0 and use_volume < vol_min:
                return {
                    "success": False,
                    "error": f"volume below minimum ({use_volume} < {vol_min})",
                    "symbol": resolved_symbol,
                    "requested_volume": requested_volume,
                    "volume_min": vol_min,
                    "volume_step": vol_step,
                    "volume_max": vol_max,
                }
            if vol_max > 0 and use_volume > vol_max:
                use_volume = vol_max

        price = float(tick.ask if norm_side == "buy" else tick.bid)
        order_type = mt5.ORDER_TYPE_BUY if norm_side == "buy" else mt5.ORDER_TYPE_SELL

        if pending:
            if entry_price is None:
                return {"success": False, "error": "entry_price is required for pending orders"}
            pending_price = float(entry_price)
            if norm_side == "buy":
                order_type = mt5.ORDER_TYPE_BUY_LIMIT if pending_price <= float(tick.ask) else mt5.ORDER_TYPE_BUY_STOP
            else:
                order_type = mt5.ORDER_TYPE_SELL_LIMIT if pending_price >= float(tick.bid) else mt5.ORDER_TYPE_SELL_STOP
            price = pending_price

        order_type_name = {
            getattr(mt5, "ORDER_TYPE_BUY", None): "BUY",
            getattr(mt5, "ORDER_TYPE_SELL", None): "SELL",
            getattr(mt5, "ORDER_TYPE_BUY_LIMIT", None): "BUY_LIMIT",
            getattr(mt5, "ORDER_TYPE_SELL_LIMIT", None): "SELL_LIMIT",
            getattr(mt5, "ORDER_TYPE_BUY_STOP", None): "BUY_STOP",
            getattr(mt5, "ORDER_TYPE_SELL_STOP", None): "SELL_STOP",
            getattr(mt5, "ORDER_TYPE_BUY_STOP_LIMIT", None): "BUY_STOP_LIMIT",
            getattr(mt5, "ORDER_TYPE_SELL_STOP_LIMIT", None): "SELL_STOP_LIMIT",
        }.get(order_type, str(order_type))

        metadata = {
            "execution_mode": "pending" if pending else "market",
            "order_type_name": order_type_name,
            "requested_symbol": sym,
            "resolved_symbol": resolved_symbol,
            "side": norm_side,
            "entry_price": price,
            "current_bid": float(tick.bid),
            "current_ask": float(tick.ask),
            "volume": use_volume,
            "stop_loss": float(sl) if sl is not None else None,
            "take_profit": float(tp) if tp is not None else None,
        }

        request = {
            "action": mt5.TRADE_ACTION_PENDING if pending else mt5.TRADE_ACTION_DEAL,
            "symbol": resolved_symbol,
            "volume": use_volume,
            "type": order_type,
            "price": price,
            "deviation": self.deviation,
            "magic": self.magic,
            "comment": str(comment or "GOLD_PRO")[:32],
            "type_time": mt5.ORDER_TIME_GTC,
        }

        if not pending:
            request["type_filling"] = mt5.ORDER_FILLING_IOC

        if sl is not None:
            request["sl"] = float(sl)
        if tp is not None:
            request["tp"] = float(tp)

        if dry_run:
            return {"success": True, "dry_run": True, "request": request, "metadata": metadata}

        if not self.allow_trading:
            return {
                "success": False,
                "error": "Trading blocked. Set MT5_ALLOW_TRADING=true or use dry_run=true.",
                "request": request,
                "metadata": metadata,
            }

        done_codes = {getattr(mt5, "TRADE_RETCODE_DONE", None), getattr(mt5, "TRADE_RETCODE_PLACED", None)}
        retryable_codes = {
            getattr(mt5, "TRADE_RETCODE_REQUOTE", None),
            getattr(mt5, "TRADE_RETCODE_REJECT", None),
            getattr(mt5, "TRADE_RETCODE_PRICE_CHANGED", None),
            getattr(mt5, "TRADE_RETCODE_PRICE_OFF", None),
            getattr(mt5, "TRADE_RETCODE_INVALID_PRICE", None),
            getattr(mt5, "TRADE_RETCODE_INVALID_FILL", None),
            10004,
            10006,
            10015,
            10020,
            10021,
            10030,
        }
        retryable_codes = {int(code) for code in retryable_codes if code is not None}

        attempts = []

        if pending:
            attempts.append(dict(request))
        else:
            fill_candidates = []
            for fill_name in ["ORDER_FILLING_IOC", "ORDER_FILLING_FOK", "ORDER_FILLING_RETURN"]:
                fill_value = getattr(mt5, fill_name, None)
                if fill_value is None or fill_value in fill_candidates:
                    continue
                fill_candidates.append(fill_value)
            if not fill_candidates:
                fill_candidates = [None]

            deviation_candidates = [int(self.deviation), max(int(self.deviation) * 2, 30), max(int(self.deviation) * 3, 50)]
            seen_deviation = set()
            compact_deviations = []
            for one in deviation_candidates:
                if one not in seen_deviation:
                    seen_deviation.add(one)
                    compact_deviations.append(one)

            for dev in compact_deviations:
                for fill in fill_candidates:
                    req = dict(request)
                    req["deviation"] = int(dev)
                    if fill is not None:
                        req["type_filling"] = fill
                    attempts.append(req)

        last_result = None
        last_error = None
        attempt_log = []

        for idx, one_request in enumerate(attempts):
            current_request = dict(one_request)
            if not pending:
                latest_tick = self._get_tick(resolved_symbol)
                if latest_tick is not None:
                    current_request["price"] = float(latest_tick.ask if norm_side == "buy" else latest_tick.bid)

            result = mt5.order_send(current_request)
            if result is None:
                last_error = f"order_send failed: {mt5.last_error()}"
                attempt_log.append(
                    {
                        "attempt": idx + 1,
                        "retcode": None,
                        "error": last_error,
                        "deviation": int(current_request.get("deviation", self.deviation)),
                        "type_filling": current_request.get("type_filling"),
                    }
                )
                continue

            last_result = result
            retcode = int(result.retcode)
            attempt_log.append(
                {
                    "attempt": idx + 1,
                    "retcode": retcode,
                    "error": None if retcode in done_codes else _retcode_error(retcode),
                    "deviation": int(current_request.get("deviation", self.deviation)),
                    "type_filling": current_request.get("type_filling"),
                }
            )

            if retcode in done_codes:
                return {
                    "success": True,
                    "retcode": retcode,
                    "result": result._asdict(),
                    "request": current_request,
                    "metadata": metadata,
                    "attempts": attempt_log,
                }

            if retcode not in retryable_codes:
                break

        if last_result is None:
            return {
                "success": False,
                "error": last_error or "order_send failed",
                "request": request,
                "metadata": metadata,
                "attempts": attempt_log,
            }

        failed_retcode = int(last_result.retcode)
        return {
            "success": False,
            "retcode": failed_retcode,
            "result": last_result._asdict(),
            "request": request,
            "metadata": metadata,
            "attempts": attempt_log,
            "error": _retcode_error(failed_retcode),
        }

    def get_pending_order(self, ticket: int) -> Dict[str, Any]:
        connection_error = self._ensure_connection()
        if connection_error:
            return connection_error

        if mt5 is None:
            return {"success": False, "error": "MetaTrader5 package is not installed."}

        tk = int(ticket or 0)
        if tk <= 0:
            return {"success": False, "error": "ticket is required"}

        rows = mt5.orders_get(ticket=tk)
        if not rows:
            return {"success": True, "exists": False, "ticket": tk}

        order = rows[0]
        return {"success": True, "exists": True, "ticket": tk, "order": order._asdict()}

    def cancel_pending_order(self, ticket: int, dry_run: bool = False) -> Dict[str, Any]:
        connection_error = self._ensure_connection()
        if connection_error:
            return connection_error

        if mt5 is None:
            return {"success": False, "error": "MetaTrader5 package is not installed."}

        tk = int(ticket or 0)
        if tk <= 0:
            return {"success": False, "error": "ticket is required"}

        current = mt5.orders_get(ticket=tk)
        if not current:
            return {"success": True, "ticket": tk, "already_closed": True}

        order = current[0]
        request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": tk,
            "symbol": str(getattr(order, "symbol", "") or ""),
            "magic": self.magic,
            "comment": "GOLD_PRO_CANCEL",
        }

        if dry_run:
            return {"success": True, "dry_run": True, "request": request}

        if not self.allow_trading:
            return {
                "success": False,
                "error": "Trading blocked. Set MT5_ALLOW_TRADING=true or use dry_run=true.",
                "request": request,
            }

        result = mt5.order_send(request)
        if result is None:
            return {"success": False, "error": f"order_remove failed: {mt5.last_error()}", "request": request}

        result_payload = result._asdict()
        done_codes = {getattr(mt5, "TRADE_RETCODE_DONE", None), getattr(mt5, "TRADE_RETCODE_PLACED", None)}
        success = result.retcode in done_codes
        out = {
            "success": success,
            "ticket": tk,
            "retcode": int(result.retcode),
            "result": result_payload,
            "request": request,
        }
        if not success:
            out["error"] = _retcode_error(result.retcode)
        return out

    def has_open_positions(self, symbol: str = "", magic: Optional[int] = None) -> Dict[str, Any]:
        connection_error = self._ensure_connection()
        if connection_error:
            return connection_error

        if mt5 is None:
            return {"success": False, "error": "MetaTrader5 package is not installed."}

        resolved_symbol = ""
        if symbol:
            resolved_symbol = self._resolve_symbol_name(str(symbol).strip().upper()) or ""

        rows = mt5.positions_get(symbol=resolved_symbol) if resolved_symbol else mt5.positions_get()
        rows = list(rows or [])

        use_magic = int(magic) if magic is not None else None
        if use_magic is not None:
            rows = [row for row in rows if int(getattr(row, "magic", 0) or 0) == use_magic]

        return {
            "success": True,
            "count": len(rows),
            "has_open": len(rows) > 0,
            "symbol": resolved_symbol or str(symbol or "").upper(),
            "magic": use_magic,
            "positions": [row._asdict() for row in rows],
        }

    def modify_position_sl_tp(
        self,
        ticket: int,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        connection_error = self._ensure_connection()
        if connection_error:
            return connection_error

        if mt5 is None:
            return {"success": False, "error": "MetaTrader5 package is not installed."}

        tk = int(ticket or 0)
        if tk <= 0:
            return {"success": False, "error": "ticket is required"}

        rows = mt5.positions_get(ticket=tk)
        if not rows:
            return {"success": False, "error": "position not found", "ticket": tk}

        position = rows[0]
        current_sl = float(getattr(position, "sl", 0.0) or 0.0)
        current_tp = float(getattr(position, "tp", 0.0) or 0.0)

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": tk,
            "symbol": str(getattr(position, "symbol", "") or ""),
            "sl": float(sl) if sl is not None else current_sl,
            "tp": float(tp) if tp is not None else current_tp,
            "magic": self.magic,
            "comment": "GOLD_PRO_SLTP",
        }

        if dry_run:
            return {"success": True, "dry_run": True, "request": request}

        if not self.allow_trading:
            return {
                "success": False,
                "error": "Trading blocked. Set MT5_ALLOW_TRADING=true or use dry_run=true.",
                "request": request,
            }

        result = mt5.order_send(request)
        if result is None:
            return {"success": False, "error": f"order_send failed: {mt5.last_error()}", "request": request}

        result_payload = result._asdict()
        done_codes = {getattr(mt5, "TRADE_RETCODE_DONE", None), getattr(mt5, "TRADE_RETCODE_PLACED", None)}
        success = result.retcode in done_codes
        out = {
            "success": success,
            "ticket": tk,
            "retcode": int(result.retcode),
            "result": result_payload,
            "request": request,
        }
        if not success:
            out["error"] = _retcode_error(result.retcode)
        return out

    def get_symbol_volume_rules(self, symbol: str) -> Dict[str, Any]:
        connection_error = self._ensure_connection()
        if connection_error:
            return connection_error

        if mt5 is None:
            return {"success": False, "error": "MetaTrader5 package is not installed."}

        req = str(symbol or "").strip().upper()
        if not req:
            return {"success": False, "error": "symbol is required"}

        resolved = self._resolve_symbol_name(req)
        if not resolved:
            return {"success": False, "error": f"symbol not available: {req}"}

        info = mt5.symbol_info(resolved)
        if info is None:
            return {"success": False, "error": f"symbol_info unavailable: {resolved}"}

        return {
            "success": True,
            "requested_symbol": req,
            "symbol": resolved,
            "volume_min": float(getattr(info, "volume_min", 0.0) or 0.0),
            "volume_step": float(getattr(info, "volume_step", 0.0) or 0.0),
            "volume_max": float(getattr(info, "volume_max", 0.0) or 0.0),
        }

    def execute_signal(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        symbol = str(payload.get("symbol") or payload.get("pair") or "").strip().upper()
        side = str(payload.get("signal_type") or payload.get("trade_type") or payload.get("signal") or "").strip().lower()
        entry_price = payload.get("entry_price") if payload.get("entry_price") is not None else payload.get("entry")
        sl = payload.get("stop_loss") if payload.get("stop_loss") is not None else payload.get("sl")

        tp1 = payload.get("take_profit_1") if payload.get("take_profit_1") is not None else payload.get("tp1")
        tp2 = payload.get("take_profit_2") if payload.get("take_profit_2") is not None else payload.get("tp2")
        tp3 = payload.get("take_profit_3") if payload.get("take_profit_3") is not None else payload.get("tp3")

        dry_run = bool(payload.get("dry_run", True))
        split_tp = bool(payload.get("split_tp", True))
        pending_entry = bool(payload.get("pending_entry", False))
        total_volume = float(payload.get("volume") or self.default_volume)

        if not symbol:
            return {"success": False, "error": "symbol/pair is required"}

        if split_tp:
            targets = [tp for tp in [tp1, tp2, tp3] if tp is not None]
            if not targets:
                targets = [None]

            # Split one trade volume across targets; do not multiply risk by repeating full volume.
            weights = [0.5, 0.3, 0.2]
            if len(targets) == 1:
                weights = [1.0]
            elif len(targets) == 2:
                weights = [0.6, 0.4]
            volumes = [round(max(total_volume * weights[idx], 0.0), 4) for idx in range(len(targets))]

            orders = []
            for idx, tp in enumerate(targets):
                volume = volumes[idx]
                if volume <= 0:
                    continue
                one = self.send_order(
                    symbol=symbol,
                    side=side,
                    volume=volume,
                    sl=float(sl) if sl is not None else None,
                    tp=float(tp) if tp is not None else None,
                    comment=f"GOLD_PRO_TP{idx+1}",
                    dry_run=dry_run,
                    pending=pending_entry,
                    entry_price=float(entry_price) if entry_price is not None else None,
                )
                orders.append(one)

            return {
                "success": all(bool(item.get("success")) for item in orders) if orders else False,
                "dry_run": dry_run,
                "orders": orders,
            }

        return self.send_order(
            symbol=symbol,
            side=side,
            volume=total_volume,
            sl=float(sl) if sl is not None else None,
            tp=float(tp1) if tp1 is not None else None,
            dry_run=dry_run,
            comment="GOLD_PRO_SIGNAL",
            pending=pending_entry,
            entry_price=float(entry_price) if entry_price is not None else None,
        )

    def history(self, hours: int = 24) -> Dict[str, Any]:
        connection_error = self._ensure_connection()
        if connection_error:
            return connection_error

        if mt5 is None:
            return {"success": False, "error": "MetaTrader5 package is not installed."}

        to_time = datetime.now()
        from_time = to_time - timedelta(hours=max(1, min(int(hours or 24), 24 * 30)))

        deals = mt5.history_deals_get(from_time, to_time)
        orders = mt5.history_orders_get(from_time, to_time)

        return {
            "success": True,
            "from": from_time.strftime("%Y-%m-%d %H:%M:%S"),
            "to": to_time.strftime("%Y-%m-%d %H:%M:%S"),
            "deals": [d._asdict() for d in (deals or [])],
            "orders": [o._asdict() for o in (orders or [])],
            "deals_count": len(deals or []),
            "orders_count": len(orders or []),
        }

    def search_symbols(self, query: str = "", limit: int = 100) -> Dict[str, Any]:
        connection_error = self._ensure_connection()
        if connection_error:
            return connection_error

        if mt5 is None:
            return {"success": False, "error": "MetaTrader5 package is not installed."}

        q = str(query or "").strip().upper()
        max_items = max(1, min(int(limit or 100), 1000))
        symbols = mt5.symbols_get()
        rows: List[Dict[str, Any]] = []

        for item in (symbols or []):
            name = str(getattr(item, "name", "") or "")
            if not name:
                continue
            if q and q not in name.upper():
                continue
            rows.append(
                {
                    "name": name,
                    "visible": bool(getattr(item, "visible", False)),
                    "path": str(getattr(item, "path", "") or ""),
                    "description": str(getattr(item, "description", "") or ""),
                }
            )
            if len(rows) >= max_items:
                break

        return {
            "success": True,
            "query": q,
            "count": len(rows),
            "symbols": rows,
        }


mt5_bridge = MT5Bridge()
