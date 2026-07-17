import argparse
import json
import os
import subprocess
import shutil
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DIST_DIR = PROJECT_ROOT / "dist"
PACKAGE_NAME = "GOLD_PRO_DESKTOP_TRADER_WINDOWS"
BUILD_DIR = DIST_DIR / PACKAGE_NAME
ZIP_PATH = DIST_DIR / f"{PACKAGE_NAME}.zip"
SETUP_EXE_NAME = "GOLD_PRO_DESKTOP_TRADER_SETUP"
SETUP_EXE_PATH = DIST_DIR / f"{SETUP_EXE_NAME}.exe"
PYINSTALLER_GUI_DIST = DIST_DIR / "multi_account_trader_gui"
PYINSTALLER_TRADER_DIST = DIST_DIR / "continuous_auto_trader"
PYINSTALLER_SETUP_DIST = DIST_DIR / SETUP_EXE_NAME

SOURCE_FILES = [
    "multi_account_config.json",
    "requirements_desktop_windows.txt",
    "START_MULTI_ACCOUNT_GUI.bat",
    "START_MULTI_ACCOUNT_TRADER.bat",
    "start_account2_tp3_trader.ps1",
    "install_account2_tp3_autostart.ps1",
    "PORTABLE_MULTI_ACCOUNT_TRADER_README.md",
]

EXTRA_SOURCE_FILES = [
    "run_multi_account_traders.py",
    "continuous_auto_trader.py",
    "mt5_bridge.py",
    "forex_analyzer.py",
    "multi_account_trader_gui.py",
]

STRATEGY_TEMPLATE_FILES = [
    "accounts/xauusd_tp3_focus_template.json",
    "accounts/scalping_gold_aggressive_template.json",
]

REPORT_FILES = [
    "reports/wallet_262972266_strategy_review.md",
    "reports/wallet_262972266_strategy_review_trades.csv",
    "reports/wallet_262972266_tp3_execution_plan.md",
    "reports/xauusd_tp3_focus_all_wallets_apply_report.md",
    "reports/auto_risk_sizing_apply_report.md",
]

APP_SOURCE_DIRS = [
    "my-forex-app/services",
]


def copy_file(relative_path: str) -> None:
    source_path = PROJECT_ROOT / relative_path
    if not source_path.exists():
        return
    target_path = BUILD_DIR / relative_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)


def ensure_pyinstaller() -> None:
    """Install PyInstaller in the current interpreter if it is missing."""
    try:
        __import__("PyInstaller")
        return
    except Exception:
        pass

    subprocess.run(
        [
            os.sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pyinstaller",
        ],
        cwd=str(PROJECT_ROOT),
        check=True,
    )


def run_pyinstaller_builds() -> None:
    """Build GUI and trader executables as portable onedir bundles."""
    ensure_pyinstaller()

    gui_cmd = [
        os.sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--name",
        "multi_account_trader_gui",
        str(PROJECT_ROOT / "multi_account_trader_gui.py"),
    ]
    subprocess.run(gui_cmd, cwd=str(PROJECT_ROOT), check=True)

    trader_cmd = [
        os.sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--name",
        "continuous_auto_trader",
        "--paths",
        str(PROJECT_ROOT / "my-forex-app"),
        "--hidden-import",
        "services",
        "--hidden-import",
        "services.advanced_analyzer_engine",
        str(PROJECT_ROOT / "continuous_auto_trader.py"),
    ]
    subprocess.run(trader_cmd, cwd=str(PROJECT_ROOT), check=True)


def merge_tree(source_dir: Path, target_dir: Path) -> None:
    """Copy all files from source tree into target tree, preserving relative structure."""
    if not source_dir.exists():
        return
    for src in source_dir.rglob("*"):
        if src.is_dir():
            continue
        if "__pycache__" in src.parts or src.suffix.lower() in {".pyc", ".pyo"}:
            continue
        rel = src.relative_to(source_dir)
        dst = target_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def copy_source_tree(relative_dir: str) -> None:
    source_dir = PROJECT_ROOT / relative_dir
    target_dir = BUILD_DIR / relative_dir
    merge_tree(source_dir, target_dir)


def copy_pyinstaller_outputs() -> None:
    """Bring built exe runtimes into the final package folder."""
    if not PYINSTALLER_GUI_DIST.exists() or not (PYINSTALLER_GUI_DIST / "multi_account_trader_gui.exe").exists():
        raise FileNotFoundError(f"GUI executable is missing: {PYINSTALLER_GUI_DIST}")
    if not PYINSTALLER_TRADER_DIST.exists() or not (PYINSTALLER_TRADER_DIST / "continuous_auto_trader.exe").exists():
        raise FileNotFoundError(f"Trader executable is missing: {PYINSTALLER_TRADER_DIST}")

    merge_tree(PYINSTALLER_GUI_DIST, BUILD_DIR)
    merge_tree(PYINSTALLER_TRADER_DIST, BUILD_DIR)


