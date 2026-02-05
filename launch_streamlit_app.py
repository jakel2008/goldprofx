
import os
import subprocess

# تحديد مسار مجلد التطبيق
app_path = os.path.join(os.path.dirname(__file__), "forex_streamlit_app", "app.py")

# تشغيل Streamlit
subprocess.run(["streamlit", "run", app_path], shell=True)
