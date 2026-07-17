import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_REGISTRY = PROJECT_ROOT / "multi_account_config.json"


def _load_json(path: Path):
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _resolve_path(base: Path, value: str, fallback: str) -> Path:
    raw = str(value or "").strip() or fallback
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = base / p
    return p


def _prompt(label: str, current: str = "", required: bool = False, secret: bool = False) -> str:
    suffix = ""
    if current:
        suffix = f" [{current}]"
    if secret and current:
        suffix = " [saved]"

    while True:
        value = input(f"{label}{suffix}: ").strip()
        if not value and current:
            return current
        if value:
            return value
        if not required:
            return ""
        print("This field is required.")


def _prompt_int(label: str, current: int = 0, required: bool = False) -> int:
    while True:
        raw = input(f"{label} [{current}]: ").strip()
        if not raw:
            return int(current)
        try:
            return int(raw)
        except ValueError:
            print("Please enter a valid integer.")
            if not required:
                continue


def _prompt_bool(label: str, current: bool) -> bool:
    default_text = "y" if current else "n"
    while True:
        raw = input(f"{label} [y/n, default {default_text}]: ").strip().lower()
        if not raw:
            return bool(current)
        if raw in ("y", "yes", "1", "true", "on"):
            return True
        if raw in ("n", "no", "0", "false", "off"):
            return False
        print("Please answer y or n.")


def _accounts_from_registry(registry_path: Path):
    payload = _load_json(registry_path) or {}
    out = []
    for item in (payload.get("accounts") or []):
        if not isinstance(item, dict):
            continue
        account_id = str(item.get("id") or "").strip()
        if not account_id:
            continue
        wallet_path = _resolve_path(PROJECT_ROOT, item.get("wallet"), f"accounts/{account_id}/wallet.json")
        out.append(
            {
                "id": account_id,
                "label": str(item.get("label") or account_id),
                "enabled": bool(item.get("enabled", True)),
                "wallet_path": wallet_path,
            }
        )
    return out


def setup_wallet(wallet_path: Path, account_label: str) -> None:
    payload = _load_json(wallet_path) or {}

    print("\n" + "=" * 70)
    print(f"Wallet setup: {account_label}")
    print(f"File: {wallet_path}")
    print("=" * 70)

    payload["enabled"] = _prompt_bool("Enabled", bool(payload.get("enabled", True)))
    payload["allow_trading"] = _prompt_bool("Allow trading", bool(payload.get("allow_trading", True)))
    payload["allow_site_signals"] = _prompt_bool("Allow site signals", bool(payload.get("allow_site_signals", True)))
    payload["auto_execution_enabled"] = _prompt_bool(
        "Auto execution enabled", bool(payload.get("auto_execution_enabled", True))
    )

    current_symbols = payload.get("auto_execution_symbols")
    if not isinstance(current_symbols, list) or not current_symbols:
        current_symbols = ["XAUUSD", "BTCUSD"]
    symbols_text = ",".join(str(x).strip().upper() for x in current_symbols if str(x).strip())
    raw_symbols = _prompt("Auto execution symbols (comma-separated)", symbols_text, required=True)
    payload["auto_execution_symbols"] = [
        s.strip().upper().replace("/", "")
        for s in raw_symbols.split(",")
        if s.strip()
    ]

    payload["login"] = _prompt_int("MT5 login", int(payload.get("login") or 0), required=True)
    payload["password"] = _prompt("MT5 password", str(payload.get("password") or ""), required=True, secret=True)
    payload["server"] = _prompt("MT5 server", str(payload.get("server") or ""), required=True)
    payload["path"] = _prompt("MT5 terminal path (terminal64.exe)", str(payload.get("path") or ""), required=True)
    payload["magic"] = _prompt_int("Magic number", int(payload.get("magic") or 88001), required=True)
    payload["deviation"] = _prompt_int("Deviation", int(payload.get("deviation") or 20), required=False)

    current_vol = str(payload.get("default_volume") or "0.01")
    raw_vol = _prompt("Default volume", current_vol, required=True)
    try:
        payload["default_volume"] = float(raw_vol)
    except ValueError:
        payload["default_volume"] = 0.01

    _save_json(wallet_path, payload)
    print(f"Saved: {wallet_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Interactive setup for multi-account MT5 wallet files")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY), help="Path to multi_account_config.json")
    parser.add_argument("--include-disabled", action="store_true", help="Also prompt for disabled accounts")
    args = parser.parse_args()

    registry_path = Path(args.registry)
    accounts = _accounts_from_registry(registry_path)
    if not accounts:
        print(f"No accounts found in: {registry_path}")
        return 1

    for acc in accounts:
        if not args.include_disabled and not acc["enabled"]:
            continue
        setup_wallet(wallet_path=acc["wallet_path"], account_label=f"{acc['id']} - {acc['label']}")

    print("\nAll wallet files updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())