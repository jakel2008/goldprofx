from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from typing import Any, Dict, List


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _badge_class(value: str) -> str:
    text = str(value or "").strip().lower()
    if text in {"buy", "strong_buy"}:
        return "buy"
    if text in {"sell", "strong_sell"}:
        return "sell"
    return "wait"


def _row_class_from_delta(delta: Any) -> str:
    val = _to_float(delta)
    if val > 0:
        return "delta-pos"
    if val < 0:
        return "delta-neg"
    return "delta-zero"


def _strength_from_delta(delta: Any) -> str:
    val = abs(_to_float(delta))
    if val >= 50:
        return "strong"
    if val >= 20:
        return "medium"
    return "weak"


def _fmt_price(value: Any) -> str:
    try:
        num = float(value)
        return f"{num:.5f}"
    except Exception:
        text = str(value or "").strip()
        return text if text else "-"


def _labels(lang: str) -> Dict[str, str]:
    is_en = str(lang or "ar").strip().lower() == "en"
    if is_en:
        return {
            "title": "Shadow Signals Dashboard",
            "run": "Run",
            "generated": "Generated",
            "symbols": "Symbols",
            "intervals": "Intervals",
            "success": "Success",
            "failed": "Failed",
            "agreement": "Agreement",
            "avg_delta": "Avg Delta",
            "top_intervals": "Top Intervals",
            "bottom_intervals": "Bottom Intervals",
            "weekly_summary": "Weekly Summary",
            "run_count": "Run count",
            "avg_agreement": "Avg agreement",
            "alerts": "Alerts",
            "signals_detail": "Signals Detail",
            "interval": "Interval",
            "official": "Official",
            "experimental": "Experimental",
            "delta": "Delta",
            "chosen": "Chosen",
            "horizon": "Horizon",
            "trade_plan": "Trade Plan",
            "entry": "Entry",
            "stop_loss": "Stop Loss",
            "tp1": "TP1",
            "tp2": "TP2",
            "tp3": "TP3",
            "exp_entry": "Exp Entry",
            "agree": "Agree",
            "disagree": "Disagree",
            "no_data": "No data",
            "no_alerts": "No alerts",
            "alert_overall_low": "Weekly average agreement {value}% is below threshold {threshold}%.",
            "alert_interval_low": "Interval {interval} average agreement {value}% is below threshold {threshold}%.",
            "alert_interval_grouped": "Low-agreement interval alert repeated across {count} interval(s): {intervals} (min={value}%, threshold={threshold}%).",
            "alert_daily_grouped": "Daily low-agreement alert repeated across {count} day(s) from {start} to {end} (min={value}%, threshold={threshold}%).",
        }

    return {
        "title": "لوحة إشارات الشادو",
        "run": "التشغيل",
        "generated": "تم التوليد",
        "symbols": "الرموز",
        "intervals": "الفريمات",
        "success": "ناجح",
        "failed": "فاشل",
        "agreement": "نسبة التطابق",
        "avg_delta": "متوسط الفارق",
        "top_intervals": "أفضل الفريمات",
        "bottom_intervals": "أضعف الفريمات",
        "weekly_summary": "الملخص الأسبوعي",
        "run_count": "عدد مرات التشغيل",
        "avg_agreement": "متوسط التطابق",
        "alerts": "التنبيهات",
        "signals_detail": "تفاصيل الإشارات",
        "interval": "الفريم",
        "official": "الرسمي",
        "experimental": "التجريبي",
        "delta": "الفارق",
        "chosen": "الفريم المختار",
        "horizon": "الأفق",
        "trade_plan": "خطة الصفقة",
        "entry": "نقطة الدخول",
        "stop_loss": "وقف الخسارة",
        "tp1": "هدف 1",
        "tp2": "هدف 2",
        "tp3": "هدف 3",
        "exp_entry": "دخول التجريبي",
        "agree": "متطابق",
        "disagree": "غير متطابق",
        "no_data": "لا توجد بيانات",
        "no_alerts": "لا توجد تنبيهات",
        "alert_overall_low": "متوسط التطابق الأسبوعي {value}% أقل من العتبة {threshold}%.",
        "alert_interval_low": "الفريم {interval} متوسط التطابق فيه {value}% أقل من العتبة {threshold}%.",
        "alert_interval_grouped": "تنبيه انخفاض التطابق تكرر عبر {count} فريم/فريمات: {intervals} (الأدنى={value}%، العتبة={threshold}%).",
        "alert_daily_grouped": "تنبيه انخفاض التطابق اليومي تكرر خلال {count} يوم/أيام من {start} إلى {end} (الأدنى={value}%، العتبة={threshold}%).",
    }




