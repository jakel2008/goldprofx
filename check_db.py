import sqlite3

conn = sqlite3.connect('goldpro_system.db')
c = conn.cursor()

c.execute('SELECT id, name, price FROM plans')
print('Plans:')
for row in c.fetchall():
    print(f'  ID: {row[0]}, Name: {row[1]}, Price: {row[2]}')

c.execute('SELECT id, email, full_name, plan_id, is_active FROM users')
print('\nUsers:')
for row in c.fetchall():
    print(f'  ID: {row[0]}, Email: {row[1]}, Name: {row[2]}, Plan ID: {row[3]}, Active: {row[4]}')

conn.close()
