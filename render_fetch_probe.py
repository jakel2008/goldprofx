# -*- coding: utf-8 -*-
"""Standalone diagnostic probe for Render data-fetch / analysis crashes.

Runs each stage in isolation and prints a single JSON line to stdout so the
caller (a Flask debug endpoint) can run it as a subprocess. Because it runs in
its OWN process, a native crash (segfault) or OOM kill here does NOT take down
the web worker; the caller can inspect the subprocess return code:

    returncode  0   -> completed (see JSON "ok"/"error")
    returncode -9   -> killed by SIGKILL (almost always OOM on Render free plan)
    returncode -11  -> killed by SIGSEGV (native segfault: numpy/pandas/ta)

Usage:  python render_fetch_probe.py SYMBOL INTERVAL
"""
import json
import sys
import time
import traceback


def _stage(result, name, ok, **extra):
    entry = {"stage": name, "ok": ok}
    entry.update(extra)
    result["stages"].append(entry)


def main():
    symbol = sys.argv[1] if len(sys.argv) > 1 else "EURUSD"
    interval = sys.argv[2] if len(sys.argv) > 2 else "1h"

    result = {
        "symbol": symbol,
        "interval": interval,
        "ok": False,
        "error": None,
        "stages": [],
    }

    # Stage 1: import forex_analyzer
    t0 = time.time()
    try:
        import forex_analyzer  # type: ignore
        _stage(result, "import_forex_analyzer", True, ms=int((time.time() - t0) * 1000))
    except Exception as e:  # noqa: BLE001
        result["error"] = f"import_forex_analyzer: {type(e).__name__}: {e}"
        _stage(result, "import_forex_analyzer", False, error=traceback.format_exc(limit=6))
        print(json.dumps(result, ensure_ascii=False))
        return

    # Stage 2: fetch_data
    t0 = time.time()
    try:
        df = forex_analyzer.fetch_data(symbol, interval, outputsize=100, force_live=True)
        rows = 0 if df is None else len(df)
        cols = [] if df is None else [str(c) for c in df.columns][:12]
        _stage(result, "fetch_data", True, rows=rows, columns=cols, ms=int((time.time() - t0) * 1000))
    except Exception as e:  # noqa: BLE001
        result["error"] = f"fetch_data: {type(e).__name__}: {e}"
        _stage(result, "fetch_data", False, error=traceback.format_exc(limit=8), ms=int((time.time() - t0) * 1000))
        print(json.dumps(result, ensure_ascii=False))
        return

    # Stage 3: import advanced_analyzer_engine
    t0 = time.time()
    try:
        import advanced_analyzer_engine  # type: ignore
        _stage(result, "import_analyzer_engine", True, ms=int((time.time() - t0) * 1000))
    except Exception as e:  # noqa: BLE001
        result["error"] = f"import_analyzer_engine: {type(e).__name__}: {e}"
        _stage(result, "import_analyzer_engine", False, error=traceback.format_exc(limit=6))
        print(json.dumps(result, ensure_ascii=False))
        return

    # Stage 4: perform_full_analysis (the suspected crash site)
    t0 = time.time()
    try:
        analysis = advanced_analyzer_engine.perform_full_analysis(symbol, interval, False)
        keys = sorted(list(analysis.keys()))[:25] if isinstance(analysis, dict) else None
        rec = analysis.get("recommendation") if isinstance(analysis, dict) else None
        _stage(result, "perform_full_analysis", True, keys=keys, recommendation=rec, ms=int((time.time() - t0) * 1000))
        result["ok"] = True
    except Exception as e:  # noqa: BLE001
        result["error"] = f"perform_full_analysis: {type(e).__name__}: {e}"
        _stage(result, "perform_full_analysis", False, error=traceback.format_exc(limit=10), ms=int((time.time() - t0) * 1000))

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
