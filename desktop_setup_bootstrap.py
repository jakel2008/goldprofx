import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


PACKAGE_ZIP_NAME = "GOLD_PRO_DESKTOP_TRADER_WINDOWS.zip"
APP_FOLDER_NAME = "GOLD_PRO_DESKTOP_TRADER_WINDOWS"
INSTALL_ROOT_NAME = "GOLD_PRO_Desktop_Trader"


def _resource_path(relative_path: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relative_path


def _default_install_dir() -> Path:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata) / INSTALL_ROOT_NAME
    return Path.home() / INSTALL_ROOT_NAME


def _ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _create_bat_shortcut(target_bat: Path, destination_bat: Path) -> None:
    destination_bat.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        f"cd /d \"{target_bat.parent}\"\r\n"
        f"call \"{target_bat}\"\r\n"
    )
    destination_bat.write_text(content, encoding="utf-8")


def _launch_app(start_bat_path: Path) -> None:
    subprocess.Popen(["cmd.exe", "/c", str(start_bat_path)], cwd=str(start_bat_path.parent))


def main() -> int:
    try:
        package_zip = _resource_path(f"payload/{PACKAGE_ZIP_NAME}")
        if not package_zip.exists():
            print(f"[ERROR] Missing embedded package: {package_zip}")
            return 1

        install_root = _default_install_dir()
        _ensure_clean_dir(install_root)

        with zipfile.ZipFile(package_zip, "r") as archive:
            archive.extractall(install_root)

        app_dir = install_root / APP_FOLDER_NAME
        start_bat = app_dir / "START_DESKTOP_APP.bat"
        if not start_bat.exists():
            print(f"[ERROR] START_DESKTOP_APP.bat not found: {start_bat}")
            return 1

        desktop_dir = Path.home() / "Desktop"
        desktop_launcher = desktop_dir / "GOLD PRO Desktop Trader.bat"
        _create_bat_shortcut(start_bat, desktop_launcher)

        start_menu_dir = Path(os.environ.get("APPDATA", str(Path.home()))) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        start_menu_launcher = start_menu_dir / "GOLD PRO Desktop Trader.bat"
        _create_bat_shortcut(start_bat, start_menu_launcher)

        print("[OK] Installation completed")
        print(f"[OK] App location: {app_dir}")
        print(f"[OK] Desktop launcher: {desktop_launcher}")
        print(f"[OK] Start menu launcher: {start_menu_launcher}")

        _launch_app(start_bat)
        return 0
    except Exception as exc:
        print(f"[ERROR] Setup failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
