@echo off
REM إعداد بيئة العمل
cd /d "%~dp0"

REM إنشاء ملف متطلبات
echo tk> requirements.txt
echo matplotlib>> requirements.txt
echo pandas>> requirements.txt
echo ta>> requirements.txt
echo requests>> requirements.txt
echo fpdf>> requirements.txt
echo psutil>> requirements.txt
echo Pillow>> requirements.txt

REM تثبيت المتطلبات
pip install -r requirements.txt

REM تحزيم البرنامج مع جميع الملفات المطلوبة
pyinstaller --noconfirm --onefile --windowed ^
  --add-data "clients_codes.json;." ^
  --add-data "DejaVuSansCondensed.ttf;." ^
  --add-data "DejaVuSansCondensed-Bold.ttf;." ^
  run_forex_analyzer.py

REM إعلام المستخدم
echo ---------------------------------------------
echo تم إنشاء الملف التنفيذي في مجلد dist
echo انسخ جميع الملفات المطلوبة (clients_codes.json, الخطوط, icon.ico) مع EXE إذا لم تدمج تلقائياً
pause