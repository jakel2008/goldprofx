# قائمة روابط صفحات النظام GOLD PRO
# يمكن استيرادها في أي قالب Jinja2 عبر include أو import

links = [
    {"name": "الرئيسية", "name_en": "Home", "url": "/", "icon": "🏠"},
    {"name": "لوحة التحكم", "name_en": "Dashboard", "url": "/dashboard", "icon": "📊"},
    {"name": "الإشارات", "name_en": "Signals", "url": "/signals", "icon": "📈"},
    {"name": "الصفقات", "name_en": "Trades", "url": "/trades", "icon": "💹"},
    {"name": "تحميل التطبيق", "name_en": "Download App", "url": "/download-app", "icon": "📲"},
    {"name": "التقارير", "name_en": "Reports", "url": "/reports", "icon": "📑"},
    {"name": "الخطط", "name_en": "Plans", "url": "/plans", "icon": "💰"},
    {"name": "التعليم", "name_en": "Tutorials", "url": "/tutorials", "icon": "🎓", "auth": True},
    {"name": "اختيار الأزواج", "name_en": "Pair Selection", "url": "/pairs-selection", "icon": "🎯"},
    {"name": "الملف الشخصي", "name_en": "Profile", "url": "/profile", "icon": "👤"},
    {"name": "التحكم المركزي", "name_en": "Central Control", "url": "/master-dashboard", "icon": "🛠️", "auth": True},

    # روابط الأدمن فقط
    {"name": "لوحة الأدمن", "name_en": "Admin Panel", "url": "/admin-panel", "icon": "🔐", "admin": True},
    {"name": "إدارة الاشتراكات", "name_en": "Subscriptions", "url": "/subscriptions_management", "icon": "👥", "admin": True},
    {"name": "بوتات التداول", "name_en": "Trading Bots", "url": "/bot-management", "icon": "🤖", "admin": True},
    {"name": "المحلل المتقدم", "name_en": "Advanced Analyzer", "url": "/advanced_analyzer", "icon": "🧠", "admin": True},

    # زر التحليل (الإشارات القوية) - إضافة منفصلة
    {"name": "التحليل", "name_en": "Analysis", "url": "/forex-app/strong-signals", "icon": "📡"},

    # روابط الضيف فقط
    {"name": "تسجيل الدخول", "name_en": "Login", "url": "/login?first=1", "icon": "🔓", "guest": True},
    {"name": "تسجيل جديد", "name_en": "Register", "url": "/register?first=1", "icon": "✍️", "guest": True},

    # روابط المستخدم المسجل
    {"name": "خروج", "name_en": "Logout", "url": "/logout", "icon": "🚪", "auth": True}
]