def load_json_file(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig") or "{}")
    except Exception:
        return {}


def write_json_file(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def copy_accounts(include_wallet_secrets: bool) -> None:
    accounts_dir = PROJECT_ROOT / "accounts"
    if not accounts_dir.exists():
        return

    for account_dir in sorted(item for item in accounts_dir.iterdir() if item.is_dir()):
        target_account_dir = BUILD_DIR / "accounts" / account_dir.name
        target_account_dir.mkdir(parents=True, exist_ok=True)

        for filename in ("config.json", "runtime_state.json"):
            source_path = account_dir / filename
            if source_path.exists():
                shutil.copy2(source_path, target_account_dir / filename)

        wallet_path = account_dir / "wallet.json"
        if wallet_path.exists():
            wallet_payload = load_json_file(wallet_path)
            if not include_wallet_secrets:
                wallet_payload["password"] = ""
            write_json_file(target_account_dir / "wallet.json", wallet_payload)


def write_launcher_files() -> None:
    (BUILD_DIR / "START_DESKTOP_APP.bat").write_text(
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        "cd /d %~dp0\r\n"
        "if not exist \"multi_account_trader_gui.exe\" (\r\n"
        "  echo [ERROR] multi_account_trader_gui.exe not found\r\n"
        "  pause\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        "start \"\" \"%~dp0multi_account_trader_gui.exe\"\r\n"
        "exit /b 0\r\n",
        encoding="utf-8",
    )
    (BUILD_DIR / "START_DESKTOP_APP_FROM_SOURCE.bat").write_text(
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        "cd /d %~dp0\r\n"
        "set \"PY=.venv\\Scripts\\python.exe\"\r\n"
        "if not exist \"%PY%\" set \"PY=%LOCALAPPDATA%\\Programs\\Python\\Python313\\python.exe\"\r\n"
        "if not exist \"%PY%\" set \"PY=python\"\r\n"
        "\"%PY%\" multi_account_trader_gui.py\r\n"
        "pause\r\n",
        encoding="utf-8",
    )
    (BUILD_DIR / "START_MULTI_ACCOUNT_TRADER_FROM_SOURCE.bat").write_text(
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        "cd /d %~dp0\r\n"
        "set \"PY=.venv\\Scripts\\python.exe\"\r\n"
        "if not exist \"%PY%\" set \"PY=%LOCALAPPDATA%\\Programs\\Python\\Python313\\python.exe\"\r\n"
        "if not exist \"%PY%\" set \"PY=python\"\r\n"
        "\"%PY%\" run_multi_account_traders.py --registry multi_account_config.json\r\n"
        "pause\r\n",
        encoding="utf-8",
    )
    (BUILD_DIR / "SETUP_PYTHON_ENV.bat").write_text(
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        "cd /d %~dp0\r\n"
        "set \"PY=%LOCALAPPDATA%\\Programs\\Python\\Python313\\python.exe\"\r\n"
        "if not exist \"%PY%\" set \"PY=python\"\r\n"
        "\"%PY%\" -m venv .venv\r\n"
        "if errorlevel 1 pause & exit /b 1\r\n"
        "\".venv\\Scripts\\python.exe\" -m pip install --upgrade pip\r\n"
        "\".venv\\Scripts\\python.exe\" -m pip install -r requirements_desktop_windows.txt\r\n"
        "pause\r\n",
        encoding="utf-8",
    )
    (BUILD_DIR / "START_TRADER_ENGINE_ONLY.bat").write_text(
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        "cd /d %~dp0\r\n"
        "if not exist \"continuous_auto_trader.exe\" (\r\n"
        "  echo [ERROR] continuous_auto_trader.exe not found\r\n"
        "  pause\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        "echo Use desktop app to manage account configs, then run this only if needed.\r\n"
        "pause\r\n",
        encoding="utf-8",
    )
    (BUILD_DIR / "README_DESKTOP_AR.txt").write_text(
        "GOLD PRO Desktop Trader - Windows\n"
        "================================\n\n"
        "طريقة التشغيل:\n"
        "1) فك الضغط في أي مجلد على Windows.\n"
        "2) إذا كانت الحزمة تحتوي exe شغل START_DESKTOP_APP.bat.\n"
        "3) إذا لم تعمل نسخة exe شغل SETUP_PYTHON_ENV.bat مرة واحدة ثم START_DESKTOP_APP_FROM_SOURCE.bat.\n"
        "4) افتح كل محفظة، أدخل بيانات MT5 ومسار terminal64.exe، ثم اختر Preset التداول واحفظ.\n"
        "5) استخدم اختبار الاتصال قبل بدء التداول.\n\n"
        "ماذا تتضمن الحزمة:\n"
        "- التطبيق التنفيذي multi_account_trader_gui.exe\n"
        "- محرك التداول التنفيذي continuous_auto_trader.exe\n"
        "- مكتبات بايثون المطلوبة مضمّنة داخل الحزمة\n"
        "- إعدادات المحافظ من مجلد accounts/ + ملف multi_account_config.json\n\n"
        "- قالب الاستراتيجية XAUUSD TP3 Focus وتقارير المراجعة في reports/\n\n"
        "خيارات التداول الموجودة داخل التطبيق:\n"
        "- XAUUSD TP3 Focus (Best Report): أفضل استراتيجية مراجعة، TP3 فقط وحساب مخاطرة تلقائي حسب Equity.\n"
        "- Gold Aggressive v3 (XAUUSD)\n"
        "- ذهب محافظ: صفقة واحدة، دخول 3m/5m، توافق 15m، وزخم RSI مطلوب.\n"
        "- ذهب متوازن مباشر: تنفيذ سوق مباشر مع فلترة متوسطة.\n"
        "- ذهب هجومي مباشر: الفريمات القصيرة وتخفيف توافق السياق.\n"
        "- ذهب بأوامر معلقة: Pending entry مع منع التكرار.\n"
        "- مراقبة فقط: Dry Run بدون تنفيذ أوامر حقيقية.\n\n"
        "ملاحظات مهمة:\n"
        "- لتشغيل أكثر من محفظة في نفس الوقت، يجب أن يكون لكل محفظة Terminal MT5 منفصل.\n"
        "- كلمات مرور المحافظ لا توضع في الحزمة افتراضياً. أدخلها من التطبيق ثم احفظ.\n"
        "- إذا أردت تضمين كلمات المرور محلياً فقط، ابنِ الحزمة بالوسيط --include-wallet-secrets.\n",
        encoding="utf-8",
    )


def build_zip() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source_path in BUILD_DIR.rglob("*"):
            if source_path.is_file():
                archive.write(source_path, source_path.relative_to(DIST_DIR))


def build_setup_exe() -> Path:
    """Build a single Windows setup EXE that embeds the prepared ZIP package."""
    ensure_pyinstaller()
    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"Package ZIP is missing: {ZIP_PATH}")

    if SETUP_EXE_PATH.exists():
        SETUP_EXE_PATH.unlink()

    setup_cmd = [
        os.sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        SETUP_EXE_NAME,
        "--add-data",
        f"{ZIP_PATH};payload",
        str(PROJECT_ROOT / "desktop_setup_bootstrap.py"),
    ]
    subprocess.run(setup_cmd, cwd=str(PROJECT_ROOT), check=True)

    built_exe = PYINSTALLER_SETUP_DIST.with_suffix(".exe")
    if not built_exe.exists():
        raise FileNotFoundError(f"Setup executable was not produced: {built_exe}")
    return built_exe


def build_package(include_wallet_secrets: bool, build_portable_exe: bool, build_setup_installer: bool) -> dict:
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    if build_portable_exe:
        run_pyinstaller_builds()
        copy_pyinstaller_outputs()

    for relative_path in SOURCE_FILES:
        copy_file(relative_path)
    for relative_path in EXTRA_SOURCE_FILES:
        copy_file(relative_path)
    for relative_path in STRATEGY_TEMPLATE_FILES:
        copy_file(relative_path)
    for relative_path in REPORT_FILES:
        copy_file(relative_path)
    for relative_dir in APP_SOURCE_DIRS:
        copy_source_tree(relative_dir)
    copy_accounts(include_wallet_secrets=include_wallet_secrets)
    write_launcher_files()
    build_zip()
    setup_exe = build_setup_exe() if build_setup_installer else None
    return {"zip_path": ZIP_PATH, "setup_exe_path": setup_exe}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Windows desktop ZIP package for GOLD PRO trader.")
    parser.add_argument("--include-wallet-secrets", action="store_true", help="Include wallet passwords in the ZIP. Use only for private local backups.")
    parser.add_argument("--portable-exe", action="store_true", default=True, help="Build standalone EXE runtimes with bundled Python libraries.")
    parser.add_argument("--no-portable-exe", action="store_true", help="Skip EXE build and package source files only.")
    parser.add_argument("--setup-exe", action="store_true", default=True, help="Build a one-file Windows setup EXE that embeds the ZIP package.")
    parser.add_argument("--no-setup-exe", action="store_true", help="Skip building the setup EXE.")
    args = parser.parse_args()
    build_portable = bool(args.portable_exe) and not bool(args.no_portable_exe)
    build_setup = bool(args.setup_exe) and not bool(args.no_setup_exe)
    result = build_package(
        include_wallet_secrets=bool(args.include_wallet_secrets),
        build_portable_exe=build_portable,
        build_setup_installer=build_setup,
    )
    print(
        json.dumps(
            {
                "success": True,
                "zip_path": str(result["zip_path"]),
                "setup_exe_path": str(result["setup_exe_path"]) if result.get("setup_exe_path") else None,
                "include_wallet_secrets": bool(args.include_wallet_secrets),
                "portable_exe": build_portable,
                "setup_exe": build_setup,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())