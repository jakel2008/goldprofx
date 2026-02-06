import sqlite3

conn = sqlite3.connect('goldpro_system.db')
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()

print(f'🗄️ الجداول المُنشأة: {len(tables)} جدول')
for t in tables:
    print(f'   ✓ {t[0]}')

# التحقق من الخطط
c.execute('SELECT name, price, description FROM plans')
plans = c.fetchall()
print(f'\n📋 الخطط المتاحة:')
for plan in plans:
    print(f'   ✓ {plan[0]}: ${plan[1]} - {plan[2]}')

conn.close()
print('\n✅ قاعدة البيانات جاهزة للاستخدام!')
