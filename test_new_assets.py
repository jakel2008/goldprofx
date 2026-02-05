# -*- coding: utf-8 -*-
import yfinance as yf
import os

os.system('chcp 65001 > nul')

print('✅ تحديث الأصول المالية - النتيجة النهائية:')
print('-' * 60)

assets = [
    ('الفضة', 'SLV'),
    ('النفط الخام', 'USO'),
    ('نفط برنت', 'BNO'),
    ('الغاز الطبيعي', 'UNG'),
    ('S&P 500', '^GSPC'),
    ('Dow Jones', '^DJI'),
    ('NASDAQ 100', '^NDX'),
    ('Russell 2000', '^RUT')
]

for name, ticker in assets:
    try:
        data = yf.download(ticker, period='1d', interval='5m', progress=False)
        status = '✅' if len(data) > 0 else '❌'
        print(f'{status} {name:20s} ({ticker:8s}): {len(data)} شمعة')
    except Exception as e:
        print(f'❌ {name:20s} ({ticker:8s}): خطأ - {str(e)[:30]}')

print('-' * 60)
print('📊 إجمالي الأصول في النظام: 22 أصل مالي')
print('   - 7 أزواج عملات رئيسية')
print('   - 2 معادن ثمينة (ذهب، فضة)')
print('   - 3 سلع طاقة (نفط خام، برنت، غاز)')
print('   - 4 مؤشرات أمريكية')
print('   - 6 عملات رقمية')
