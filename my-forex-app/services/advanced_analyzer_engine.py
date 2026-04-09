from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import yfinance as yf


SUPPORTED_SYMBOLS = {
	"EURUSD": {"ticker": "EURUSD=X", "label": "EUR/USD"},
	"GBPUSD": {"ticker": "GBPUSD=X", "label": "GBP/USD"},
	"USDJPY": {"ticker": "USDJPY=X", "label": "USD/JPY"},
	"USDCHF": {"ticker": "USDCHF=X", "label": "USD/CHF"},
	"AUDUSD": {"ticker": "AUDUSD=X", "label": "AUD/USD"},
	"USDCAD": {"ticker": "USDCAD=X", "label": "USD/CAD"},
	"NZDUSD": {"ticker": "NZDUSD=X", "label": "NZD/USD"},
	"EURGBP": {"ticker": "EURGBP=X", "label": "EUR/GBP"},
	"EURJPY": {"ticker": "EURJPY=X", "label": "EUR/JPY"},
	"EURCHF": {"ticker": "EURCHF=X", "label": "EUR/CHF"},
	"EURAUD": {"ticker": "EURAUD=X", "label": "EUR/AUD"},
	"EURCAD": {"ticker": "EURCAD=X", "label": "EUR/CAD"},
	"EURNZD": {"ticker": "EURNZD=X", "label": "EUR/NZD"},
	"GBPJPY": {"ticker": "GBPJPY=X", "label": "GBP/JPY"},
	"GBPCHF": {"ticker": "GBPCHF=X", "label": "GBP/CHF"},
	"GBPAUD": {"ticker": "GBPAUD=X", "label": "GBP/AUD"},
	"GBPCAD": {"ticker": "GBPCAD=X", "label": "GBP/CAD"},
	"GBPNZD": {"ticker": "GBPNZD=X", "label": "GBP/NZD"},
	"AUDJPY": {"ticker": "AUDJPY=X", "label": "AUD/JPY"},
	"AUDNZD": {"ticker": "AUDNZD=X", "label": "AUD/NZD"},
	"AUDCAD": {"ticker": "AUDCAD=X", "label": "AUD/CAD"},
	"AUDCHF": {"ticker": "AUDCHF=X", "label": "AUD/CHF"},
	"CADJPY": {"ticker": "CADJPY=X", "label": "CAD/JPY"},
	"CADCHF": {"ticker": "CADCHF=X", "label": "CAD/CHF"},
	"CHFJPY": {"ticker": "CHFJPY=X", "label": "CHF/JPY"},
	"NZDJPY": {"ticker": "NZDJPY=X", "label": "NZD/JPY"},
	"NZDCHF": {"ticker": "NZDCHF=X", "label": "NZD/CHF"},
	"NZDCAD": {"ticker": "NZDCAD=X", "label": "NZD/CAD"},
	"US500": {"ticker": "ES=F", "label": "S&P 500"},
	"NAS100": {"ticker": "NQ=F", "label": "Nasdaq 100"},
	"US30": {"ticker": "YM=F", "label": "Dow Jones 30"},
	"US2000": {"ticker": "RTY=F", "label": "Russell 2000"},
	"BTCUSD": {"ticker": "BTC-USD", "label": "Bitcoin / USD"},
	"ETHUSD": {"ticker": "ETH-USD", "label": "Ethereum / USD"},
	"SOLUSD": {"ticker": "SOL-USD", "label": "Solana / USD"},
	"XRPUSD": {"ticker": "XRP-USD", "label": "XRP / USD"},
	"BNBUSD": {"ticker": "BNB-USD", "label": "BNB / USD"},
	"XAUUSD": {"ticker": "GC=F", "label": "Gold / USD"},
	"XAGUSD": {"ticker": "SI=F", "label": "Silver / USD"},
}

PRICE_PRECISION = {
	"XAUUSD": 2,
	"XAGUSD": 3,
	"US500": 2,
	"NAS100": 2,
	"US30": 2,
	"US2000": 2,
	"BTCUSD": 2,
	"ETHUSD": 2,
	"SOLUSD": 3,
	"XRPUSD": 4,
	"BNBUSD": 2,
}

