# تشغيل استراتيجية GOLD_PRO Legacy Strong Signal

تم حفظ الاستراتيجية المشتركة هنا:

```text
accounts\strategy_gold_pro_tp_split_legacy_strong_signal_v1.json
```

## وضع حماية رأس المال الحالي

الاستراتيجية المحفوظة الآن مضبوطة لتقليل الخسائر والانتظار لفرص أقوى:

- مصدر تحليل الصفقات هو `advanced_analyzer` عبر `services.advanced_analyzer_engine.perform_full_analysis`.
- إشارات قوية فقط؛ الإشارات العادية لا تدخل.
- حد قوة الإشارة `min_score_gap = 45`.
- حد أقصى إعداد واحد مفتوح للحساب كله.
- إعداد واحد فقط لكل رمز، مع منع تكرار نفس الرمز أو نفس الفريم.
- تبريد 60 دقيقة بعد صفقة الرمز.
- إيقاف سريع بعد خسارة كاملة تقريبًا عبر `max_consecutive_losses = 3`.
- حد خسارة يومي `1%`، ولا يوجد قفل ربح يومي؛ التداول لا يتوقف بسبب تحقيق ربح.
- الذهب يحتاج توافق سياقين على الأقل من الفريمات الأعلى.
- لا يسمح بعكس فريمات الاتجاه الأعلى إلا إذا كانت الإشارة قوية جدًا `score_gap >= 55`.
- يتم تجنب دخول الذهب عند أطراف Bollinger الشديدة.
- تفعيل تأكيد حركة السعر اللحظية قبل التنفيذ.

ملاحظة: بسبب طريقة `GOLD_PRO_TP1/TP2/TP3` القديمة، كل إعداد واحد قد يظهر في MT5 كثلاث صفقات، لأن كل هدف له أمر مستقل. هذا مقصود للحفاظ على الطريقة القديمة، لكن النظام الآن يمنع تكرار إعدادات كثيرة لنفس الرمز.

هذا الملف يحتوي إعدادات التداول فقط، ولا يحتوي بيانات دخول المحفظة. بيانات كل محفظة تبقى داخل:

```text
accounts\اسم_المحفظة\wallet.json
```

## تشغيل المحفظة الحالية

من Terminal داخل VS Code، ومن مجلد المشروع `D:\GOLD PRO`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\RUN_LEGACY_STRONG_SIGNAL_WALLET.ps1 -AccountId account1_gold
```

أو من VS Code:

```text
Terminal > Run Task > run-legacy-strong-signal-account1
```

## تشغيل أكثر من محفظة بدون تعارض

لكل محفظة يجب أن يكون لها مجلد مستقل داخل `accounts`، مثل:

```text
accounts\account1_gold\wallet.json
accounts\account1_gold\runtime_state.json
accounts\account2_real\wallet.json
accounts\account2_real\runtime_state.json
```

شغّل كل محفظة في نافذة PowerShell مستقلة، مع `AccountId` مختلف:

```powershell
Start-Process powershell -ArgumentList @('-NoExit','-NoProfile','-ExecutionPolicy','Bypass','-File',"$PWD\RUN_LEGACY_STRONG_SIGNAL_WALLET.ps1",'-AccountId','account1_gold')
Start-Process powershell -ArgumentList @('-NoExit','-NoProfile','-ExecutionPolicy','Bypass','-File',"$PWD\RUN_LEGACY_STRONG_SIGNAL_WALLET.ps1",'-AccountId','account2_real')
```

إذا كان اسم مجلد المحفظة مختلفًا عن `AccountId`، مرر `AccountDir`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\RUN_LEGACY_STRONG_SIGNAL_WALLET.ps1 -AccountId wallet_2 -AccountDir accounts\account2_bitcoin
```

## شروط عدم التعارض

- لا تشغّل محفظتين بنفس `AccountId`؛ القفل سيكون بنفس الاسم.
- لا تجعل محفظتين تستخدمان نفس `runtime_state.json`.
- لا تجعل محفظتين تستخدمان نفس `wallet.json` إلا إذا كنت تقصد نفس الحساب فعلًا.
- الأفضل لكل محفظة MT5 terminal مستقل في `wallet.json` عبر قيمة `path` مختلفة، لأن تشغيل أكثر من حساب على نفس `terminal64.exe` قد يبدّل اتصال MT5 بين الحسابات.
- لا تشغّل استراتيجيتين على نفس حساب MT5 في نفس الوقت إلا إذا كنت متأكدًا من الفصل بين الرموز و`magic`.

ملف الاستراتيجية مشترك. إذا عدلت الملف المشترك، فكل المحافظ التي تعمل عليه ستقرأ التعديل في الدورات القادمة. إذا أردت إعدادات مختلفة لمحفظة معينة، انسخ ملف الاستراتيجية إلى مجلد المحفظة وشغّلها مع `-StrategyConfig` مختلف.
