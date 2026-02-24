import sqlite3

# List of databases to update
DBS = [
    'users.db',
    'vip_subscriptions.db',
    'vip_signals.db',
]
USERNAME = 'jakel2008'

for db in DBS:
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute("UPDATE users SET is_admin=1, role='admin' WHERE username=?", (USERNAME,))
        conn.commit()
        print(f"Updated {db}")
    except Exception as e:
        print(f"Error updating {db}: {e}")
    finally:
        conn.close()