SUPPORTED_INTERVALS = {
	"5m": {"yf_interval": "5m", "period": "10d", "risk_multiplier": 0.90},
	"15m": {"yf_interval": "15m", "period": "30d", "risk_multiplier": 1.00},
	"30m": {"yf_interval": "30m", "period": "30d", "risk_multiplier": 1.15},
	"1h": {"yf_interval": "60m", "period": "60d", "risk_multiplier": 1.30},
	"4h": {"yf_interval": "60m", "period": "180d", "risk_multiplier": 1.80},
	"1d": {"yf_interval": "1d", "period": "1y", "risk_multiplier": 2.40},
}


def _normalize_symbol(symbol: str) -> str:
	return (symbol or "").strip().upper().replace("/", "")


def _normalize_interval(interval: str) -> str:
	return (interval or "").strip().lower()


def _round_price(value: float, symbol: str) -> float:
	precision = PRICE_PRECISION.get(symbol, 5)
	return round(float(value), precision)


def _compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
	delta = close.diff()
	gains = delta.clip(lower=0)
	losses = -delta.clip(upper=0)
	avg_gain = gains.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
	avg_loss = losses.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
	rs = avg_gain / avg_loss.replace(0, pd.NA)
	rsi = 100 - (100 / (1 + rs))
	return rsi.fillna(50)


def _compute_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
	previous_close = data["Close"].shift(1)
	true_range = pd.concat(
		[
			data["High"] - data["Low"],
			(data["High"] - previous_close).abs(),
			(data["Low"] - previous_close).abs(),
		],
		axis=1,
	).max(axis=1)
	return true_range.rolling(period).mean().bfill()


def _confidence_label(score_gap: int) -> str:
	if score_gap >= 36:
		return "مرتفعة"
	if score_gap >= 18:
		return "جيدة"
	return "متوسطة"


def _recommendation_from_gap(score_gap: int) -> str:
	if score_gap >= 26:
		return "شراء قوي"
	if score_gap >= 10:
		return "شراء"
	if score_gap <= -26:
		return "بيع قوي"
	if score_gap <= -10:
		return "بيع"
	return "انتظار"


def _score_market(data: pd.DataFrame) -> tuple[int, int, dict]:
	close = data["Close"]
	ema12 = close.ewm(span=12, adjust=False).mean()
	ema26 = close.ewm(span=26, adjust=False).mean()
	macd = ema12 - ema26
	macd_signal = macd.ewm(span=9, adjust=False).mean()
	sma20 = close.rolling(20).mean().bfill()
	sma50 = close.rolling(50).mean().bfill()
	rsi14 = _compute_rsi(close)
	atr14 = _compute_atr(data)
	momentum = close.pct_change(5).fillna(0) * 100
	trend_strength = ((close - sma20) / sma20.replace(0, pd.NA)).fillna(0) * 100

	latest = data.iloc[-1]
	last_close = float(data["Close"].iloc[-1])
	last_open = float(data["Open"].iloc[-1])
	_vol_series = data.get("Volume", pd.Series(dtype=float))
	last_volume = float(_vol_series.iloc[-1]) if len(_vol_series) > 0 and pd.notna(_vol_series.iloc[-1]) else 0.0
	average_volume = float(_vol_series.tail(20).mean() or 0)

	buy_score = 0
	sell_score = 0

	if last_close > float(sma20.iloc[-1]):
		buy_score += 18
	else:
		sell_score += 18

	if float(sma20.iloc[-1]) > float(sma50.iloc[-1]):
		buy_score += 18
	else:
		sell_score += 18

	if float(macd.iloc[-1]) > float(macd_signal.iloc[-1]):
		buy_score += 16
	else:
		sell_score += 16

	rsi_value = float(rsi14.iloc[-1])
	if 52 <= rsi_value <= 68:
		buy_score += 14
	elif 32 <= rsi_value <= 48:
		sell_score += 14
	elif rsi_value > 70:
		sell_score += 9
	elif rsi_value < 30:
		buy_score += 9

	momentum_value = float(momentum.iloc[-1])
	if momentum_value > 0:
		buy_score += 14
	elif momentum_value < 0:
		sell_score += 14

	if last_close > last_open:
		buy_score += 10
	elif last_close < last_open:
		sell_score += 10

	if average_volume > 0 and last_volume > average_volume:
		if buy_score >= sell_score:
			buy_score += 10
		else:
			sell_score += 10

	buy_score = max(0, min(100, buy_score))
	sell_score = max(0, min(100, sell_score))

	details = {
		"rsi": round(rsi_value, 2),
		"macd": round(float(macd.iloc[-1]), 5),
		"macd_signal": round(float(macd_signal.iloc[-1]), 5),
		"sma20": round(float(sma20.iloc[-1]), 5),
		"sma50": round(float(sma50.iloc[-1]), 5),
		"atr14": float(atr14.iloc[-1]),
		"momentum_pct": round(momentum_value, 3),
		"trend_pct_from_sma20": round(float(trend_strength.iloc[-1]), 3),
	}
	return buy_score, sell_score, details


