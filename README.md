# 🚀 GOLD PRO - نظام التداول المتقدم

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-green.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-red.svg)](https://flask.palletsprojects.com)

## 📊 نظام تداول شامل للعملات والمؤشرات

نظام GOLD PRO هو منصة تداول متكاملة توفر:
- 📡 بث إشارات تلقائي إلى Telegram
- 📊 تحليل مستمر لـ 49+ أزواج تداول
- 🌐 واجهة ويب تفاعلية
- 📈 تتبع الصفقات والأرباح
- 👥 نظام إدارة مستخدمين متعدد المستويات

---

## ✨ الميزات الرئيسية

### 🎯 التحليل المتقدم
- **49+ أزواج** مدعومة (FOREX, Indices, Metals, Crypto, Energy)
- **8+ استراتيجيات** تحليلية (ICT/SMC, RSI, MACD, EMA, Bollinger, Fibonacci)
- **تحديث مستمر** كل 5 دقائق
- **نسبة نجاح 81.9%** للإشارات

### 📡 البث التلقائي
- بث فوري إلى Telegram
- دعم 18 مستخدم نشط
- 5 مستويات اشتراك (Free, Bronze, Silver, Gold, Platinum)
- تنسيق احترافي مع Markdown

### 🌐 واجهة الويب
- لوحة تحكم تفاعلية
- عرض الإشارات الحية
- تتبع الصفقات النشطة
- تقارير الأداء

### 📊 التقارير
- تقارير ساعية تلقائية
- ملخصات يومية وأسبوعية
- إحصائيات الأرباح والخسائر
- تحليل الأداء

---

## 🚀 التشغيل السريع

### المتطلبات
```bash
Python 3.9+
Flask 2.0+
yfinance
ta (Technical Analysis)
requests
```

### التثبيت
```bash
# 1. استنساخ المستودع
git clone https://github.com/jakel2008/goldprofx.git
cd goldprofx

# 2. إنشاء بيئة افتراضية
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 3. تثبيت المتطلبات
pip install flask yfinance ta requests pandas schedule

# 4. بدء النظام
START_PRODUCTION.bat  # Windows
# أو
python web_app.py &
python signal_broadcaster.py &
python analyze_all_pairs.py &
```

### الوصول
- **واجهة الويب**: http://localhost:5000
- **البريد الإلكتروني**: test@goldpro.com
- **كلمة المرور**: Test123

---

## 📁 هيكل المشروع

```
goldprofx/
├── web_app.py                    # خادم Flask الرئيسي
├── signal_broadcaster.py         # نظام البث التلقائي
├── analyze_all_pairs.py          # محرك التحليل
├── auto_track_signals.py         # تتبع الصفقات
├── auto_reports_scheduler.py     # التقارير الدورية
│
├── analysis_engine.py            # محرك التحليل المتقدم
├── recommendations_engine.py     # نظام التوصيات
├── signal_formatter.py           # تنسيق الرسائل
├── vip_subscription_system.py   # إدارة الاشتراكات
│
├── templates/                    # قوالب HTML
├── signals/                      # الإشارات المولدة
├── recommendations/              # التوصيات
├── .github/                      # وثائق GitHub Copilot
│
├── goldpro_system.db            # قاعدة البيانات الرئيسية
├── vip_subscriptions.db         # قاعدة بيانات المستخدمين
│
├── START_PRODUCTION.bat         # تشغيل سريع
├── STOP_ALL.bat                 # إيقاف جميع الخدمات
└── PRODUCTION_README.md         # دليل الإنتاج

```

---

## 🎯 الأزواج المدعومة

### FOREX (28 أزواج)
**Major**: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, NZDUSD, USDCHF  
**Minor**: EURGBP, EURJPY, GBPJPY, EURCHF, AUDJPY, GBPAUD, EURAUD, GBPCAD  
**Cross**: CADJPY, CHFJPY, NZDJPY, AUDCAD, AUDCHF, AUDNZD, CADCHF, EURNZD, EURCAD, GBPNZD, GBPCHF, NZDCAD, NZDCHF

### US Indices (5)
US30 (Dow Jones), NAS100 (Nasdaq), SPX500 (S&P 500), RUSSELL 2000, VIX

### Metals (4)
XAUUSD (Gold), XAGUSD (Silver), XPTUSD (Platinum), XPDUSD (Palladium)

### Crypto (7)
BTCUSD, ETHUSD, BNBUSD, XRPUSD, ADAUSD, SOLUSD, DOGEUSD

### Energy (5)
CRUDE, BRENT, NATGAS, HEATING, GASOLINE

---

## 📈 الإحصائيات

- **الأزواج المدعومة**: 49+
- **المستخدمون النشطون**: 18
- **نسبة نجاح الصفقات**: 81.9%
- **صفقات نشطة**: 31
- **صفقات رابحة**: 136
- **صفقات خاسرة**: 30

---

## 🔧 الإعدادات

### متغيرات البيئة
```bash
MM_TELEGRAM_BOT_TOKEN=your_bot_token
MM_TELEGRAM_CHAT_ID=your_chat_id
```

### إضافة مستخدم جديد
```python
python admin_panel.py
# اختر "إضافة مستخدم جديد"
```

### تغيير إعدادات التحليل
عدّل `analyze_all_pairs.py`:
```python
ALL_PAIRS = {
    'SYMBOL': 'YFINANCE_TICKER',
    # أضف أزواج جديدة هنا
}
```

---

## 📝 الوثائق

- [دليل الإنتاج](PRODUCTION_README.md)
- [ملخص النظام](SYSTEM_STATUS_SUMMARY.py)
- [دليل Copilot](.github/copilot-instructions.md)

---

## 🤝 المساهمة

نرحب بالمساهمات! الرجاء:
1. عمل Fork للمشروع
2. إنشاء فرع للميزة (`git checkout -b feature/AmazingFeature`)
3. Commit التغييرات (`git commit -m 'Add AmazingFeature'`)
4. Push للفرع (`git push origin feature/AmazingFeature`)
5. فتح Pull Request

---

## 📄 الترخيص

هذا المشروع مرخص بموجب MIT License - انظر ملف [LICENSE](LICENSE) للتفاصيل.

---

## 📞 الدعم

- **Issues**: [GitHub Issues](https://github.com/jakel2008/goldprofx/issues)
- **البريد الإلكتروني**: support@goldpro.com

---

## 🙏 شكر خاص

- [yfinance](https://github.com/ranaroussi/yfinance) - بيانات السوق
- [ta](https://github.com/bukosabino/ta) - التحليل الفني
- [Flask](https://flask.palletsprojects.com) - إطار الويب

---

**✨ نظام GOLD PRO - جاهز للإنتاج!**
fx wep sit
