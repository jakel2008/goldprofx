#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).parent
DB_PATH = ROOT / "vip_subscriptions.db"
REPORTS_DIR = ROOT / "reports"


def fetch_rows(report_date: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS delivery_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan TEXT,
            content_type TEXT,
            quality_score INTEGER,
            quality_bucket TEXT,
            status TEXT,
            reason TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    c.execute('''
        SELECT user_id, plan, content_type, quality_score, quality_bucket, status, reason, sent_at
        FROM delivery_audit
        WHERE DATE(sent_at) = ?
        ORDER BY sent_at DESC
    ''', (report_date,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def write_csv(report_date: str, rows):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"delivery_report_{report_date}.csv"

    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["date", report_date])
        writer.writerow([])
        writer.writerow(["user_id", "plan", "content_type", "quality_score", "quality_bucket", "status", "reason", "sent_at"])

        for r in rows:
            writer.writerow([
                r.get("user_id"),
                r.get("plan"),
                r.get("content_type"),
                r.get("quality_score"),
                r.get("quality_bucket"),
                r.get("status"),
                r.get("reason"),
                r.get("sent_at"),
            ])

        writer.writerow([])
        writer.writerow(["summary_by_plan"])
        writer.writerow(["plan", "status", "count"])

        summary = defaultdict(int)
        for r in rows:
            key = (str(r.get("plan") or "unknown"), str(r.get("status") or "unknown"))
            summary[key] += 1

        for (plan, status), count in sorted(summary.items(), key=lambda x: (x[0][0], x[0][1])):
            writer.writerow([plan, status, count])

    return out_path


def main():
    parser = argparse.ArgumentParser(description="Generate daily delivery CSV report")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="Report date format YYYY-MM-DD")
    args = parser.parse_args()

    rows = fetch_rows(args.date)
    out_path = write_csv(args.date, rows)
    print(f"report_date={args.date}")
    print(f"rows={len(rows)}")
    print(f"csv={out_path}")


if __name__ == "__main__":
    main()