def _build_signals(recommendation: str, buy_score: int, sell_score: int, details: dict, price_change_pct: float) -> list[str]:
	signals = [
		f"التوصية الحالية: {recommendation}",
		f"قوة الشراء: {buy_score}/100 مقابل قوة البيع: {sell_score}/100",
		f"التغير السعري الأخير: {price_change_pct:.3f}%",
		f"RSI 14: {details['rsi']}",
		f"الفارق عن متوسط 20 شمعة: {details['trend_pct_from_sma20']:.3f}%",
		f"زخم آخر 5 شموع: {details['momentum_pct']:.3f}%",
	]
	if recommendation == "شراء قوي":
		signals.append("السعر فوق متوسطاته القصيرة والمتوسطة مع زخم داعم للاتجاه الصاعد")
	elif recommendation == "بيع قوي":
		signals.append("السعر دون متوسطاته الرئيسية مع ضغط فني هابط واضح")
	elif recommendation == "شراء":
		signals.append("الانحياز إيجابي لكن التوافق بين المؤشرات ليس كاملاً بعد")
	elif recommendation == "بيع":
		signals.append("الانحياز سلبي لكن ما زالت هناك حاجة لتأكيد إضافي")
	else:
		signals.append("الإشارات الفنية متقاربة، لذلك الانتظار أكثر انضباطاً من الدخول السريع")
	return signals


