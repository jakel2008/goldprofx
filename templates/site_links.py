# قائمة روابط صفحات النظام GOLD PRO
# يمكن استيرادها في أي قالب Jinja2 عبر include أو import

links = [
    {"name": "الرئيسية", "url": "/", "icon": "🏠"},
    {"name": "لوحة التحكم", "url": "/dashboard", "icon": "📊"},
    {"name": "الإشارات", "url": "/signals", "icon": "📈"},
    {"name": "الصفقات", "url": "/trades", "icon": "💹"},
    {"name": "الخطط", "url": "/plans", "icon": "💰"},
    {"name": "اختر خطتك", "url": "/payment_jordan", "icon": "🛒"},
    {"name": "الدفع الأردن", "url": "/payment_jordan", "icon": "💳"},
    {"name": "الدفع الدولي", "url": "/payment_international", "icon": "🌍"},
    {"name": "التقارير", "url": "/reports", "icon": "📑"},
    {"name": "الاشتراكات", "url": "/subscriptions_management", "icon": "👥"},
    {"name": "الملف الشخصي", "url": "/profile", "icon": "👤"},
    {"name": "بوتات التداول", "url": "/bot_management", "icon": "🤖"},
    {"name": "المحلل الذكي", "url": "/advanced_analyzer", "icon": "📈"},
    {"name": "الإدارة", "url": "/admin", "icon": "🔐", "admin": True},
    {"name": "تسجيل الدخول", "url": "/login", "icon": "🔓", "guest": True},
    {"name": "تسجيل جديد", "url": "/register", "icon": "✍️", "guest": True},
    {"name": "خروج", "url": "/logout", "icon": "🚪", "auth": True}
]
