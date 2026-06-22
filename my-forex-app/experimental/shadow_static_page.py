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


def _fmt_minutes_left(value: Any, lang: str) -> str:
    if value in (None, ""):
        return "-"
    try:
        minutes = int(value)
    except Exception:
        return "-"

    if lang == "en":
        if minutes > 0:
            return f"in {minutes}m"
        if minutes < 0:
            return f"{abs(minutes)}m ago"
        return "now"

    if minutes > 0:
        return f"بعد {minutes} دقيقة"
    if minutes < 0:
        return f"منذ {abs(minutes)} دقيقة"
    return "الآن"


def _impact_badge_class(value: str) -> str:
    text = str(value or "").strip().lower()
    if text == "high":
        return "impact-high"
    if text == "medium":
        return "impact-medium"
    return "impact-low"


def _status_badge_class(value: str) -> str:
  text = str(value or "").strip().lower()
  if text in {"مستمرة", "active", "running", "live"}:
    return "active"
  if text in {"متوقفة", "stopped", "paused"}:
    return "stopped"
  if text in {"منتهية", "expired", "ended"}:
    return "expired"
  return "active"


def _derive_signal_status(
  official: Dict[str, Any],
  experimental: Dict[str, Any],
  item: Dict[str, Any],
  lang: str,
) -> tuple[str, str]:
  is_en = str(lang or "ar").strip().lower() == "en"
  stopped = "Stopped" if is_en else "متوقفة"
  active = "Active" if is_en else "مستمرة"

  explicit_status = str(
    official.get("signal_status")
    or experimental.get("signal_status")
    or item.get("signal_status")
    or ""
  ).strip()
  explicit_reason = str(
    official.get("signal_status_reason")
    or experimental.get("signal_status_reason")
    or item.get("signal_status_reason")
    or ""
  ).strip()

  if experimental.get("news_blocked"):
    reason = "Stopped by economic news filter" if is_en else "موقوفة بسبب فلتر الأخبار أو التقويم الاقتصادي"
    return stopped, explicit_reason or reason

  exp_rec = str(experimental.get("normalized_recommendation") or "wait").strip().lower()
  off_rec = str(official.get("normalized_recommendation") or "wait").strip().lower()
  if exp_rec == "wait":
    if off_rec == "wait":
      reason = "No clear directional edge" if is_en else "لا توجد أفضلية اتجاهية واضحة"
    else:
      reason = "Experimental model is waiting" if is_en else "النموذج التجريبي يوصي بالانتظار"
    return stopped, explicit_reason or reason

  if explicit_status:
    return explicit_status, explicit_reason or ("Ready for broadcast" if is_en else "جاهزة للبث")

  return active, explicit_reason or ("Ready for broadcast" if is_en else "جاهزة للبث")


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
            "data_source": "Data Source",
            "current_price": "Current Price",
            "price_updated": "Price Updated",
            "signal_status": "Status",
            "signal_status_reason": "Reason",
            "signal_expires_at": "Expires At",
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
            "news_title": "Economic News",
            "news_event": "Event",
            "news_currency": "Currency",
            "news_impact": "Impact",
            "news_time_left": "Time left",
            "news_time": "Time",
            "news_actual": "Actual",
            "news_forecast": "Forecast",
            "news_previous": "Previous",
            "news_revision": "Revision",
            "news_source": "Source",
            "news_none": "No matching economic event",
            "news_enter_alert": "Imminent economic event for this symbol",
            "mt5_controls": "MT5 Execution",
            "mt5_volume": "Volume",
            "mt5_dry_run": "Dry Run",
            "mt5_auto": "Auto execute active interval",
            "mt5_execute_active": "Execute Active Interval",
            "mt5_activate": "Activate on MT5",
            "mt5_wait": "No executable direction",
            "mt5_pending_mode": "Pending Orders: entry price, stop loss, and all targets are sent to MT5.",
            "mt5_sending": "Sending to MT5...",
            "mt5_auto_on": "Auto execution is enabled for the active interval.",
            "mt5_dry_note": "Dry Run is enabled: no real order is sent.",
            "mt5_success": "MT5 activation succeeded",
            "mt5_failed": "MT5 activation failed",
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
        "data_source": "مصدر البيانات",
        "current_price": "السعر الحالي",
        "price_updated": "تحديث السعر",
        "signal_status": "حالة الإشارة",
        "signal_status_reason": "السبب",
        "signal_expires_at": "تنتهي عند",
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
        "news_title": "الخبر الاقتصادي",
        "news_event": "الحدث",
        "news_currency": "العملة",
        "news_impact": "التأثير",
        "news_time_left": "الوقت المتبقي",
        "news_time": "الوقت",
        "news_actual": "الفعلي",
        "news_forecast": "المتوقع",
        "news_previous": "السابق",
        "news_revision": "المراجعة",
        "news_source": "المصدر",
        "news_none": "لا يوجد حدث اقتصادي مطابق",
        "news_enter_alert": "حدث اقتصادي قريب لهذا الزوج",
        "mt5_controls": "تنفيذ MT5",
        "mt5_volume": "الحجم",
        "mt5_dry_run": "تشغيل تجريبي",
        "mt5_auto": "تنفيذ تلقائي للفريم النشط",
        "mt5_execute_active": "تنفيذ الفريم النشط",
        "mt5_activate": "تفعيل على MT5",
        "mt5_wait": "لا يوجد اتجاه قابل للتنفيذ",
        "mt5_pending_mode": "أوامر معلّقة: يتم إرسال سعر الدخول ووقف الخسارة وجميع الأهداف إلى MT5.",
        "mt5_sending": "جاري الإرسال إلى MT5...",
        "mt5_auto_on": "التنفيذ التلقائي مفعّل للفريم النشط.",
        "mt5_dry_note": "التشغيل التجريبي مفعّل: لا يتم إرسال أمر حقيقي.",
        "mt5_success": "تم تفعيل MT5 بنجاح",
        "mt5_failed": "فشل تفعيل MT5",
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
                symbol = str(item.get("symbol") or "-")
                error_text = str(item.get("error") or labels["no_data"]).strip()
                cards_html.append(
                    """
                    <article class='signal-card failed' data-live-symbol='{symbol}' data-mt5-executable='0' data-symbol='{symbol}' data-interval='{interval}' data-recommendation='wait' data-entry='' data-sl='' data-tp1='' data-tp2='' data-tp3=''>
                      <div class='signal-head'>
                        <h4>{symbol}</h4>
                        <div class='head-badges'>
                          <span class='agreement no'>{failed_label}</span>
                        </div>
                      </div>
                      <div class='signal-pair'>
                        <span>{official_label}</span>
                        <span class='badge wait'>{no_data_label}</span>
                      </div>
                      <div class='signal-pair'>
                        <span>{experimental_label}</span>
                        <span class='badge wait'>{no_data_label}</span>
                      </div>
                      <div class='signal-meta'>
                        <span>{status_label}: <strong class='status-pill stopped'>{failed_label}</strong></span>
                        <span>{reason_label}: <strong>{error_text}</strong></span>
                      </div>
                      <div class='mt5-actions'>
                        <button class='mt5-btn' type='button' data-role='mt5-activate' disabled>{mt5_wait_label}</button>
                        <span class='mt5-result' data-role='mt5-result'>{mt5_wait_label}</span>
                      </div>
                    </article>
                    """.format(
                        symbol=escape(symbol),
                        interval=escape(str(interval)),
                        failed_label=escape(labels["failed"]),
                        no_data_label=escape(labels["no_data"]),
                        official_label=escape(labels["official"]),
                        experimental_label=escape(labels["experimental"]),
                        status_label=escape(labels["signal_status"]),
                        reason_label=escape(labels["signal_status_reason"]),
                        error_text=escape(error_text),
                        mt5_wait_label=escape(labels["mt5_wait"]),
                    )
                )
                continue

            official = item.get("official") or {}
            experimental = item.get("experimental") or {}
            comparison = item.get("comparison") or {}

            off_rec = str(official.get("normalized_recommendation") or "wait")
            exp_rec = str(experimental.get("normalized_recommendation") or "wait")
            delta = _to_float(comparison.get("direction_delta"))
            agree = bool(comparison.get("agreement"))
            strength = _strength_from_delta(delta)
            market_data_source = str(official.get("market_data_source") or comparison.get("market_data_source") or "-")
            signal_status, signal_status_reason = _derive_signal_status(official, experimental, item, lang)
            signal_expires_at = str(
              official.get("expires_at")
              or experimental.get("expires_at")
              or item.get("expires_at")
              or "-"
            )
            entry = _fmt_price(official.get("entry_point"))
            stop_loss = _fmt_price(official.get("stop_loss"))
            take_profit_1 = _fmt_price(official.get("take_profit_1"))
            take_profit_2 = _fmt_price(official.get("take_profit_2"))
            take_profit_3 = _fmt_price(official.get("take_profit_3"))
            exp_entry = _fmt_price(experimental.get("entry_price"))
            executable = off_rec in {"buy", "sell"} and all(
              value not in {"", "-"}
              for value in (entry, stop_loss, take_profit_1, take_profit_2, take_profit_3)
            )
            news_info = experimental.get("news_info") or {}
            news_context_info = experimental.get("news_context_info") or {}
            event_title = str(news_context_info.get("event_title") or "").strip()
            event_currency = ", ".join(str(x) for x in (news_context_info.get("event_currencies") or []))
            event_time_left = _fmt_minutes_left(news_info.get("minutes_to_event"), lang)
            event_time = str(news_context_info.get("event_time_utc") or "-")
            event_impact = str(news_info.get("impact") or "low").lower()
            event_actual = str(news_context_info.get("actual") or "-")
            event_forecast = str(news_context_info.get("forecast") or "-")
            event_previous = str(news_context_info.get("previous") or "-")
            event_revision = str(news_context_info.get("revision") or "-")
            event_source = str(news_context_info.get("source") or "-")
            event_minutes = news_info.get("minutes_to_event")
            try:
                event_minutes_int = int(event_minutes) if event_minutes is not None else 99999
            except Exception:
                event_minutes_int = 99999
            imminent = -15 <= event_minutes_int <= 30
            impact_badge = _impact_badge_class(event_impact)

            if event_title:
                news_html = """
                  <div class='news-box {imminent_class}' data-news-minutes='{news_minutes}' data-news-symbol='{symbol}' data-news-impact='{news_impact}' data-news-event='{news_event}' data-news-time-utc='{news_time_utc}'>
                    <h5>{news_title}</h5>
                    <div class='news-row'><span>{news_event_label}</span><strong>{news_event}</strong></div>
                    <div class='news-row'><span>{news_currency_label}</span><strong>{news_currency}</strong></div>
                    <div class='news-row'><span>{news_impact_label}</span><strong class='impact-pill {impact_badge}'>{news_impact}</strong></div>
                    <div class='news-row'><span>{news_time_left_label}</span><strong class='news-time-left'>{news_time_left}</strong></div>
                    <div class='news-row'><span>{news_time_label}</span><strong>{news_time}</strong></div>
                    <div class='news-grid'>
                      <span>{news_actual_label}</span><strong>{news_actual}</strong>
                      <span>{news_forecast_label}</span><strong>{news_forecast}</strong>
                      <span>{news_previous_label}</span><strong>{news_previous}</strong>
                      <span>{news_revision_label}</span><strong>{news_revision}</strong>
                    </div>
                    <p class='news-source'>{news_source_label}: {news_source}</p>
                  </div>
                """.format(
                    imminent_class="imminent" if imminent else "",
                    news_minutes=escape(str(event_minutes_int)),
                    symbol=escape(str(item.get("symbol") or "")),
                    news_time_utc=escape(str(news_context_info.get("event_time_utc") or "")),
                    news_title=escape(labels["news_title"]),
                    news_event_label=escape(labels["news_event"]),
                    news_event=escape(event_title),
                    news_currency_label=escape(labels["news_currency"]),
                    news_currency=escape(event_currency or "-"),
                    news_impact_label=escape(labels["news_impact"]),
                    news_impact=escape(event_impact),
                    impact_badge=impact_badge,
                    news_time_left_label=escape(labels["news_time_left"]),
                    news_time_left=escape(event_time_left),
                    news_time_label=escape(labels["news_time"]),
                    news_time=escape(event_time),
                    news_actual_label=escape(labels["news_actual"]),
                    news_actual=escape(event_actual),
                    news_forecast_label=escape(labels["news_forecast"]),
                    news_forecast=escape(event_forecast),
                    news_previous_label=escape(labels["news_previous"]),
                    news_previous=escape(event_previous),
                    news_revision_label=escape(labels["news_revision"]),
                    news_revision=escape(event_revision),
                    news_source_label=escape(labels["news_source"]),
                    news_source=escape(event_source),
                )
            else:
                news_html = "<div class='news-box empty'>{}</div>".format(escape(labels["news_none"]))

            cards_html.append(
                """
                <article class='signal-card {delta_class}' data-live-symbol='{live_symbol}' data-mt5-executable='{mt5_executable}' data-symbol='{symbol}' data-interval='{interval}' data-recommendation='{mt5_recommendation}' data-entry='{entry}' data-sl='{stop_loss}' data-tp1='{tp1}' data-tp2='{tp2}' data-tp3='{tp3}'>
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
                    <span>{source_label}: <strong>{market_data_source}</strong></span>
                    <span>{current_price_label}: <strong class='current-price-value'>-</strong></span>
                    <span>{price_updated_label}: <strong class='current-price-updated'>-</strong></span>
                    <span>{status_label}: <strong class='status-pill {status_class}'>{signal_status}</strong></span>
                    <span>{reason_label}: <strong>{signal_status_reason}</strong></span>
                    <span>{expires_label}: <strong>{signal_expires_at}</strong></span>
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
                  <div class='mt5-actions'>
                    <button class='mt5-btn' type='button' data-role='mt5-activate' {mt5_disabled}>{mt5_activate_label}</button>
                    <span class='mt5-result' data-role='mt5-result'>{mt5_hint}</span>
                  </div>
                  {news_html}
                </article>
                """.format(
                    delta_class=_row_class_from_delta(delta),
                    symbol=escape(str(item.get("symbol") or "")),
                    interval=escape(str(interval)),
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
                    mt5_executable="1" if executable else "0",
                    mt5_recommendation=escape(off_rec),
                    mt5_disabled="" if executable else "disabled",
                    mt5_activate_label=escape(labels["mt5_activate"] if executable else labels["mt5_wait"]),
                    mt5_hint=escape("" if executable else labels["mt5_wait"]),
                    official_label=escape(labels["official"]),
                    experimental_label=escape(labels["experimental"]),
                    delta_label=escape(labels["delta"]),
                    chosen_label=escape(labels["chosen"]),
                    horizon_label=escape(labels["horizon"]),
                    source_label=escape(labels["data_source"]),
                    current_price_label=escape(labels["current_price"]),
                    price_updated_label=escape(labels["price_updated"]),
                    status_label=escape(labels["signal_status"]),
                    reason_label=escape(labels["signal_status_reason"]),
                    expires_label=escape(labels["signal_expires_at"]),
                    trade_plan_label=escape(labels["trade_plan"]),
                    entry_label=escape(labels["entry"]),
                    stop_loss_label=escape(labels["stop_loss"]),
                    tp1_label=escape(labels["tp1"]),
                    tp2_label=escape(labels["tp2"]),
                    tp3_label=escape(labels["tp3"]),
                    exp_entry_label=escape(labels["exp_entry"]),
                    market_data_source=escape(market_data_source),
                    status_class=_status_badge_class(signal_status),
                    signal_status=escape(signal_status),
                    signal_status_reason=escape(signal_status_reason),
                    signal_expires_at=escape(signal_expires_at),
                    live_symbol=escape(str(item.get("symbol") or "")),
                    news_html=news_html,
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
    .status-pill { display: inline-block; padding: 2px 8px; border-radius: 999px; color: #fff; font-size: 12px; }
    .status-pill.active { background: #1f7a1f; }
    .status-pill.stopped { background: #b42318; }
    .status-pill.expired { background: #7a4f01; }
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
    .mt5-toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      margin: 10px 0 12px;
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: #f8fafc;
    }
    .mt5-toolbar label { display: inline-flex; gap: 6px; align-items: center; font-size: 13px; color: #334155; }
    .mt5-volume { width: 92px; padding: 7px 8px; border: 1px solid var(--line); border-radius: 8px; }
    .mt5-btn {
      border: 1px solid #0b57d0;
      background: #0b57d0;
      color: #fff;
      border-radius: 8px;
      padding: 7px 10px;
      cursor: pointer;
      font-size: 12px;
      min-height: 32px;
    }
    .mt5-btn:disabled { cursor: not-allowed; opacity: 0.55; background: #94a3b8; border-color: #94a3b8; }
    .mt5-actions { display: flex; flex-direction: column; gap: 6px; margin-top: 10px; border-top: 1px dashed var(--line); padding-top: 8px; }
    .mt5-result { min-height: 16px; font-size: 12px; color: #475467; }
    .mt5-result.ok { color: #0f9d58; }
    .mt5-result.err { color: #b42318; }
    .levels-grid {
      display: grid;
      grid-template-columns: 1fr auto;
      row-gap: 4px;
      column-gap: 8px;
      font-size: 12px;
      color: #334155;
    }
    .levels-grid strong { color: #0f172a; font-weight: 700; }
    .news-box {
      margin-top: 10px;
      border: 1px solid #dbe7ff;
      background: #f7fbff;
      border-radius: 10px;
      padding: 8px;
    }
    .news-box.empty { color: var(--muted); text-align: center; background: #f8fafc; border-color: #e5e7eb; }
    .news-box.imminent { border-color: #ef4444; background: #fff1f2; box-shadow: 0 0 0 1px #fecdd3 inset; }
    .news-box h5 { margin: 0 0 8px; font-size: 12px; text-transform: uppercase; letter-spacing: 0.3px; }
    .news-row { display: flex; justify-content: space-between; gap: 8px; font-size: 12px; margin: 2px 0; }
    .news-grid {
      margin-top: 6px;
      display: grid;
      grid-template-columns: 1fr auto;
      row-gap: 3px;
      column-gap: 8px;
      font-size: 12px;
    }
    .impact-pill {
      display: inline-block;
      border-radius: 999px;
      padding: 1px 8px;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.3px;
      color: #fff;
    }
    .impact-pill.impact-high { background: #b42318; }
    .impact-pill.impact-medium { background: #b26a00; }
    .impact-pill.impact-low { background: #475467; }
    .news-source { margin: 7px 0 0; font-size: 11px; color: #475467; }
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
      <div class='mt5-toolbar'>
        <strong>[[MT5_CONTROLS_LABEL]]</strong>
        <label>[[MT5_VOLUME_LABEL]] <input id='mt5-volume' class='mt5-volume' type='number' min='0.01' step='0.01' value='0.01'></label>
        <label><input id='mt5-dry-run' type='checkbox' checked> [[MT5_DRY_RUN_LABEL]]</label>
        <label><input id='mt5-auto-execute' type='checkbox'> [[MT5_AUTO_LABEL]]</label>
        <button id='mt5-execute-active' class='mt5-btn' type='button'>[[MT5_EXECUTE_ACTIVE_LABEL]]</button>
        <span id='mt5-toolbar-result' class='mt5-result'>[[MT5_PENDING_MODE]] [[MT5_DRY_NOTE]]</span>
      </div>
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
        autoExecuteActiveIntervalOnce();
      });
    });

    // Live mode: auto-refresh page and alert when a new run_id is detected.
    const currentRunId = document.body.dataset.runId || '';
    const storageKey = 'shadow_last_run_id';
    const refreshMs = 45000;
    const newSignalAlert = '[[NEW_SIGNAL_ALERT]]';
    const newsEnterAlert = '[[NEWS_ENTER_ALERT]]';
    const lang = document.documentElement.getAttribute('lang') || 'ar';
    const knownRunId = localStorage.getItem(storageKey) || currentRunId;
    localStorage.setItem(storageKey, knownRunId || currentRunId);

    const mt5Labels = {
      sending: '[[MT5_SENDING_LABEL]]',
      success: '[[MT5_SUCCESS_LABEL]]',
      failed: '[[MT5_FAILED_LABEL]]',
      autoOn: '[[MT5_AUTO_ON_LABEL]]',
      dryNote: '[[MT5_DRY_NOTE]]'
    };
    const mt5VolumeInput = document.getElementById('mt5-volume');
    const mt5DryRunInput = document.getElementById('mt5-dry-run');
    const mt5AutoInput = document.getElementById('mt5-auto-execute');
    const mt5ExecuteActiveBtn = document.getElementById('mt5-execute-active');
    const mt5ToolbarResult = document.getElementById('mt5-toolbar-result');
    const mt5AutoStorageKey = 'shadow_mt5_auto_execute';
    const mt5VolumeStorageKey = 'shadow_mt5_volume';
    const mt5DryRunStorageKey = 'shadow_mt5_dry_run';

    if (mt5AutoInput) mt5AutoInput.checked = localStorage.getItem(mt5AutoStorageKey) === '1';
    if (mt5VolumeInput && localStorage.getItem(mt5VolumeStorageKey)) mt5VolumeInput.value = localStorage.getItem(mt5VolumeStorageKey);
    if (mt5DryRunInput && localStorage.getItem(mt5DryRunStorageKey)) mt5DryRunInput.checked = localStorage.getItem(mt5DryRunStorageKey) !== '0';

    function getMt5Volume() {
      const value = mt5VolumeInput ? Number(mt5VolumeInput.value || '0.01') : 0.01;
      return Number.isFinite(value) && value > 0 ? value : 0.01;
    }

    function setMt5Message(target, message, ok) {
      const el = target || mt5ToolbarResult;
      if (!el) return;
      el.textContent = message || '';
      el.classList.remove('ok', 'err');
      if (ok === true) el.classList.add('ok');
      if (ok === false) el.classList.add('err');
    }

    function buildMt5Payload(card) {
      return {
        symbol: card.dataset.symbol,
        recommendation: card.dataset.recommendation,
        interval: card.dataset.interval || '1h',
        entry_price: Number(card.dataset.entry),
        stop_loss: Number(card.dataset.sl),
        take_profit1: Number(card.dataset.tp1),
        take_profit2: Number(card.dataset.tp2),
        take_profit3: Number(card.dataset.tp3),
        volume: getMt5Volume(),
        split_tp: true,
        pending_entry: true,
        dry_run: mt5DryRunInput ? Boolean(mt5DryRunInput.checked) : true
      };
    }

    async function activateMt5Card(card) {
      if (!card || card.dataset.mt5Executable !== '1') return false;
      const resultEl = card.querySelector('[data-role="mt5-result"]');
      const button = card.querySelector('[data-role="mt5-activate"]');
      const payload = buildMt5Payload(card);
      if (button) button.disabled = true;
      setMt5Message(resultEl, mt5Labels.sending, null);
      try {
        const response = await fetch('/api/shadow/mt5/activate-signal', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const contentType = response.headers.get('content-type') || '';
        if (!contentType.includes('application/json')) {
          const rawText = await response.text();
          throw new Error(rawText.replace(/<[^>]*>/g, ' ').replace(/\\s+/g, ' ').trim() || 'Unexpected response');
        }
        const data = await response.json();
        if (!response.ok || !data.success) {
          const orderErrors = Array.isArray(data?.result?.orders)
            ? data.result.orders.filter(item => item && item.success === false && item.error).map(item => item.error)
            : [];
          throw new Error(data?.error || data?.result?.error || orderErrors[0] || 'activation failed');
        }
        const login = data?.mt5_context?.login;
        const dry = data?.payload?.dry_run === true;
        const orderTypes = Array.isArray(data?.result?.orders)
          ? data.result.orders.map(item => item?.metadata?.order_type_name).filter(Boolean)
          : [];
        const orderSummary = orderTypes.length ? ' [' + Array.from(new Set(orderTypes)).join(', ') + ']' : '';
        const message = mt5Labels.success + orderSummary + (login ? ' (' + login + ')' : '') + (dry ? ' - ' + mt5Labels.dryNote : '');
        setMt5Message(resultEl, message, true);
        setMt5Message(mt5ToolbarResult, message, true);
        card.dataset.mt5Executed = '1';
        return true;
      } catch (error) {
        const message = mt5Labels.failed + ': ' + (error.message || error);
        setMt5Message(resultEl, message, false);
        setMt5Message(mt5ToolbarResult, message, false);
        return false;
      } finally {
        if (button) button.disabled = false;
      }
    }

    async function executeActiveInterval() {
      const activePanel = document.querySelector('.interval-panel.active') || document;
      const cards = Array.from(activePanel.querySelectorAll('.signal-card[data-mt5-executable="1"]'));
      let done = 0;
      for (const card of cards) {
        if (await activateMt5Card(card)) done += 1;
      }
      setMt5Message(mt5ToolbarResult, (lang === 'en' ? 'Executed cards: ' : 'البطاقات المنفذة: ') + done, true);
    }

    async function autoExecuteActiveIntervalOnce() {
      if (!mt5AutoInput || !mt5AutoInput.checked) return;
      const activePanel = document.querySelector('.interval-panel.active');
      const interval = activePanel ? activePanel.id.replace('panel-', '') : 'active';
      const key = 'shadow_mt5_auto_done_' + currentRunId + '_' + interval;
      if (localStorage.getItem(key)) return;
      localStorage.setItem(key, String(Date.now()));
      setMt5Message(mt5ToolbarResult, mt5Labels.autoOn, null);
      await executeActiveInterval();
    }

    document.addEventListener('click', event => {
      const button = event.target.closest('[data-role="mt5-activate"]');
      if (!button) return;
      activateMt5Card(button.closest('.signal-card'));
    });
    if (mt5ExecuteActiveBtn) mt5ExecuteActiveBtn.addEventListener('click', executeActiveInterval);
    if (mt5AutoInput) mt5AutoInput.addEventListener('change', () => {
      localStorage.setItem(mt5AutoStorageKey, mt5AutoInput.checked ? '1' : '0');
      if (mt5AutoInput.checked) autoExecuteActiveIntervalOnce();
    });
    if (mt5VolumeInput) mt5VolumeInput.addEventListener('change', () => localStorage.setItem(mt5VolumeStorageKey, mt5VolumeInput.value || '0.01'));
    if (mt5DryRunInput) mt5DryRunInput.addEventListener('change', () => localStorage.setItem(mt5DryRunStorageKey, mt5DryRunInput.checked ? '1' : '0'));

    function formatMinutesText(minutes) {
      if (!Number.isFinite(minutes)) return '-';
      if (lang === 'en') {
        if (minutes > 0) return 'in ' + minutes + 'm';
        if (minutes < 0) return Math.abs(minutes) + 'm ago';
        return 'now';
      }
      if (minutes > 0) return 'بعد ' + minutes + ' دقيقة';
      if (minutes < 0) return 'منذ ' + Math.abs(minutes) + ' دقيقة';
      return 'الآن';
    }

    function playImpactTone(impact) {
      try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return;
        const ctx = new AudioCtx();

        const now = ctx.currentTime;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';

        let freq = 720;
        let dur = 0.22;
        if (impact === 'high') {
          freq = 980;
          dur = 0.35;
        } else if (impact === 'medium') {
          freq = 820;
          dur = 0.28;
        }

        osc.frequency.setValueAtTime(freq, now);
        gain.gain.setValueAtTime(0.0001, now);
        gain.gain.exponentialRampToValueAtTime(0.18, now + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + dur);

        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + dur + 0.02);
      } catch (e) {
        // Ignore audio restrictions silently.
      }
    }

    function updateLiveNewsCountdown() {
      const cards = Array.from(document.querySelectorAll('.news-box[data-news-time-utc], .news-box[data-news-minutes]'));
      const nowMs = Date.now();
      cards.forEach(card => {
        const leftEl = card.querySelector('.news-time-left');
        if (!leftEl) return;

        let mins = Number(card.dataset.newsMinutes || 'NaN');
        const eventUtc = String(card.dataset.newsTimeUtc || '').trim();
        if (eventUtc) {
          const ms = Date.parse(eventUtc);
          if (!Number.isNaN(ms)) {
            mins = Math.floor((ms - nowMs) / 60000);
          }
        }

        if (!Number.isFinite(mins)) return;
        card.dataset.newsMinutes = String(mins);
        leftEl.textContent = formatMinutesText(mins);

        if (mins >= -15 && mins <= 30) {
          card.classList.add('imminent');
        } else {
          card.classList.remove('imminent');
        }
      });
    }

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
          alert(newSignalAlert + '\\nRun: ' + remoteRunId);
          window.location.reload();
        }
      } catch (e) {
        // Ignore transient network errors.
      }
    }

    function formatLivePrice(value) {
      const num = Number(value);
      if (!Number.isFinite(num)) return '-';
      return num.toFixed(5);
    }

    async function refreshLivePrices() {
      if (!window.location.protocol.startsWith('http')) return;

      const activePanel = document.querySelector('.interval-panel.active');
      const cards = Array.from((activePanel || document).querySelectorAll('.signal-card[data-live-symbol]'));
      if (!cards.length) return;

      const symbols = Array.from(new Set(cards
        .map(card => String(card.getAttribute('data-live-symbol') || '').trim().toUpperCase())
        .filter(Boolean)));
      if (!symbols.length) return;

      try {
        const params = new URLSearchParams();
        params.set('symbols', symbols.join(','));
        const resp = await fetch('/api/live-prices?' + params.toString(), { cache: 'no-store' });
        if (!resp.ok) return;

        const data = await resp.json();
        if (!data || !data.success) return;

        const bySymbol = new Map();
        for (const row of (data.prices || [])) {
          const key = String(row.symbol || '').trim().toUpperCase();
          if (!key) continue;
          bySymbol.set(key, row);
        }

        cards.forEach(card => {
          const symbol = String(card.getAttribute('data-live-symbol') || '').trim().toUpperCase();
          const priceNode = card.querySelector('.current-price-value');
          const updatedNode = card.querySelector('.current-price-updated');
          if (!priceNode || !updatedNode) return;

          const row = bySymbol.get(symbol);
          if (!row) {
            return;
          }

          priceNode.textContent = formatLivePrice(row.current_price);
          updatedNode.textContent = String(row.updated_at || '-');
        });
      } catch (e) {
        // Ignore transient fetch errors.
      }
    }

    setInterval(checkForNewRun, refreshMs);
    setInterval(updateLiveNewsCountdown, 1000);
    setInterval(refreshLivePrices, 15000);
    updateLiveNewsCountdown();
    refreshLivePrices();

    // News proximity alert: notify when a card has an imminent event window.
    function checkNewsImminentCards() {
      try {
        const cards = Array.from(document.querySelectorAll('.news-box.imminent[data-news-minutes][data-news-symbol]'));
        const hits = [];
        cards.forEach(card => {
          const mins = Number(card.dataset.newsMinutes || '99999');
          const symbol = String(card.dataset.newsSymbol || '').trim();
          const impact = String(card.dataset.newsImpact || 'low').trim().toLowerCase();
          const eventName = String(card.dataset.newsEvent || '').trim();
          if (!symbol) return;
          if (mins >= -15 && mins <= 30) hits.push({ symbol, mins, impact, eventName });
        });
        if (!hits.length) return;

        const runId = document.body.dataset.runId || 'na';
        const alertKey = 'shadow_news_alert_' + runId;
        if (sessionStorage.getItem(alertKey)) return;

        sessionStorage.setItem(alertKey, '1');
        const strongest = hits.some(h => h.impact === 'high') ? 'high' : (hits.some(h => h.impact === 'medium') ? 'medium' : 'low');
        playImpactTone(strongest);
        const text = hits
          .slice(0, 6)
          .map(h => h.symbol + ' | ' + (h.eventName || '-') + ' | ' + (h.mins >= 0 ? '+' + h.mins : h.mins) + 'm')
          .join(', ');
        alert(newsEnterAlert + '\\n' + text);
      } catch (e) {
        // ignore
      }
    }

    checkNewsImminentCards();
    autoExecuteActiveIntervalOnce();
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
    html = html.replace("[[MT5_CONTROLS_LABEL]]", escape(labels["mt5_controls"]))
    html = html.replace("[[MT5_VOLUME_LABEL]]", escape(labels["mt5_volume"]))
    html = html.replace("[[MT5_DRY_RUN_LABEL]]", escape(labels["mt5_dry_run"]))
    html = html.replace("[[MT5_AUTO_LABEL]]", escape(labels["mt5_auto"]))
    html = html.replace("[[MT5_EXECUTE_ACTIVE_LABEL]]", escape(labels["mt5_execute_active"]))
    html = html.replace("[[MT5_PENDING_MODE]]", escape(labels["mt5_pending_mode"]))
    html = html.replace("[[MT5_SENDING_LABEL]]", escape(labels["mt5_sending"]))
    html = html.replace("[[MT5_AUTO_ON_LABEL]]", escape(labels["mt5_auto_on"]))
    html = html.replace("[[MT5_DRY_NOTE]]", escape(labels["mt5_dry_note"]))
    html = html.replace("[[MT5_SUCCESS_LABEL]]", escape(labels["mt5_success"]))
    html = html.replace("[[MT5_FAILED_LABEL]]", escape(labels["mt5_failed"]))
    html = html.replace(
      "[[NEW_SIGNAL_ALERT]]",
      escape("تم اكتشاف إشارة/تحديث جديد" if lang == "ar" else "New signal update detected"),
    )
    html = html.replace(
      "[[NEWS_ENTER_ALERT]]",
      escape(labels["news_enter_alert"]),
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