def _build_professional_scenario(
	symbol: str,
	recommendation: str,
	entry_point: float,
	take_profit1: float,
	take_profit2: float,
	take_profit3: float,
	stop_loss: float,
	market_data: pd.DataFrame,
	atr_value: float,
	confidence: str,
	details: dict,
) -> dict:
	recent_window = market_data.tail(20)
	support = _round_price(float(recent_window["Low"].min()), symbol)
	resistance = _round_price(float(recent_window["High"].max()), symbol)
	pivot = _round_price(float((support + resistance) / 2), symbol)
	entry_buffer = _round_price(max(atr_value * 0.35, entry_point * 0.0008), symbol)
	risk_distance = abs(entry_point - stop_loss)
	reward_distance = abs(take_profit2 - entry_point)
	risk_reward_ratio = round(reward_distance / risk_distance, 2) if risk_distance else 0.0
	bullish_bias = recommendation in ["شراء", "شراء قوي"]
	bearish_bias = recommendation in ["بيع", "بيع قوي"]

	if bullish_bias:
		bias = "صاعد"
		primary_title = "سيناريو الشراء المفضل"
		primary_trigger = f"يفعل إذا حافظ السعر على التداول أعلى {support} مع ثبات فوق {pivot}."
		primary_entry = f"منطقة المتابعة بين {max(_round_price(entry_point - entry_buffer, symbol), support)} و {entry_point}."
		primary_targets = [take_profit1, take_profit2, take_profit3]
		primary_invalidation = f"إغلاق واضح أسفل {stop_loss} يلغي الفكرة الصاعدة قصيرة الأجل."
		alternative_title = "السيناريو البديل"
		alternative_trigger = f"إذا فشل السعر في الحفاظ على {support} فقد يتحول إلى ضغط هابط باتجاه {stop_loss}."
		alternative_plan = f"في هذه الحالة يفضل تقليص المخاطرة وانتظار إعادة بناء هيكل فوق {pivot} قبل أي دخول جديد."
	elif bearish_bias:
		bias = "هابط"
		primary_title = "سيناريو البيع المفضل"
		primary_trigger = f"يفعل إذا بقي السعر دون {resistance} واستمر التداول أسفل {pivot}."
		primary_entry = f"منطقة المتابعة بين {entry_point} و {min(_round_price(entry_point + entry_buffer, symbol), resistance)}."
		primary_targets = [take_profit1, take_profit2, take_profit3]
		primary_invalidation = f"إغلاق واضح أعلى {stop_loss} يلغي الفكرة الهابطة قصيرة الأجل."
		alternative_title = "السيناريو البديل"
		alternative_trigger = f"اختراق {resistance} مع ثبات سعري قد ينقل السوق إلى ارتداد معاكس قصير المدى."
		alternative_plan = f"في هذه الحالة يفضل تجنب ملاحقة البيع والانتظار حتى يعود السعر دون {pivot}."
	else:
		bias = "محايد"
		primary_title = "سيناريو الانتظار"
		primary_trigger = f"السوق يتحرك داخل نطاق بين {support} و {resistance} بدون أفضلية واضحة."
		primary_entry = f"الأفضل انتظار كسر مؤكد أعلى {resistance} أو أسفل {support} قبل بناء مركز جديد."
		primary_targets = [resistance, pivot, support]
		primary_invalidation = f"أي دخول داخل النطاق الحالي يظل منخفض الجودة ما لم تتحسن الزخمات الفنية."
		alternative_title = "السيناريو البديل"
		alternative_trigger = f"في حال ارتفع RSI فوق 60 مع اختراق {resistance} يميل السوق للصعود، أما الكسر دون {support} فيرجح الهبوط."
		alternative_plan = "يتم التحول من الحياد إلى الاتجاه فقط بعد كسر مدعوم بزخم وحجم تداول أفضل من المتوسط."

	market_state = "زخم متوازن" if bias == "محايد" else f"انحياز {bias} بثقة {confidence}"
	return {
		"bias": bias,
		"market_state": market_state,
		"risk_reward_ratio": risk_reward_ratio,
		"primary": {
			"title": primary_title,
			"trigger": primary_trigger,
			"entry_zone": primary_entry,
			"targets": primary_targets,
			"invalidation": primary_invalidation,
		},
		"alternative": {
			"title": alternative_title,
			"trigger": alternative_trigger,
			"plan": alternative_plan,
		},
		"levels": {
			"support": support,
			"pivot": pivot,
			"resistance": resistance,
		},
		"risk_management": [
			f"لا تتجاوز المخاطرة لكل صفقة 1% إلى 2% من رأس المال.",
			f"أفضلية الخطة الحالية {risk_reward_ratio}:1 تقريباً حتى الهدف الثاني.",
			f"RSI الحالي {details['rsi']} و MACD عند {details['macd']} مقابل إشارة {details['macd_signal']}.",
		],
	}


