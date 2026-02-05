@echo off
chcp 65001 > nul
setlocal

:: Usage: MAKE_ADMIN.bat <username>
if "%~1"=="" (
  echo Usage: MAKE_ADMIN.bat ^<username^>
  exit /b 1
)

set USERNAME=%~1

python - <<PY
import sys
from user_manager import user_manager
import sqlite3
from pathlib import Path

username = sys.argv[1]

# Lookup user id by username
conn = sqlite3.connect(str(Path(__file__).parent / 'users.db'))
cursor = conn.cursor()
cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
row = cursor.fetchone()
conn.close()

if not row:
    print(f'User not found: {username}')
    sys.exit(1)

user_id = row[0]
res = user_manager.set_admin_status(user_id, True)
print('Promoted to admin.' if res['success'] else 'Failed to promote.')
PY %USERNAME%

endlocal
