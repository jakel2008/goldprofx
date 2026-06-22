from __future__ import annotations

import ast
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.advanced_analyzer_engine import build_provider_coverage_matrix


def _extract_symbols_from_recommendations_engine(project_root: Path) -> list[str]:
    target = project_root / "recommendations_engine.py"
    if not target.exists():
        return []

    source = target.read_text(encoding="utf-8")
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target_node in node.targets:
                if isinstance(target_node, ast.Name) and target_node.id == "ALL_AVAILABLE_PAIRS":
                    value = ast.literal_eval(node.value)
                    symbols = []
                    if isinstance(value, dict):
                        for bucket in value.values():
                            if isinstance(bucket, dict):
                                symbols.extend(str(key).upper() for key in bucket.keys())
                    return sorted(set(symbols))
    return []


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    symbols = _extract_symbols_from_recommendations_engine(project_root)
    matrix = build_provider_coverage_matrix(symbols=symbols or None)

    reports_dir = Path(__file__).resolve().parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_file = reports_dir / "provider_coverage_matrix.json"

    payload: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "source_symbols": "recommendations_engine.ALL_AVAILABLE_PAIRS" if symbols else "advanced_analyzer_engine.SUPPORTED_SYMBOLS",
        "matrix": matrix,
    }

    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    rows = matrix.get("rows", [])
    oanda_supported = sum(1 for row in rows if row.get("providers", {}).get("oanda", {}).get("supported"))
    print(f"saved: {out_file}")
    print(f"rows: {len(rows)}")
    print(f"oanda_supported_rows: {oanda_supported}")


if __name__ == "__main__":
    main()