def _build_multi_horizon_scenarios(
	symbol: str,
	recommendation: str,
	entry_point: float,
	take_profit1: float,
	take_profit2: float,
	take_profit3: float,
	stop_loss: float,
	scenario: dict,
	confidence: str,
) -> dict:
	bias = scenario["bias"]
	levels = scenario["levels"]
	bullish_bias = bias == "صاعد"
	bearish_bias = bias == "هابط"

	def bounded_entry(low_value: float, high_value: float) -> str:
		return f"بين {_round_price(low_value, symbol)} و {_round_price(high_value, symbol)}"

	if bullish_bias:
		short_term = {
			"title": "المدى القصير",
			"stance": "شراء تكتيكي مع انتظار تأكيد قريب.",
			"trigger": f"ثبات أعلى {levels['pivot']} مع بقاء التداول فوق {levels['support']}.",
			"entry_zone": bounded_entry(levels['support'], entry_point),
			"target": take_profit1,
			"invalidation": f"كسر {stop_loss} يلغي السيناريو السريع.",
		}
		medium_term = {
			"title": "المدى المتوسط",
			"stance": "استمرار صاعد طالما لم يفقد السعر البنية الإيجابية.",
			"trigger": f"اختراق {levels['resistance']} أو إعادة اختبار ناجحة فوق {levels['pivot']}.",
			"entry_zone": bounded_entry(entry_point, take_profit1),
			"target": take_profit2,
			"invalidation": f"إغلاق دون {levels['support']} يضعف المتابعة المتوسطة.",
		}
		long_term = {
			"title": "المدى الأطول",
			"stance": "الاحتفاظ الجزئي مبرر فقط إذا تحسن الزخم وبقيت الثقة {confidence} أو أعلى.",
			"trigger": f"استقرار أعلى {take_profit1} مع اتساع المسافة عن المتوسطات المتحركة.",
			"entry_zone": bounded_entry(levels['pivot'], take_profit1),
			"target": take_profit3,
			"invalidation": f"عودة السعر دون {levels['pivot']} تعني أن الاحتفاظ الطويل لم يعد مفضلًا.",
		}
	elif bearish_bias:
		short_term = {
			"title": "المدى القصير",
			"stance": "بيع تكتيكي مع مراقبة الكسر الهابط.",
			"trigger": f"ثبات دون {levels['pivot']} مع بقاء السعر أسفل {levels['resistance']}.",
			"entry_zone": bounded_entry(entry_point, levels['resistance']),
			"target": take_profit1,
			"invalidation": f"اختراق {stop_loss} يلغي السيناريو السريع.",
		}
		medium_term = {
			"title": "المدى المتوسط",
			"stance": "استمرار هابط طالما أن الارتدادات تبقى محدودة تحت المقاومة.",
			"trigger": f"كسر {levels['support']} أو فشل إعادة الاختبار قرب {levels['pivot']}.",
			"entry_zone": bounded_entry(take_profit1, entry_point),
			"target": take_profit2,
			"invalidation": f"إغلاق فوق {levels['resistance']} يضعف المتابعة المتوسطة.",
		}
		long_term = {
			"title": "المدى الأطول",
			"stance": "الاحتفاظ الجزئي مبرر إذا استمر الهيكل الهابط وبقيت الثقة {confidence} أو أعلى.",
			"trigger": f"استقرار دون {take_profit1} مع بقاء الضغط أسفل المحور {levels['pivot']}.",
			"entry_zone": bounded_entry(take_profit1, levels['pivot']),
			"target": take_profit3,
			"invalidation": f"العودة فوق {levels['pivot']} تقلل جودة السيناريو الطويل.",
		}
	else:
		short_term = {
			"title": "المدى القصير",
			"stance": "حياد تكتيكي حتى يظهر كسر واضح للنطاق.",
			"trigger": f"مراقبة سلوك السعر بين {levels['support']} و {levels['resistance']}.",
			"entry_zone": bounded_entry(levels['support'], levels['resistance']),
			"target": levels['pivot'],
			"invalidation": "لا توجد أفضلية فنية كافية لبناء مركز مباشر داخل النطاق.",
		}
		medium_term = {
			"title": "المدى المتوسط",
			"stance": "التحول إلى اتجاهي فقط بعد خروج مؤكد من النطاق الحالي.",
			"trigger": f"اختراق {levels['resistance']} أو كسر {levels['support']} مع زخم داعم.",
			"entry_zone": bounded_entry(levels['support'], levels['resistance']),
			"target": levels['resistance'],
			"invalidation": "استمرار التذبذب الضيق يبقي فرص المتابعة ضعيفة.",
		}
		long_term = {
			"title": "المدى الأطول",
			"stance": "الاحتفاظ غير مفضل حتى تتشكل بنية اتجاهية أوضح.",
			"trigger": f"إغلاق يومي خارج النطاق {levels['support']} - {levels['resistance']}.",
			"entry_zone": bounded_entry(levels['support'], levels['resistance']),
			"target": levels['resistance'],
			"invalidation": "كل عودة سريعة إلى قلب النطاق تلغي جدوى الاحتفاظ الطويل.",
		}

	return {
		"short_term": short_term,
		"medium_term": medium_term,
		"long_term": long_term,
	}


def _build_executive_summary(
	symbol_label: str,
	interval: str,
	recommendation: str,
	confidence: str,
	scenario: dict,
	price_change_pct: float,
	technical: dict,
) -> dict:
	bias = scenario["bias"]
	if bias == "صاعد":
		headline = f"الترجيح الحالي يميل إلى الصعود على {symbol_label} ضمن إطار {interval}."
		overview = "البنية الفنية تدعم متابعة الموجة الصاعدة ما دام السعر يحافظ على التداول أعلى المحور والدعم القريب."
		tactical = "الأفضل هو متابعة الشراء على مراحل مع تخفيف المخاطر عند الهدف الأول ورفع الوقف تدريجيًا."
	elif bias == "هابط":
		headline = f"الترجيح الحالي يميل إلى الهبوط على {symbol_label} ضمن إطار {interval}."
		overview = "الهيكل الفني يفضل استمرار الضغط البيعي طالما بقي السعر دون المقاومة والمحور التشغيلي."
		tactical = "الأفضل هو التعامل مع الارتدادات كفرص متابعة هابطة بدل مطاردة السعر بعد التمدد."
	else:
		headline = f"الصورة الحالية على {symbol_label} ضمن إطار {interval} ما تزال محايدة."
		overview = "المؤشرات لا تعطي أفضلية اتجاهية كافية، لذلك قيمة الانتظار أعلى من قيمة الدخول المبكر."
		tactical = "الأفضل هو انتظار كسر مؤكد للنطاق الحالي قبل التحول إلى خطة هجومية أو دفاعية."

	conviction = f"درجة الثقة {confidence}، والتغير السعري الأخير {price_change_pct:.3f}%، بينما RSI عند {technical['rsi']} وMACD عند {technical['macd']}."
	return {
		"headline": headline,
		"overview": overview,
		"tactical_stance": tactical,
		"conviction_note": conviction,
	}