def _format_alert(item: Dict[str, Any], labels: Dict[str, str]) -> str:
    alert_type = str(item.get("type") or "").strip()
    value = _to_float(item.get("value"))
    threshold = _to_float(item.get("threshold"))

    if alert_type == "overall_low_agreement":
        return labels["alert_overall_low"].format(value=value, threshold=threshold)

    if alert_type == "interval_low_agreement":
        return labels["alert_interval_low"].format(
            interval=str(item.get("interval") or "-"),
            value=value,
            threshold=threshold,
        )

    if alert_type == "interval_low_agreement_grouped":
        intervals = ", ".join(str(x) for x in (item.get("intervals") or []))
        return labels["alert_interval_grouped"].format(
            count=int(item.get("intervals_count") or 0),
            intervals=intervals or "-",
            value=value,
            threshold=threshold,
        )

    if alert_type == "daily_low_agreement_grouped":
        return labels["alert_daily_grouped"].format(
            count=int(item.get("days_count") or 0),
            start=str(item.get("start_date") or "-"),
            end=str(item.get("end_date") or "-"),
            value=value,
            threshold=threshold,
        )

    msg = str(item.get("message") or "").strip()
    return msg or labels["no_alerts"]


def render_shadow_static_html(
    batch_summary: Dict[str, Any],
    weekly_summary: Dict[str, Any],
    reports_by_interval: Dict[str, Dict[str, Any]],
    lang: str = "ar",
) -> str:
    lang = str(lang or "ar").strip().lower()
    if lang not in {"ar", "en"}:
        lang = "ar"
    labels = _labels(lang)
    page_dir = "ltr" if lang == "en" else "rtl"

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    run_id = batch_summary.get("run_id")
    symbols = batch_summary.get("symbols") or []
    intervals = batch_summary.get("intervals") or []

    alert_rows = weekly_summary.get("alerts") or []
    top_intervals = weekly_summary.get("top_intervals") or []
    bottom_intervals = weekly_summary.get("bottom_intervals") or []

    interval_cards: List[str] = []
    interval_tables: List[str] = []

    for idx, interval in enumerate(intervals):
        report = reports_by_interval.get(str(interval).lower()) or {}
        summary = {
            "success_symbols": int(report.get("success_symbols") or 0),
            "failed_symbols": int(report.get("failed_symbols") or 0),
            "agreement_rate_pct": _to_float(report.get("agreement_rate_pct")),
            "avg_direction_delta": _to_float(report.get("avg_direction_delta")),
        }

        interval_cards.append(
            """
            <div class='card'>
              <h3>{interval}</h3>
              <p>{success_label}: {success}</p>
              <p>{agreement_label}: {agreement:.2f}%</p>
              <p>{avg_delta_label}: {delta:.3f}</p>
            </div>
            """.format(
                interval=escape(str(interval)),
                success=summary["success_symbols"],
                agreement=summary["agreement_rate_pct"],
                delta=summary["avg_direction_delta"],
                success_label=escape(labels["success"]),
                agreement_label=escape(labels["agreement"]),
                avg_delta_label=escape(labels["avg_delta"]),
            )
        )

        cards_html: List[str] = []
        for item in report.get("results") or []:
            if not item.get("success"):
            # User requested successful signals only in the live page.
                continue

            official = item.get("official") or {}
            experimental = item.get("experimental") or {}
            comparison = item.get("comparison") or {}

            off_rec = str(official.get("normalized_recommendation") or "wait")
            exp_rec = str(experimental.get("normalized_recommendation") or "wait")
            delta = _to_float(comparison.get("direction_delta"))
            agree = bool(comparison.get("agreement"))
            strength = _strength_from_delta(delta)
            entry = _fmt_price(official.get("entry_point"))
            stop_loss = _fmt_price(official.get("stop_loss"))
            take_profit_1 = _fmt_price(official.get("take_profit_1"))
            take_profit_2 = _fmt_price(official.get("take_profit_2"))
            take_profit_3 = _fmt_price(official.get("take_profit_3"))
            exp_entry = _fmt_price(experimental.get("entry_price"))

            cards_html.append(
                """
                <article class='signal-card {delta_class}'>
                  <div class='signal-head'>
                    <h4>{symbol}</h4>
                    <div class='head-badges'>
                      <span class='agreement {agree_class}'>{agree}</span>
                      <span class='strength {strength}'>{strength}</span>
                    </div>
                  </div>
                  <div class='signal-pair'>
                    <span>{official_label}</span>
                    <span class='badge {off_badge}'>{off_rec}</span>
                  </div>
                  <div class='signal-pair'>
                    <span>{experimental_label}</span>
                    <span class='badge {exp_badge}'>{exp_rec}</span>
                  </div>
                  <div class='signal-meta'>
                    <span>{delta_label}: <strong>{delta:.3f}</strong></span>
                    <span>{chosen_label}: <strong>{chosen_interval}</strong></span>
                    <span>{horizon_label}: <strong>{horizon}</strong></span>
                  </div>
                  <div class='signal-levels'>
                    <h5>{trade_plan_label}</h5>
                    <div class='levels-grid'>
                      <span>{entry_label}</span><strong>{entry}</strong>
                      <span>{stop_loss_label}</span><strong>{stop_loss}</strong>
                      <span>{tp1_label}</span><strong>{tp1}</strong>
                      <span>{tp2_label}</span><strong>{tp2}</strong>
                      <span>{tp3_label}</span><strong>{tp3}</strong>
                      <span>{exp_entry_label}</span><strong>{exp_entry}</strong>
                    </div>
                  </div>
                </article>
                """.format(
                    delta_class=_row_class_from_delta(delta),
                    symbol=escape(str(item.get("symbol") or "")),
                    off_badge=_badge_class(off_rec),
                    off_rec=escape(off_rec),
                    exp_badge=_badge_class(exp_rec),
                    exp_rec=escape(exp_rec),
                    agree=labels["agree"] if agree else labels["disagree"],
                    agree_class="ok" if agree else "no",
                    strength=escape(strength),
                    delta=delta,
                    chosen_interval=escape(str(experimental.get("chosen_interval") or "-")),
                    horizon=escape(str(experimental.get("chosen_horizon") or "-")),
                    entry=escape(entry),
                    stop_loss=escape(stop_loss),
                    tp1=escape(take_profit_1),
                    tp2=escape(take_profit_2),
                    tp3=escape(take_profit_3),
                    exp_entry=escape(exp_entry),
                    official_label=escape(labels["official"]),
                    experimental_label=escape(labels["experimental"]),
                    delta_label=escape(labels["delta"]),
                    chosen_label=escape(labels["chosen"]),
                    horizon_label=escape(labels["horizon"]),
                    trade_plan_label=escape(labels["trade_plan"]),
                    entry_label=escape(labels["entry"]),
                    stop_loss_label=escape(labels["stop_loss"]),
                    tp1_label=escape(labels["tp1"]),
                    tp2_label=escape(labels["tp2"]),
                    tp3_label=escape(labels["tp3"]),
                    exp_entry_label=escape(labels["exp_entry"]),
                )
            )

        if not cards_html:
              cards_html.append(f"<article class='signal-card empty'>{escape(labels['no_data'])}</article>")

        active_class = "active" if idx == 0 else ""
        interval_tables.append(
            """
            <section id='panel-{interval}' class='interval-panel {active_class}'>
              <h3>{interval_label}: {interval}</h3>
              <div class='signal-grid'>
                {rows}
              </div>
            </section>
            """.format(
                interval=escape(str(interval)),
                active_class=active_class,
                rows="\n".join(cards_html),
                interval_label=escape(labels["interval"]),
            )
        )

    nav_buttons = []
    for idx, interval in enumerate(intervals):
        active_class = "active" if idx == 0 else ""
        nav_buttons.append(
            "<button class='tab-btn {active}' data-target='panel-{interval}'>{interval}</button>".format(
                active=active_class,
                interval=escape(str(interval)),
            )
        )

    top_html = "".join(
        "<li>{interval}: agreement={agreement:.2f}% delta={delta:.3f}</li>".format(
            interval=escape(str(item.get("interval") or "-")),
            agreement=_to_float(item.get("avg_agreement_rate_pct")),
            delta=_to_float(item.get("avg_direction_delta")),
        )
        for item in top_intervals
    ) or f"<li>{escape(labels['no_data'])}</li>"

    bottom_html = "".join(
        "<li>{interval}: agreement={agreement:.2f}% delta={delta:.3f}</li>".format(
            interval=escape(str(item.get("interval") or "-")),
            agreement=_to_float(item.get("avg_agreement_rate_pct")),
            delta=_to_float(item.get("avg_direction_delta")),
        )
        for item in bottom_intervals
    ) or f"<li>{escape(labels['no_data'])}</li>"

    alerts_html = "".join(
      "<li>{msg}</li>".format(msg=escape(_format_alert(item, labels)))
      for item in alert_rows
    ) or f"<li>{escape(labels['no_alerts'])}</li>"

    html = """
<!doctype html>
<html lang='[[LANG]]' dir='[[DIR]]'>
<head>
  <meta charset='utf-8' />
  <meta name='viewport' content='width=device-width, initial-scale=1' />
  <title>[[TITLE]]</title>
  <style>
    :root {
      --bg: #f4f7fb;
      --panel: #ffffff;
      --ink: #15202b;
      --muted: #52606d;
      --line: #d9e2ec;
      --buy: #0f9d58;
      --sell: #d93025;
      --wait: #f9ab00;
      --accent: #0b57d0;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Segoe UI, Tahoma, sans-serif;
      background: linear-gradient(180deg, #eef4ff 0%, #f7f9fc 60%, #ffffff 100%);
      color: var(--ink);
    }
    .container { max-width: 1240px; margin: 0 auto; padding: 20px; }
    .header { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 16px; }
    .meta { color: var(--muted); font-size: 14px; }
    .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-top: 14px; }
    .card { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 12px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px; }
    .panel { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 12px; }
    .tab-nav { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
    .tab-btn {
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      padding: 8px 12px;
      border-radius: 8px;
      cursor: pointer;
    }
    .tab-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }
    .interval-panel { display: none; margin-top: 12px; }
    .interval-panel.active { display: block; }
    .badge { display: inline-block; min-width: 56px; text-align: center; padding: 2px 8px; border-radius: 999px; color: #fff; font-size: 12px; }
    .badge.buy { background: var(--buy); }
    .badge.sell { background: var(--sell); }
    .badge.wait { background: var(--wait); color: #202124; }
    .signal-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 10px; }
    .signal-card {
      border: 1px solid var(--line);
      border-radius: 12px;
      background: #fff;
      padding: 10px;
    }
    .signal-card.failed { border-color: #f4b4b1; background: #fff6f6; }
    .signal-card.empty { color: var(--muted); text-align: center; padding: 18px 10px; }
    .signal-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .signal-head h4 { margin: 0; font-size: 16px; }
    .head-badges { display: flex; gap: 6px; align-items: center; }
    .signal-pair { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 13px; }
    .signal-meta { display: flex; flex-direction: column; gap: 4px; font-size: 13px; margin-top: 8px; color: var(--muted); }
    .signal-levels { margin-top: 10px; border-top: 1px dashed var(--line); padding-top: 8px; }
    .signal-levels h5 { margin: 0 0 6px; font-size: 12px; color: #334155; letter-spacing: 0.3px; text-transform: uppercase; }
    .levels-grid {
      display: grid;
      grid-template-columns: 1fr auto;
      row-gap: 4px;
      column-gap: 8px;
      font-size: 12px;
      color: #334155;
    }
    .levels-grid strong { color: #0f172a; font-weight: 700; }
    .agreement { font-size: 12px; border-radius: 999px; padding: 2px 8px; }
    .agreement.ok { background: #e9f7ee; color: #0f9d58; }
    .agreement.no { background: #fdecec; color: #d93025; }
    .strength { font-size: 12px; border-radius: 999px; padding: 2px 8px; text-transform: uppercase; letter-spacing: 0.3px; }
    .strength.weak { background: #eef2f6; color: #3b4a5a; }
    .strength.medium { background: #fff4e5; color: #b26a00; }
    .strength.strong { background: #fdecec; color: #b42318; }
    .error { margin: 6px 0 0; color: #b42318; font-size: 13px; }
    .delta-pos { background: #f1fbf4; }
    .delta-neg { background: #fff5f5; }
    .delta-zero { background: #fffdf2; }
    ul { margin: 8px 0 0 18px; }
    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body data-run-id='[[RUN_ID_RAW]]'>
  <div class='container'>
    <section class='header'>
      <h1>[[TITLE]]</h1>
      <p class='meta'>[[RUN_LABEL]]: [[RUN_ID]] | [[GENERATED_LABEL]]: [[GENERATED]]</p>
      <p class='meta'>[[SYMBOLS_LABEL]]: [[SYMBOLS]] | [[INTERVALS_LABEL]]: [[INTERVALS]]</p>
      <div class='cards'>
        [[INTERVAL_CARDS]]
      </div>
    </section>

    <section class='grid'>
      <article class='panel'>
        <h3>[[TOP_INTERVALS_LABEL]]</h3>
        <ul>[[TOP_HTML]]</ul>
      </article>
      <article class='panel'>
        <h3>[[BOTTOM_INTERVALS_LABEL]]</h3>
        <ul>[[BOTTOM_HTML]]</ul>
      </article>
      <article class='panel'>
        <h3>[[WEEKLY_SUMMARY_LABEL]]</h3>
        <ul>
          <li>[[RUN_COUNT_LABEL]]: [[RUN_COUNT]]</li>
          <li>[[AVG_AGREEMENT_LABEL]]: [[AVG_AGREEMENT]]%</li>
          <li>[[AVG_DELTA_LABEL]]: [[AVG_DELTA]]</li>
          <li>[[ALERTS_LABEL]]: [[ALERTS_COUNT]]</li>
        </ul>
      </article>
      <article class='panel'>
        <h3>[[ALERTS_LABEL]]</h3>
        <ul>[[ALERTS_HTML]]</ul>
      </article>
    </section>

    <section class='panel'>
      <h2>[[SIGNALS_DETAIL_LABEL]]</h2>
      <div class='tab-nav'>
        [[TAB_BUTTONS]]
      </div>
      [[INTERVAL_TABLES]]
    </section>
  </div>

  <script>
    const buttons = Array.from(document.querySelectorAll('.tab-btn'));
    const panels = Array.from(document.querySelectorAll('.interval-panel'));
    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        buttons.forEach(b => b.classList.remove('active'));
        panels.forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        const target = document.getElementById(btn.dataset.target);
        if (target) target.classList.add('active');
      });
    });

    // Live mode: auto-refresh page and alert when a new run_id is detected.
    const currentRunId = document.body.dataset.runId || '';
    const storageKey = 'shadow_last_run_id';
    const refreshMs = 45000;
    const newSignalAlert = '[[NEW_SIGNAL_ALERT]]';
    const knownRunId = localStorage.getItem(storageKey) || currentRunId;
    localStorage.setItem(storageKey, knownRunId || currentRunId);

    async function checkForNewRun() {
      try {
        const url = window.location.href.split('#')[0] + (window.location.search ? '&' : '?') + '_ts=' + Date.now();
        const resp = await fetch(url, { cache: 'no-store' });
        if (!resp.ok) return;
        const text = await resp.text();
        const doc = new DOMParser().parseFromString(text, 'text/html');
        const remoteRunId = (doc.body && doc.body.dataset && doc.body.dataset.runId) ? doc.body.dataset.runId : '';
        const lastKnown = localStorage.getItem(storageKey) || currentRunId;
        if (remoteRunId && lastKnown && remoteRunId !== lastKnown) {
          localStorage.setItem(storageKey, remoteRunId);
          alert(newSignalAlert + '\nRun: ' + remoteRunId);
          window.location.reload();
        }
      } catch (e) {
        // Ignore transient network errors.
      }
    }

    setInterval(checkForNewRun, refreshMs);
  </script>
</body>
</html>
"""

    html = html.replace("[[RUN_ID]]", escape(str(run_id or "-")))
    html = html.replace("[[RUN_ID_RAW]]", escape(str(run_id or "")))
    html = html.replace("[[LANG]]", escape(lang))
    html = html.replace("[[DIR]]", escape(page_dir))
    html = html.replace("[[TITLE]]", escape(labels["title"]))
    html = html.replace("[[RUN_LABEL]]", escape(labels["run"]))
    html = html.replace("[[GENERATED_LABEL]]", escape(labels["generated"]))
    html = html.replace("[[SYMBOLS_LABEL]]", escape(labels["symbols"]))
    html = html.replace("[[INTERVALS_LABEL]]", escape(labels["intervals"]))
    html = html.replace("[[TOP_INTERVALS_LABEL]]", escape(labels["top_intervals"]))
    html = html.replace("[[BOTTOM_INTERVALS_LABEL]]", escape(labels["bottom_intervals"]))
    html = html.replace("[[WEEKLY_SUMMARY_LABEL]]", escape(labels["weekly_summary"]))
    html = html.replace("[[RUN_COUNT_LABEL]]", escape(labels["run_count"]))
    html = html.replace("[[AVG_AGREEMENT_LABEL]]", escape(labels["avg_agreement"]))
    html = html.replace("[[AVG_DELTA_LABEL]]", escape(labels["avg_delta"]))
    html = html.replace("[[ALERTS_LABEL]]", escape(labels["alerts"]))
    html = html.replace("[[SIGNALS_DETAIL_LABEL]]", escape(labels["signals_detail"]))
    html = html.replace(
      "[[NEW_SIGNAL_ALERT]]",
      escape("تم اكتشاف إشارة/تحديث جديد" if lang == "ar" else "New signal update detected"),
    )
    html = html.replace("[[GENERATED]]", escape(generated))
    html = html.replace("[[SYMBOLS]]", escape(", ".join(str(item) for item in symbols) if symbols else "-"))
    html = html.replace("[[INTERVALS]]", escape(", ".join(str(item) for item in intervals) if intervals else "-"))
    html = html.replace("[[INTERVAL_CARDS]]", "\n".join(interval_cards))
    html = html.replace("[[TOP_HTML]]", top_html)
    html = html.replace("[[BOTTOM_HTML]]", bottom_html)
    html = html.replace("[[RUN_COUNT]]", str(int(weekly_summary.get("run_count") or 0)))
    html = html.replace("[[AVG_AGREEMENT]]", f"{_to_float(weekly_summary.get('avg_agreement_rate_pct')):.2f}")
    html = html.replace("[[AVG_DELTA]]", f"{_to_float(weekly_summary.get('avg_direction_delta')):.3f}")
    html = html.replace("[[ALERTS_COUNT]]", str(len(alert_rows)))
    html = html.replace("[[ALERTS_HTML]]", alerts_html)
    html = html.replace("[[TAB_BUTTONS]]", "\n".join(nav_buttons))
    html = html.replace("[[INTERVAL_TABLES]]", "\n".join(interval_tables))
    return html
