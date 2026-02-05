
# Gold Analyzer Pro - دليل التشغيل الكامل

هذا الملف يحتوي على تعليمات تثبيت بايثون، إضافة المكتبات، تشغيل البرنامج، وتحويله إلى ملف تنفيذي (EXE).

---

## الخطوة 1: تثبيت Python
1. اذهب إلى: https://www.python.org/downloads/
2. اختر "Download Python 3.x.x for Windows"
3. أثناء التثبيت:
   - ضع علامة على "Add Python to PATH"
   - اختر "Install Now"
4. بعد التثبيت، افتح CMD واكتب:
   python --version
   إذا ظهرت النسخة، فأنت جاهز للخطوة التالية.

---

## الخطوة 2: تثبيت المكتبات المطلوبة
افتح CMD واكتب:

```
pip install yfinance
pip install ta
pip install pandas
pip install matplotlib
```

---

## الخطوة 3: تشغيل البرنامج
1. حمّل الملف Gold_Analyzer_GUI.py
2. افتح CMD وانتقل إلى المجلد:
   cd مسار\المجلد
3. شغّل البرنامج:
   python Gold_Analyzer_GUI.py

---

## الخطوة 4: تحويل البرنامج إلى .EXE (بدون الحاجة إلى بايثون عند المستخدم)
1. ثبّت أداة التحويل:
   pip install auto-py-to-exe

2. شغّلها:
   auto-py-to-exe

3. في الواجهة:
   - Browse لاختيار Gold_Analyzer_GUI.py
   - اختر "One File"
   - اختر "Window Based"
   - اضغط Convert

سيتم إنشاء ملف EXE داخل مجلد output، يمكن نقله وتشغيله على أي جهاز.

---

بالتوفيق في استخدام Gold Analyzer Pro