def _build_analyst_report(
	symbol_label: str,
	interval: str,
	recommendation: str,
	confidence: str,
	buy_score: int,
	sell_score: int,
	entry_point: float,
	stop_loss: float,
	take_profit1: float,
	take_profit2: float,
	take_profit3: float,
	price_change_pct: float,
	technical: dict,
	scenario: dict,
	executive_summary: dict,
) -> dict:
	bias = scenario["bias"]
	if bias == "صاعد":
		market_pulse = "الاتجاه المهيمن يميل إلى استمرار الصعود بشرط بقاء السعر فوق الدعم والمحور التشغيلي."
		desk_call = "أفضلية المكتب تميل إلى الشراء الانتقائي مع بناء مركز تدريجي وليس ملاحقة شموع التمدد."
		best_execution = "يفضل تنفيذ الدخول على عودة هادئة قرب منطقة المتابعة بدل الدخول بعد اندفاع سريع."
		invalid_context = f"أي إغلاق دون {stop_loss} يعني أن المحلل يلغي الانحياز الصاعد الحالي."
	elif bias == "هابط":
		market_pulse = "الضغط البيعي ما زال هو المسيطر، والارتدادات الحالية تُقرأ كتصحيحات داخل اتجاه أضعف."
		desk_call = "أفضلية المكتب تميل إلى البيع المنضبط عند الارتداد، مع تجنب فتح مراكز متأخرة بعد هبوط ممتد."
		best_execution = "يفضل تنفيذ البيع قرب إعادة الاختبار أو عند فشل السعر في تجاوز المقاومة القريبة."
		invalid_context = f"أي إغلاق فوق {stop_loss} يعني أن المحلل يوقف هذا السيناريو الهابط."
	else:
		market_pulse = "السوق متوازن حاليًا ولا توجد أفضلية اتجاهية كافية لبناء مركز هجومي."
		desk_call = "أفضلية المكتب هي الانتظار حتى يخرج السعر من النطاق مع تأكيد أوضح من الزخم."
		best_execution = "التنفيذ الأمثل هنا هو عدم الاستعجال وانتظار كسر أو إعادة اختبار مؤكدة."
		invalid_context = "في البيئة الحالية، الدخول قبل كسر النطاق يظل منخفض الجودة."

	indicator_biases = [
		{
			"name": "RSI 14",
			"state": "متوازن" if 45 <= technical["rsi"] <= 55 else ("داعم للصعود" if technical["rsi"] > 55 else "داعم للهبوط"),
			"comment": f"القيمة الحالية {technical['rsi']} تعطي قراءة زخم مباشرة.",
		},
		{
			"name": "MACD",
			"state": "إيجابي" if technical["macd"] >= technical["macd_signal"] else "سلبي",
			"comment": f"MACD عند {technical['macd']} مقابل إشارة {technical['macd_signal']}.",
		},
		{
			"name": "المتوسطات",
			"state": "اتجاه صاعد" if technical["sma20"] >= technical["sma50"] else "اتجاه هابط",
			"comment": f"SMA20 عند {technical['sma20']} مقابل SMA50 عند {technical['sma50']}.",
		},
		{
			"name": "الزخم القصير",
			"state": "نشط" if abs(technical["momentum_pct"]) >= 0.2 else "هادئ",
			"comment": f"تغير آخر 5 شموع يساوي {technical['momentum_pct']}%.",
		},
	]

	risk_flags = [
		f"الثقة الحالية {confidence}، لذلك لا يُفضَّل تكبير حجم الصفقة قبل ظهور متابعة سعرية واضحة.",
		f"نسبة العائد إلى المخاطرة الحالية تقارب {scenario['risk_reward_ratio']}:1 حتى الهدف الثاني.",
		invalid_context,
	]

	return {
		"headline": f"رأي المحلل على {symbol_label} ضمن إطار {interval}",
		"market_pulse": market_pulse,
		"desk_call": desk_call,
		"context_note": executive_summary["conviction_note"],
		"execution_plan": [
			f"الدخول المرجعي قرب {entry_point} مع متابعة السلوك السعري داخل منطقة السيناريو الأساسية.",
			f"تقليص المخاطرة أو جني جزء أول عند {take_profit1} ثم متابعة {take_profit2} و {take_profit3}.",
			best_execution,
		],
		"risk_flags": risk_flags,
		"indicator_biases": indicator_biases,
		"positioning": {
			"recommendation": recommendation,
			"confidence": confidence,
			"buy_score": buy_score,
			"sell_score": sell_score,
			"price_change_pct": round(price_change_pct, 3),
		},
		"levels": {
			"entry": entry_point,
			"stop_loss": stop_loss,
			"take_profit1": take_profit1,
			"take_profit2": take_profit2,
			"take_profit3": take_profit3,
			"support": scenario["levels"]["support"],
			"pivot": scenario["levels"]["pivot"],
			"resistance": scenario["levels"]["resistance"],
		},
	}


