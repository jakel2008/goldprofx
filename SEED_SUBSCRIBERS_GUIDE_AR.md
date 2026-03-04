# دليل إعداد مشتركين افتراضيين (آمن) 

هذا الدليل يضيف مستخدمين افتراضيين لكل خطة **بدون حذف أي بيانات**، ويضمن التحقق أن التوصيات تصل حسب الخطة.

## 1) ماذا يفعل السكربت

الملف: `seed_default_subscribers_safe.py`

- يعمل `backup` تلقائي لـ:
  - `users.db`
  - `vip_subscriptions.db`
- يضيف/يحدّث فقط مستخدمي Seed المعروفين (Idempotent Upsert).
- لا ينفذ أي `DELETE` للمستخدمين.
- يربط بيانات المستخدم في:
  - قاعدة الموقع `users.db`
  - قاعدة البوت `vip_subscriptions.db`
- يطبع تقرير تحقق من الاستلام حسب جودة الإشارة والخطة.

## 2) القيم الجاهزة (الافتراضية)

- كلمة المرور الموحدة لمستخدمي Seed في الموقع:
  - `SeedUser#2026`

- مستخدم لكل خطة:
  - `seed_plan_free` → `seed.free@goldpro.local`
  - `seed_plan_bronze` → `seed.bronze@goldpro.local`
  - `seed_plan_silver` → `seed.silver@goldpro.local`
  - `seed_plan_gold` → `seed.gold@goldpro.local`
  - `seed_plan_platinum` → `seed.platinum@goldpro.local`

- Telegram/User IDs للبوت:
  - `990001 ... 990005`

## 3) التشغيل خطوة بخطوة

### الخطوة A: فحص بدون كتابة

```powershell
Set-Location "D:\GOLD PRO"
python seed_default_subscribers_safe.py --dry-run
```

### الخطوة B: تنفيذ فعلي مع نسخ احتياطية

```powershell
Set-Location "D:\GOLD PRO"
python seed_default_subscribers_safe.py
```

### الخطوة C: مراجعة النسخ الاحتياطية

تحقق من مجلد:

`D:\GOLD PRO\backups`

## 4) كيف تتأكد أن كل خطة تستقبل حسب صلاحيتها

بعد التشغيل، السكربت يطبع جدول `delivery-verification`.

المتوقع عادة:
- `free` يستقبل فقط الإشارات عالية الجودة غالبًا.
- `bronze/silver/gold/platinum` حسب العتبات في `telegram_sender.py`.
- يوجد أيضًا حد يومي حسب الخطة من `vip_subscription_system.py` (`signals_per_day`).

## 5) ضمان عدم مسح بيانات المستخدمين الجدد

هذا السكربت لا يحذف بيانات نهائيًا، ويعمل فقط على:
- إضافة مستخدم Seed غير موجود.
- تحديث مستخدم Seed إذا كان موجودًا مسبقًا.

لا يعدل المستخدمين الحقيقيين لأن المطابقة تتم على:
- بريد Seed المحدد في `users.db`.
- `user_id` محدد لمستخدمي Seed في `vip_subscriptions.db`.

## 6) استرجاع سريع إذا لزم

إذا احتجت rollback:
- أوقف الخدمة.
- استبدل `users.db` و`vip_subscriptions.db` بآخر نسخة من `backups`.
- شغّل الخدمة مرة أخرى.

## 7) ملاحظة تشغيل على Render

إن كنت تستخدم Render مع قرص دائم، تأكد أن التطبيق يقرأ نفس ملفات قواعد البيانات الموجودة على القرص الدائم.
