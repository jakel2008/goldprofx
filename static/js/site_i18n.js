(function () {
    const cfg = window.GOLDPRO_I18N || {};
    const supported = Array.isArray(cfg.supported) ? cfg.supported : ["ar", "en"];
    const defaultLang = supported.includes("ar") ? "ar" : (supported[0] || "ar");
    const currentLang = (cfg.lang && supported.includes(cfg.lang)) ? cfg.lang : defaultLang;
    const hasServerLang = Boolean(cfg.lang && supported.includes(cfg.lang));
    const storageKey = "goldpro_ui_lang";
    let activeLang = (function () {
        try {
            const saved = localStorage.getItem(storageKey);
            if (hasServerLang) {
                return currentLang;
            }
            return supported.includes(saved) ? saved : currentLang;
        } catch (_err) {
            return currentLang;
        }
    })();

    const arToEn = {
        "العربية": "Arabic",
        "اللغة": "Language",
        "اختيار اللغة": "Choose Language",
        "تبديل القائمة": "Toggle Menu",
        "الإشعارات": "Notifications",
        "تفعيل": "Enable",
        "لا توجد إشعارات": "No notifications",
        "تحديد الكل كمقروء ✓": "Mark all as read ✓",
        "إغلاق التنبيه": "Close Alert",
        "فتح الدعم والمساعدة": "Open Help & Support",
        "الدعم والمساعدة": "Help & Support",
        "كيف نساعدك؟": "How can we help?",
        "اختر الطريقة المناسبة للتواصل معنا أو الوصول السريع لأهم الصفحات.": "Choose your preferred way to reach us or quickly access the most important pages.",
        "🌐 مركز الدعم الرسمي": "🌐 Official Support Hub",
        "📱 واتساب الدعم": "📱 Support WhatsApp",
        "📨 تليجرام الدعم": "📨 Support Telegram",
        "✉️ البريد الإلكتروني": "✉️ Email",
        "💳 صفحة الخطط والأسعار": "💳 Plans & Pricing",
        "👤 إدارة الحساب": "👤 Account Management",
        "✅ التسجيل الذاتي متاح. بعد إنشاء الحساب يجب تفعيله من الرابط المرسل إلى البريد الإلكتروني.": "✅ Self-registration is available. After creating your account, you must activate it using the link sent to your email.",
        "متوفرون يوميا للرد على استفسارات الاشتراك والتفعيل والدفع.": "We are available daily to answer subscription, activation, and payment questions.",
        "© 2026 GOLD PRO - جميع الحقوق محفوظة": "© 2026 GOLD PRO - All rights reserved",
        "جميع الحقوق محفوظة": "All rights reserved",
        "تسجيل الدخول": "Login",
        "🔐 تسجيل الدخول": "🔐 Login",
        "تسجيل لأول مرة": "Register",
        "إنشاء حساب": "Create Account",
        "سجل الآن": "Sign up now",
        "نسيت كلمة المرور؟": "Forgot password?",
        "إعادة إرسال رابط التفعيل": "Resend activation link",
        "أدخل بيانات دخولك": "Enter your login details",
        "اسم المستخدم أو البريد الإلكتروني": "Username or Email",
        "كلمة المرور": "Password",
        "تذكرني": "Remember me",
        "دخول": "Login",
        "تسجيل جديد": "New Registration",
        "إنشاء حساب جديد": "Create a New Account",
        "✍️ إنشاء حساب جديد": "✍️ Create a New Account",
        "أدخل بياناتك لإنشاء حسابك الأول.": "Enter your details to create your first account.",
        "ليس لديك حساب؟": "Don't have an account?",
        "لديك حساب بالفعل؟": "Already have an account?",
        "لم يصلك بريد التفعيل؟": "Didn't receive the activation email?",
        "إعادة إرسال الرابط": "Resend link",
        "الاسم الكامل": "Full Name",
        "اسم المستخدم": "Username",
        "البريد الإلكتروني": "Email",
        "رقم الهاتف أو واتساب (اختياري)": "Phone or WhatsApp (Optional)",
        "مثال: 009627XXXXXXXX": "Example: 009627XXXXXXXX",
        "تأكيد كلمة المرور": "Confirm Password",
        "🎯 مزايا الحساب": "🎯 Account Features",
        "✅ تتبع الإشارات والصفقات": "✅ Track signals and trades",
        "✅ الوصول إلى الخطط المميزة": "✅ Access premium plans",
        "✅ لوحة تحكم شخصية": "✅ Personal dashboard",
        "✅ إشعارات فورية": "✅ Instant notifications",
        "✅ دعم العملاء 24/7": "✅ 24/7 customer support",
        "أوافق على استقبال تحديثات الموقع والعروض عبر البريد الإلكتروني": "I agree to receive site updates and offers by email",
        "أوافق على استخدام رقم الهاتف للتواصل عبر واتساب عند الحاجة": "I agree to use my phone number for WhatsApp communication when needed",
        "أوافق على الشروط والأحكام": "I agree to the terms and conditions",
        "إنشاء الحساب": "Create Account",
        "الصفحة الرئيسية": "Home",
        "الخطط والأسعار": "Plans & Pricing",
        "جاهز للبدء؟": "Ready to start?",
        "ابدأ الآن": "Start now",
        "اشترك الآن": "Subscribe now",
        "الأخبار العاجلة": "Breaking News",
        "🌍 اقتصاد مباشر": "🌍 Live Economy",
        "أخبار المنصة": "Platform News",
        "🏛️ أخبار المنصة": "🏛️ Platform News",
        "منصة GOLD PRO": "GOLD PRO Platform",
        "منصة تداول وإشارات احترافية قبل تسجيل الدخول يمكنك تصفح الإعلانات والعروض، ثم الدخول أو إنشاء حساب لأول مرة.": "A professional trading and signals platform. Before logging in, you can browse announcements and offers, then sign in or create your first account.",
        "الإعلانات والعروض": "Announcements & Offers",
        "عرض خاص": "Special Offer",
        "عرض عاجل محدث من الأدمن": "Urgent offer updated by admin",
        "لفترة محدودة، اشترك الآن بخطة Silver واستفد من تحليل متقدم وإشارات يومية.": "For a limited time, subscribe to the Silver plan and benefit from advanced analysis and daily signals.",
        "إعلان": "Announcement",
        "جلسة تعريف مجانية للمستخدمين الجدد": "Free onboarding session for new users",
        "تعرف على آلية العمل، إدارة المخاطر، وكيفية الاستفادة من التقارير والإشارات.": "Learn the workflow, risk management, and how to benefit from reports and signals.",
        "تنبيه": "Alert",
        "تحديثات يومية على الأزواج الرئيسية": "Daily updates on major pairs",
        "تحليلات محدثة على أزواج الفوركس الرئيسية مع توصيات قابلة للمتابعة.": "Updated analysis on major forex pairs with actionable recommendations.",
        "جديد": "New",
        "متابعة الأداء الأسبوعي": "Weekly performance tracking",
        "اطلع على التقارير والإحصائيات الدورية لتحسين قراراتك في التداول.": "Review periodic reports and statistics to improve your trading decisions.",
        "جاهز للبدء؟": "Ready to start?",
        "أنشئ حسابك الآن وابدأ متابعة الإشارات والتقارير.": "Create your account now and start following signals and reports.",
        "جاري تحميل الأخبار العاجلة...": "Loading breaking news...",
        "جاري تحميل أخبار المنصة...": "Loading platform news...",
        "لا توجد أخبار اقتصادية عاجلة حالياً": "No urgent economic news right now",
        "تعذر تحميل الأخبار الاقتصادية حالياً": "Unable to load economic news right now",
        "لا توجد أخبار جديدة من المنصة حالياً": "No new platform news right now",
        "تعذر تحميل أخبار المنصة حالياً": "Unable to load platform news right now",
        "عرض الخطط": "View Plans",
        "الخطط": "Plans",
        "الاشتراكات": "Subscriptions",
        "التقارير": "Reports",
        "الإشارات": "Signals",
        "الملف الشخصي": "Profile",
        "تسجيل الخروج": "Logout"
        ,"الصفحة غير موجودة": "Page not found"
        ,"عذراً، الصفحة التي تبحث عنها غير متاحة": "Sorry, the page you are looking for is unavailable"
        ,"يمكنك:": "You can:"
        ,"العودة إلى الرئيسية": "Back to home"
        ,"عرض الإشارات": "View signals"
        ,"خطط الاشتراك المرنة - كلما طالت المدة زاد التوفير": "Flexible subscription plans - the longer the term, the greater the savings"
        ,"اختر مدة الاشتراك": "Choose the subscription duration"
        ,"مدة الاشتراك": "Subscription duration"
        ,"شهر واحد": "One month"
        ,"3 أشهر": "3 months"
        ,"6 أشهر": "6 months"
        ,"12 شهر (سنة)": "12 months (year)"
        ,"الخطة": "Plan"
        ,"برونزي": "Bronze"
        ,"فضي": "Silver"
        ,"ذهبي": "Gold"
        ,"بلاتينيوم": "Platinum"
        ,"الأكثر طلبا": "Most requested"
        ,"أفضل قيمة": "Best value"
        ,"لمدة شهر واحد": "For one month"
        ,"3 إشارات يوميا": "3 signals per day"
        ,"5 إشارات يوميا": "5 signals per day"
        ,"7 إشارات يوميا": "7 signals per day"
        ,"10 إشارات يوميا": "10 signals per day"
        ,"جودة عالية ومتوسطة": "High and medium quality"
        ,"أزواج فوركس رئيسية": "Major forex pairs"
        ,"تغطية أوسع للأسواق": "Wider market coverage"
        ,"دعم أولوية": "Priority support"
        ,"دخول VIP للتحليلات": "VIP access to analysis"
        ,"أولوية عالية في التنبيهات": "High priority alerts"
        ,"دعم VIP مباشر": "Live VIP support"
        ,"أولوية قصوى لكل التنبيهات": "Maximum priority for all alerts"
        ,"خطة مجانية:": "Free plan:"
        ,"5 إشارات يومية للتجربة.": "5 daily trial signals."
        ,"للترقية اختر أي باقة مدفوعة من الأعلى.": "To upgrade, choose any paid package above."
        ,"استعادة كلمة المرور": "Password Reset"
        ,"🔐 استعادة كلمة المرور": "🔐 Password Reset"
        ,"أدخل بريدك الإلكتروني لنرسل لك رابط إعادة التعيين.": "Enter your email and we will send you a reset link."
        ,"إرسال رابط الاستعادة": "Send reset link"
        ,"العودة لتسجيل الدخول": "Back to login"
        ,"Resend activation": "Resend activation"
        ,"🔁 إعادة إرسال رابط التفعيل": "🔁 Resend activation link"
        ,"أدخل البريد الإلكتروني أو اسم المستخدم وسنرسل رابط تفعيل جديد إذا كان الحساب غير مفعل.": "Enter your email or username and we will send a new activation link if your account is not activated."
        ,"البريد الإلكتروني أو اسم المستخدم": "Email or username"
        ,"إرسال رابط جديد": "Send new link"
        ,"العودة إلى تسجيل الدخول": "Back to login"
        ,"Silver / فضي": "Silver"
        ,"Bronze / برونزي": "Bronze"
        ,"Gold VIP / ذهبي": "Gold VIP"
        ,"Platinum / بلاتينيوم": "Platinum"
        ,"ذهبي VIP": "Gold VIP"
        ,"لوحة التحكم المركزية": "Central control panel"
        ,"النظام يعمل": "The system works"
        ,"تطبيق الويب": "Web application"
        ,"بوت تليجرام": "Telegram bot"
        ,"نظام البث": "Broadcast system"
        ,"المجدول": "Scheduler"
        ,"إجمالي المشتركين": "Total subscribers"
        ,"الإشارات المرسلة اليوم": "Signals sent today"
        ,"الصفقات النشطة": "Active trades"
        ,"معدل النجاح": "Success rate"
        ,"سجل النظام": "System log"
        ,"آخر التحليلات": "Latest analysis"
        ,"لا توجد تحليلات حديثة": "There are no recent analyses"
        ,"صحة أرشيف الصفقات": "Validity of transaction archive"
        ,"المغلقة الخام": "Closed raw"
        ,"المغلقة الفعلية": "Actual closed"
        ,"المكرر المحذوف": "Deleted duplicate"
        ,"إجمالي المغلقة": "Total closed"
        ,"الرابحة": "Winning"
        ,"الخاسرة": "Losing"
        ,"مصدر الأرشيف": "Archive source"
        ,"تشغيل": "Run"
        ,"إيقاف": "Stop"
        ,"توليد الآن": "Generate now"
        ,"تحليل فوري (Force Live)": "Force Live analysis"
        ,"تشغيل التحليل الآن": "Run the analysis now"
        ,"فحص مصادر البيانات": "Check data sources"
        ,"آخر تشغيل": "Last run"
        ,"إدارة الاشتراكات": "Subscription management"
        ,"إجمالي الاشتراكات": "Total subscriptions"
        ,"اشتراكات نشطة": "Active subscriptions"
        ,"اشتراكات منتهية": "Expired subscriptions"
        ,"في الانتظار": "Pending"
        ,"الكل": "All"
        ,"نشط": "Active"
        ,"منتهي": "Expired"
        ,"ملغي": "Cancelled"
        ,"قيد الانتظار": "Pending"
        ,"استيراد نسخة احتياطية": "Import backup"
        ,"مراسلات العملاء": "Customer communications"
        ,"العودة للوحة الإدارة": "Back to admin panel"
        ,"تحديث": "Refresh"
        ,"ابحث عن مستخدم... (اسم، معرف، خطة)": "Search for a user... (name, id, plan)"
        ,"غير نشط الآن": "Inactive now"
        ,"بداية": "Start"
        ,"نهاية": "End"
        ,"آخر ظهور": "Last seen"
        ,"لا يوجد ظهور حديث": "No recent activity"
        ,"آخر تسجيل دخول": "Last login"
        ,"كود الإحالة": "Referral code"
        ,"ترقية/تغيير": "Upgrade/Change"
        ,"تمديد": "Extend"
        ,"إلغاء": "Cancel"
        ,"غير محدد": "Not set"
        ,"بداية:": "Start:"
        ,"نهاية:": "End:"
        ,"آخر ظهور:": "Last seen:"
        ,"آخر تسجيل دخول:": "Last login:"
        ,"كود الإحالة:": "Referral code:"
        ,"التقرير يومي الاحترافي": "Professional daily report"
        ,"التقرير يومي - GOLD PRO": "Daily report - GOLD PRO"
        ,"وقت الإنشاء": "Creation time"
        ,"الملخص التنفيذي": "Executive summary"
        ,"مقارنة بالفترة السابقة": "Comparison with the previous period"
        ,"أفضل الأزواج": "Best pairs"
        ,"الأطر الزمنية الأفضل": "Best time frames"
        ,"آخر الإغلاقات": "Latest closures"
        ,"صفقة": "trade"
        ,"الإجمالي الخام المدمج": "Total merged raw"
        ,"المكرر الذي تمت إزالته": "Removed duplicates"
        ,"المصدر الفعلي المستخدم": "Actual source used"
        ,"تم تحديث البيانات بنجاح": "Data updated successfully"
        ,"بدء التحليل التلقائي...": "Starting automatic analysis..."
        ,"تم بث إشارة جديدة للمشتركين": "A new signal was broadcast to subscribers"
        ,"تم تحليل EUR/USD بنجاح": "EUR/USD analyzed successfully"
        ,"النظام جاهز للعمل": "The system is up and running"
        ,"السعر الحالي": "Current price"
        ,"نقطة": "pip"
        ,"جودة:": "Quality:"
        ,"إشارة": "Signal"
        ,"التحديث بعد:": "Next update:"
        ,"ثانية": "seconds"
        ,"منصة إشارات وتحليلات بواجهة موحّدة وهوية ذهبية احترافية": "A signals and analytics platform with a unified interface and a professional golden identity"
        ,"الإشارات المباشرة": "Direct signals"
        ,"الخطط والاشتراكات": "Plans and subscriptions"
        ,"إجمالي الإشارات": "Total signals"
        ,"إجمالي التوصيات": "Total recommendations"
        ,"حالة الجلسة": "Session state"
        ,"نشطة": "Active"
        ,"المستخدم الحالي": "Current user"
        ,"الإحصائيات والتقارير المتقدمة": "Advanced statistics and reports"
        ,"تصدير": "Export"
        ,"يومي": "Daily"
        ,"أسبوعي": "Weekly"
        ,"شهري": "Monthly"
        ,"الفترة": "Period"
        ,"آخر تحديث": "Last update"
        ,"الصفقات المغلقة في الفترة": "Closed trades in the period"
        ,"الصفقات الرابحة": "Winning trades"
        ,"الصفقات الخاسرة": "Losing trades"
        ,"لوحة تحكم المشرف": "Admin control panel"
        ,"إدارة وتوزيع الإشارات والتقارير عبر التليجرام": "Manage and distribute signals and reports via Telegram"
        ,"المحلل المتقدم": "Advanced analyst"
        ,"محلل الفوركس": "Forex analyst"
        ,"إدارة الأدمن": "Admin management"
        ,"التحكم المركزي": "Central control"
        ,"إدارة البوتات": "Bot management"
        ,"إجمالي المستخدمين": "Total users"
        ,"المستخدمون النشطون": "Active users"
        ,"إجمالي الإشارات": "Total signals"
        ,"لوحة متابعة الصفقات": "Trades tracking dashboard"
        ,"تحديث تلقائي كل 20 ثانية - عرض الصفقات النشطة والرابحة والخاسرة": "Automatic refresh every 20 seconds - view active, winning, and losing trades"
        ,"إجمالي الصفقات": "Total trades"
        ,"رابحة": "Winning"
        ,"خاسرة": "Losing"
        ,"صافي الربح (%)": "Net profit (%)"
        ,"صفقات مؤرشفة": "Archived trades"
        ,"الرئيسية المحلل محاكي التداول الإشارات القوية تحليل مباشر": "Home Analyst Trade simulator Strong signals Live analysis"
        ,"قراءة فنية شاملة تتضمن التوصية الحالية، التقييم العددي، مستويات التداول، والسيناريوهات التنفيذية": "A comprehensive technical reading that includes the current recommendation, numerical assessment, trading levels, and execution scenarios"
        ,"بحث داخل الرموز": "Search symbols"
        ,"الرمز": "Symbol"
        ,"الإطار الزمني": "Timeframe"
        ,"مسح البحث": "Clear search"
        ,"تحديث التحليل": "Refresh analysis"
        ,"التوصية": "Recommendation"
        ,"بيع قوي": "Strong sell"
        ,"درجة الثقة": "Confidence level"
        ,"مرتفعة": "High"
        ,"قوة الشراء": "Buy strength"
        ,"البيع": "Sell"
        ,"اختبار التداول المباشر": "Live trading test"
        ,"اختصار Force Live": "Force Live shortcut"
        ,"تشغيل تحليل فوري مع خيار تجاوز الكاش، أو فحص مصدر البيانات الحي مباشرة": "Run real-time analysis with cache bypass, or inspect the live data source directly"
        ,"تجاوز الكاش (Force Live)": "Bypass cache (Force Live)"
        ,"فحص المصادر": "Check sources"
        ,"إرسال الإشارات": "Send signals"
        ,"إرسال التوصيات": "Send recommendations"
        ,"إرسال التقارير": "Send reports"
        ,"رسالة عامة": "General message"
        ,"الدفع والدعم": "Payment and support"
        ,"إرسال الإشارات إلى التليجرام": "Send signals to Telegram"
        ,"اختر إشارة لإرسالها إلى جميع المشتركين النشطين": "Choose a signal to send to all active subscribers"
        ,"لا توجد إشارات متاحة حالياً": "No signals currently available"
        ,"العودة للرئيسية": "Back to home"
        ,"المحلل": "Analyst"
        ,"التحليل الكامل": "Full analysis"
        ,"ماسح الإشارات القوية": "Strong signal scanner"
        ,"كل الأسواق": "All markets"
        ,"هذه الصفحة تفحص السوق أو الرمز المحدد وتعرض فقط الإشارات التي خرجت من نظام البحث بتوصية شراء قوي أو بيع قوي. عند اختيار كل الأسواق، يتم التحديث الآلي بشكل دوري.": "This page scans the selected market or symbol and shows only signals that reached a strong buy or strong sell recommendation. When All Markets is selected, it refreshes automatically on a schedule."
        ,"عند اختيار كل الأسواق، يتم التحديث الآلي بشكل دوري": "When All Markets is selected, it refreshes automatically on a schedule"
        ,"بحث داخل الرموز": "Search symbols"
        ,"الرمز": "Symbol"
        ,"الإطار الزمني": "Timeframe"
        ,"مسح البحث": "Clear search"
        ,"تشغيل البحث": "Run search"
        ,"ملخص الفحص": "Scan summary"
        ,"تم العثور على": "Found"
        ,"إشارة قوية": "strong signal"
        ,"نطاق البحث:": "Search scope:"
        ,"عدد الرموز المفحوصة:": "Number of scanned symbols:"
        ,"حالة نظام البحث": "Scan status"
        ,"تعرض الصفحة فقط النتائج التي بلغت مستوى قوة كافٍ داخل المحرك.": "This page only shows results that reached a sufficient strength level in the engine."
        ,"الرموز التي لم تنتج شراء قوي أو بيع قوي لا تظهر في هذه الصفحة.": "Symbols that did not produce a strong buy or strong sell do not appear on this page."
        ,"أخطاء الفحص:": "Scan errors:"
        ,"آخر فحص:": "Last scan:"
        ,"الوضع الحالي:": "Current mode:"
        ,"فحص تلقائي لجميع الأزواج": "Automatic scan for all pairs"
        ,"التحديث التالي:": "Next refresh:"
        ,"ثانية": "seconds"
        ,"إشعارات المتصفح:": "Browser notifications:"
        ,"مفعلة": "Enabled"
        ,"تفعيل الإشعارات": "Enable notifications"
        ,"إيقاف التحديث الآلي": "Stop auto-refresh"
        ,"كل الفئات": "All categories"
        ,"الأزواج الرئيسية": "Major pairs"
        ,"الأزواج التقاطعية": "Cross pairs"
        ,"المؤشرات الأمريكية": "US indices"
        ,"العملات المشفرة": "Cryptocurrencies"
        ,"المعادن": "Metals"
        ,"الأفضل الآن": "Top pick now"
        ,"الترتيب:": "Rank:"
        ,"قوة الشراء:": "Buy strength:"
        ,"قوة البيع:": "Sell strength:"
        ,"فارق القوة:": "Strength gap:"
        ,"التغير الأخير:": "Recent change:"
        ,"الدخول:": "Entry:"
        ,"وقف الخسارة:": "Stop loss:"
        ,"الثقة:": "Confidence:"
        ,"السيناريو:": "Scenario:"
        ,"خلاصة سريعة:": "Quick summary:"
        ,"فتح المحاكاة على هذه الإشارة": "Open simulator on this signal"
        ,"لا توجد إشارة قوية حالياً": "No strong signal right now"
        ,"أثناء الفحص": "Scan errors"
        ,"آخر إشارة لكل زوج": "Latest signal per pair"
        ,"لا توجد إشارات محفوظة بعد لهذا النطاق.": "No saved signals yet for this scope."
        ,"تم رصد إشارة قوية جديدة": "A new strong signal was detected"
        ,"تم رصد إشارة جديدة": "A new signal was detected"
        ,"سيتم عرض تفاصيل الإشارة الجديدة هنا.": "The new signal details will appear here."
        ,"تم تفعيل إشعارات المتصفح": "Browser notifications enabled"
        ,"سيصلك إشعار حقيقي عند ظهور إشارة قوية جديدة.": "You'll receive a real notification when a new strong signal appears."
        ,"إشارة قوية جديدة": "New strong signal"
        ,"غير مدعومة": "Not supported"
        ,"مرفوضة": "Denied"
        ,"بانتظار الإذن": "Awaiting permission"
        ,"متاحة عند اختيار كل الأسواق": "Available when All Markets is selected"
        ,"متوقف": "Stopped"
        ,"تعذر تحديث نتائج الإشارات القوية.": "Unable to refresh strong signal results."
        ,"تعذر تحديث الفحص": "Unable to refresh scan"
        ,"حدث خطأ أثناء جلب النتائج الجديدة.": "An error occurred while fetching new results."
        ,"توصية": "Recommendation"
        ,"شراء قوي": "Strong buy"
        ,"شراء": "Buy"
        ,"بيع قوي": "Strong sell"
        ,"بيع": "Sell"
        ,"انتظار": "Wait"
        ,"الرابحة": "Winning"
        ,"الخاسرة": "Losing"
        ,"إرسال": "Send"
    };

    const enToAr = Object.keys(arToEn).reduce(function (acc, key) {
        acc[arToEn[key]] = key;
        return acc;
    }, {});

    const dynamicTranslations = {
        en: {},
        ar: {}
    };

    const sortedStaticKeys = {
        en: Object.keys(arToEn).sort(function (a, b) { return b.length - a.length; }),
        ar: Object.keys(enToAr).sort(function (a, b) { return b.length - a.length; })
    };

    function normalizeSpaces(text) {
        return String(text || "").replace(/\s+/g, " ").trim();
    }

    function translateText(rawText, targetLang) {
        if (!rawText || !rawText.trim()) {
            return rawText;
        }

        const leading = rawText.match(/^\s*/)[0] || "";
        const trailing = rawText.match(/\s*$/)[0] || "";
        const core = normalizeSpaces(rawText);

        const lookup = targetLang === "en" ? arToEn : enToAr;
        const dynamicLookup = dynamicTranslations[targetLang] || {};
        if (Object.prototype.hasOwnProperty.call(lookup, core)) {
            return leading + lookup[core] + trailing;
        }
        if (Object.prototype.hasOwnProperty.call(dynamicLookup, core)) {
            return leading + dynamicLookup[core] + trailing;
        }

        let partial = core;
        const staticKeys = sortedStaticKeys[targetLang] || [];
        for (let i = 0; i < staticKeys.length; i += 1) {
            const key = staticKeys[i];
            const isPhrase = key.length >= 6 && /\s|[:()\-]/.test(key);
            if (!isPhrase) {
                continue;
            }
            if (!key || partial.indexOf(key) === -1) {
                continue;
            }
            partial = partial.split(key).join(lookup[key]);
        }

        const dynamicKeys = Object.keys(dynamicLookup || {}).sort(function (a, b) { return b.length - a.length; });
        for (let i = 0; i < dynamicKeys.length; i += 1) {
            const key = dynamicKeys[i];
            const isPhrase = key.length >= 6 && /\s|[:()\-]/.test(key);
            if (!isPhrase) {
                continue;
            }
            if (!key || partial.indexOf(key) === -1) {
                continue;
            }
            partial = partial.split(key).join(dynamicLookup[key]);
        }

        if (partial !== core) {
            return leading + partial + trailing;
        }

        if (!Object.prototype.hasOwnProperty.call(lookup, core)) {
            return rawText;
        }

        return rawText;
    }

    function shouldAutoTranslate(core, targetLang) {
        const text = String(core || "").trim();
        if (!text || text.length > 1200) {
            return false;
        }

        const hasArabic = /[\u0600-\u06FF]/.test(text);
        const hasLatin = /[A-Za-z]/.test(text);

        if (targetLang === "en") {
            return hasArabic;
        }
        if (targetLang === "ar") {
            return hasLatin;
        }
        return false;
    }

    function requestDynamicTranslations(texts, targetLang) {
        if (!Array.isArray(texts) || texts.length === 0) {
            return Promise.resolve({});
        }

        const batchedTexts = texts.slice(0, 80);

        const sourceLang = targetLang === "en" ? "ar" : "en";
        return fetch("/api/translate-ui", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                source: sourceLang,
                target: targetLang,
                texts: batchedTexts
            })
        })
            .then(function (res) {
                return res.ok ? res.json() : Promise.reject(new Error("dynamic translation failed"));
            })
            .then(function (payload) {
                if (!payload || !payload.success || !payload.translations) {
                    return {};
                }
                const bucket = dynamicTranslations[targetLang] || (dynamicTranslations[targetLang] = {});
                Object.keys(payload.translations).forEach(function (k) {
                    const value = String(payload.translations[k] || "").trim();
                    if (value) {
                        bucket[k] = value;
                    }
                });
                return payload.translations;
            })
            .catch(function () {
                return {};
            });
    }

    function shouldSkipTextNode(node) {
        if (!node || !node.parentElement) {
            return true;
        }
        const tag = (node.parentElement.tagName || "").toLowerCase();
        return ["script", "style", "noscript", "code", "pre"].includes(tag);
    }

    function applyLanguage(targetLang) {
        const lang = supported.includes(targetLang) ? targetLang : defaultLang;
        activeLang = lang;
        try {
            localStorage.setItem(storageKey, lang);
        } catch (_err) {
            // Ignore storage errors (private mode, disabled storage).
        }
        const dir = lang === "ar" ? "rtl" : "ltr";
        const pending = new Map();

        document.documentElement.lang = lang;
        document.documentElement.dir = dir;
        if (document.body) {
            document.body.style.direction = dir;
        }

        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
        const nodes = [];
        while (walker.nextNode()) {
            nodes.push(walker.currentNode);
        }
        nodes.forEach(function (node) {
            if (shouldSkipTextNode(node)) {
                return;
            }
            const raw = node.nodeValue;
            const translated = translateText(raw, lang);
            if (translated !== raw) {
                node.nodeValue = translated;
            }

            const candidate = translated !== raw ? translated : raw;
            const leading = candidate.match(/^\s*/)[0] || "";
            const trailing = candidate.match(/\s*$/)[0] || "";
            const core = normalizeSpaces(candidate);
            if (!shouldAutoTranslate(core, lang)) {
                return;
            }

            if (!pending.has(core)) {
                pending.set(core, []);
            }
            pending.get(core).push(function (translatedCore) {
                node.nodeValue = leading + translatedCore + trailing;
            });
        });

        const attrs = ["placeholder", "title", "aria-label"];
        attrs.forEach(function (attrName) {
            document.querySelectorAll("[" + attrName + "]").forEach(function (el) {
                const value = el.getAttribute(attrName);
                const translated = translateText(value, lang);
                if (translated !== value) {
                    el.setAttribute(attrName, translated);
                }

                const candidate = translated !== value ? translated : value;
                const core = normalizeSpaces(candidate);
                if (!shouldAutoTranslate(core, lang)) {
                    return;
                }
                if (!pending.has(core)) {
                    pending.set(core, []);
                }
                pending.get(core).push(function (translatedCore) {
                    el.setAttribute(attrName, translatedCore);
                });
            });
        });

        document.querySelectorAll("input[type='button'], input[type='submit'], button[value]").forEach(function (el) {
            const value = el.value;
            const translated = translateText(value, lang);
            if (translated !== value) {
                el.value = translated;
            }

            const candidate = translated !== value ? translated : value;
            const core = normalizeSpaces(candidate);
            if (!shouldAutoTranslate(core, lang)) {
                return;
            }
            if (!pending.has(core)) {
                pending.set(core, []);
            }
            pending.get(core).push(function (translatedCore) {
                el.value = translatedCore;
            });
        });

        const titleTranslated = translateText(document.title, lang);
        if (titleTranslated !== document.title) {
            document.title = titleTranslated;
        }

        const titleCandidate = titleTranslated !== document.title ? titleTranslated : document.title;
        const titleCore = normalizeSpaces(titleCandidate);
        if (shouldAutoTranslate(titleCore, lang)) {
            if (!pending.has(titleCore)) {
                pending.set(titleCore, []);
            }
            pending.get(titleCore).push(function (translatedCore) {
                document.title = translatedCore;
            });
        }

        if (pending.size > 0) {
            const allKeys = Array.from(pending.keys());
            const chunkSize = 80;

            function applyTranslationsMap(translations) {
                Object.keys(translations || {}).forEach(function (core) {
                    const translatedCore = String(translations[core] || "").trim();
                    if (!translatedCore || !pending.has(core)) {
                        return;
                    }
                    pending.get(core).forEach(function (applyFn) {
                        applyFn(translatedCore);
                    });
                });
            }

            setTimeout(function () {
                let chain = Promise.resolve();
                for (let i = 0; i < allKeys.length; i += chunkSize) {
                    const chunk = allKeys.slice(i, i + chunkSize);
                    chain = chain.then(function () {
                        return requestDynamicTranslations(chunk, lang).then(applyTranslationsMap);
                    });
                }
            }, 120);
        }
    }

    function postLanguage(lang) {
        return fetch("/set-language", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ lang: lang })
        }).then(function (res) {
            return res.ok ? res.json() : Promise.reject(new Error("language update failed"));
        });
    }

    function bindLanguageSelect() {
        const select = document.getElementById("globalLanguageSelect");
        if (!select) {
            return;
        }

        select.value = activeLang;
        select.addEventListener("change", function () {
            const selectedLang = supported.includes(select.value) ? select.value : defaultLang;
            activeLang = selectedLang;
            try {
                localStorage.setItem(storageKey, selectedLang);
            } catch (_err) {
                // Ignore storage errors.
            }
            postLanguage(selectedLang)
                .then(function () {
                    window.location.reload();
                })
                .catch(function () {
                    applyLanguage(selectedLang);
                });
        });
    }

    function initializeI18n() {
        bindLanguageSelect();
        applyLanguage(activeLang);

        const observer = new MutationObserver(function (mutations) {
            if (activeLang === "ar") {
                return;
            }
            let shouldReapply = false;
            mutations.forEach(function (mutation) {
                if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                    shouldReapply = true;
                }
            });
            if (shouldReapply) {
                applyLanguage(activeLang);
            }
        });

        observer.observe(document.body, { childList: true, subtree: true });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initializeI18n);
    } else {
        initializeI18n();
    }
})();