def _price_levels(entry_point: float, atr_value: float, direction: int, symbol: str, interval: str) -> tuple[float, float, float, float]:
	risk_multiplier = SUPPORTED_INTERVALS[interval]["risk_multiplier"]
	step = max(atr_value * risk_multiplier, entry_point * 0.0015)

	if direction >= 0:
		take_profit1 = entry_point + step
		take_profit2 = entry_point + (step * 1.8)
		take_profit3 = entry_point + (step * 2.6)
		stop_loss = entry_point - (step * 1.2)
	else:
		take_profit1 = entry_point - step
		take_profit2 = entry_point - (step * 1.8)
		take_profit3 = entry_point - (step * 2.6)
		stop_loss = entry_point + (step * 1.2)

	return (
		_round_price(take_profit1, symbol),
		_round_price(take_profit2, symbol),
		_round_price(take_profit3, symbol),
		_round_price(stop_loss, symbol),
	)


def _download_market_data(symbol: str, interval: str) -> pd.DataFrame:
	interval_info = SUPPORTED_INTERVALS[interval]
	ticker = SUPPORTED_SYMBOLS[symbol]["ticker"]
	data = yf.download(
		tickers=ticker,
		period=interval_info["period"],
		interval=interval_info["yf_interval"],
		auto_adjust=False,
		progress=False,
		threads=False,
	)
	if isinstance(data.columns, pd.MultiIndex):
		data.columns = data.columns.get_level_values(0)
	# Remove duplicate columns that yfinance may produce (e.g. 'Adj Close' & 'Close' both flattened)
	data = data.loc[:, ~data.columns.duplicated()]
	# Ensure core columns are 1-D Series
	for col in ("Open", "High", "Low", "Close", "Volume"):
		if col in data.columns and isinstance(data[col], pd.DataFrame):
			data[col] = data[col].iloc[:, 0]
	cleaned = data.dropna(subset=["Open", "High", "Low", "Close"])
	if interval == "4h":
		cleaned = cleaned.resample("4h").agg(
			{
				"Open": "first",
				"High": "max",
				"Low": "min",
				"Close": "last",
				"Adj Close": "last",
				"Volume": "sum",
			}
		).dropna(subset=["Open", "High", "Low", "Close"])
	return cleaned


