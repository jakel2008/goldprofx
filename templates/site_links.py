# قائمة روابط صفحات النظام GOLD PRO
# يمكن استيرادها في أي قالب Jinja2 عبر include أو import

links = [
    {"name": "الرئيسية", "url": "/", "icon": "🏠"},
    {"name": "لوحة التحكم", "url": "/dashboard", "icon": "📊"},
    {"name": "الإشارات", "url": "/signals", "icon": "📈"},
    {"name": "الصفقات", "url": "/trades", "icon": "💹"},
    {"name": "التقارير", "url": "/reports", "icon": "📑"},
    {"name": "الخطط", "url": "/plans", "icon": "💰"},
    {"name": "التعليم", "url": "/tutorials", "icon": "🎓", "auth": True},
    {"name": "اختيار الأزواج", "url": "/pairs-selection", "icon": "🎯"},
    {"name": "الملف الشخصي", "url": "/profile", "icon": "👤"},
    {"name": "التحكم المركزي", "url": "/master-dashboard", "icon": "🛠️", "auth": True},

    # روابط الأدمن فقط
    {"name": "لوحة الأدمن", "url": "/admin-panel", "icon": "🔐", "admin": True},
    {"name": "إدارة الاشتراكات", "url": "/subscriptions_management", "icon": "👥", "admin": True},
    {"name": "بوتات التداول", "url": "/bot-management", "icon": "🤖", "admin": True},
    {"name": "المحلل المتقدم", "url": "/advanced_analyzer", "icon": "🧠", "admin": True},

    # زر التحليل (الإشارات القوية) - إضافة منفصلة
    {"name": "التحليل", "url": "/forex-app/strong-signals", "icon": "📡"},

    # روابط الضيف فقط
    {"name": "تسجيل الدخول", "url": "/login?first=1", "icon": "🔓", "guest": True},
    {"name": "تسجيل جديد", "url": "/register?first=1", "icon": "✍️", "guest": True},

    # روابط المستخدم المسجل
    {"name": "خروج", "url": "/logout", "icon": "🚪", "auth": True}
]