def perform_full_analysis(symbol: str, interval: str) -> dict:
	"""Analyze a market using live data fetched from Yahoo Finance."""
	normalized_symbol = _normalize_symbol(symbol)
	normalized_interval = _normalize_interval(interval)

	if not normalized_symbol:
		return {"success": False, "error": "Symbol is required."}

	if normalized_symbol not in SUPPORTED_SYMBOLS:
		supported = ", ".join(SUPPORTED_SYMBOLS)
		return {"success": False, "error": f"Unsupported symbol '{symbol}'. Supported values: {supported}."}

	if normalized_interval not in SUPPORTED_INTERVALS:
		supported = ", ".join(SUPPORTED_INTERVALS)
		return {"success": False, "error": f"Unsupported interval '{interval}'. Supported values: {supported}."}

	try:
		market_data = _download_market_data(normalized_symbol, normalized_interval)
	except Exception as exc:
		return {
			"success": False,
			"symbol": normalized_symbol,
			"interval": normalized_interval,
			"error": f"Failed to fetch market data: {exc}",
		}

	if market_data.empty or len(market_data) < 60:
		return {
			"success": False,
			"symbol": normalized_symbol,
			"interval": normalized_interval,
			"error": "Not enough market data returned for analysis.",
		}

	buy_score, sell_score, details = _score_market(market_data)
	score_gap = buy_score - sell_score
	recommendation = _recommendation_from_gap(score_gap)
	confidence = _confidence_label(abs(score_gap))

	latest_close = float(market_data["Close"].iloc[-1])
	prev_close = float(market_data["Close"].iloc[-2])
	entry_point = _round_price(latest_close, normalized_symbol)
	price_change_pct = ((latest_close - prev_close) / prev_close) * 100
	direction = -1 if "بيع" in recommendation else 1
	take_profit1, take_profit2, take_profit3, stop_loss = _price_levels(
		entry_point,
		details["atr14"],
		direction,
		normalized_symbol,
		normalized_interval,
	)

	fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
	scenario = _build_professional_scenario(
		normalized_symbol,
		recommendation,
		entry_point,
		take_profit1,
		take_profit2,
		take_profit3,
		stop_loss,
		market_data,
		details["atr14"],
		confidence,
		details,
	)
	executive_summary = _build_executive_summary(
		SUPPORTED_SYMBOLS[normalized_symbol]["label"],
		normalized_interval,
		recommendation,
		confidence,
		scenario,
		price_change_pct,
		details,
	)
	scenario_horizons = _build_multi_horizon_scenarios(
		normalized_symbol,
		recommendation,
		entry_point,
		take_profit1,
		take_profit2,
		take_profit3,
		stop_loss,
		scenario,
		confidence,
	)
	analyst_report = _build_analyst_report(
		SUPPORTED_SYMBOLS[normalized_symbol]["label"],
		normalized_interval,
		recommendation,
		confidence,
		buy_score,
		sell_score,
		entry_point,
		stop_loss,
		take_profit1,
		take_profit2,
		take_profit3,
		price_change_pct,
		{
			"rsi": details["rsi"],
			"macd": details["macd"],
			"macd_signal": details["macd_signal"],
			"sma20": round(_round_price(details["sma20"], normalized_symbol), 5),
			"sma50": round(_round_price(details["sma50"], normalized_symbol), 5),
			"momentum_pct": details["momentum_pct"],
			"trend_pct_from_sma20": details["trend_pct_from_sma20"],
		},
		scenario,
		executive_summary,
	)
	return {
		"success": True,
		"symbol": normalized_symbol,
		"symbol_label": SUPPORTED_SYMBOLS[normalized_symbol]["label"],
		"interval": normalized_interval,
		"recommendation": recommendation,
		"buy_score": buy_score,
		"sell_score": sell_score,
		"entry_point": entry_point,
		"take_profit1": take_profit1,
		"take_profit2": take_profit2,
		"take_profit3": take_profit3,
		"stop_loss": stop_loss,
		"confidence": confidence,
		"price_change_pct": round(price_change_pct, 3),
		"data_source": "Yahoo Finance",
		"fetched_at": fetched_at,
		"signals": _build_signals(recommendation, buy_score, sell_score, details, price_change_pct),
		"executive_summary": executive_summary,
		"analyst_report": analyst_report,
		"scenario": scenario,
		"scenario_horizons": scenario_horizons,
		"technical": {
			"rsi": details["rsi"],
			"macd": details["macd"],
			"macd_signal": details["macd_signal"],
			"sma20": round(_round_price(details["sma20"], normalized_symbol), 5),
			"sma50": round(_round_price(details["sma50"], normalized_symbol), 5),
			"momentum_pct": details["momentum_pct"],
			"trend_pct_from_sma20": details["trend_pct_from_sma20"],
			"atr14": _round_price(details["atr14"], normalized_symbol),
		},
	}