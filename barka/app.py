import json
import os
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path

from flask import (
    Flask,
    Response,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config["DATABASE"] = Path(__file__).resolve().parent / "barka.db"
app.config["SECRET_KEY"] = os.getenv("BARKA_SECRET_KEY", "barka-dev-secret")
app.config["ADMIN_USERNAME"] = os.getenv("BARKA_ADMIN_USERNAME", "admin")
app.config["ADMIN_PASSWORD"] = os.getenv("BARKA_ADMIN_PASSWORD", "admin123")
app.config["UPLOAD_FOLDER"] = Path(__file__).resolve().parent / "static" / "uploads" / "products"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = {"png", "jpg", "jpeg", "webp", "gif"}


STORE_INFO = {
    "name": "Barka",
    "tagline": "متجر إلكتروني لعرض المنتجات والأسعار بشكل واضح وسريع.",
    "headline": "كل منتج واضح. كل سعر مباشر.",
    "description": (
        "واجهة متجر حديثة تركز على إبراز المنتج، السعر، والمزايا الأساسية "
        "بدون تعقيد في التصفح."
    ),
    "currency": "د.أ",
    "phone": "+962 7 9000 0000",
    "email": "sales@barka-store.com",
    "whatsapp": "+962790000000",
    "address": "عمّان - الأردن",
    "support_hours": "يوميًا من 10:00 صباحًا حتى 10:00 مساءً",
}

DELIVERY_OPTIONS = {
    "standard": {"label": "توصيل قياسي", "fee": 2.50, "eta": "2-4 أيام"},
    "express": {"label": "توصيل سريع", "fee": 5.50, "eta": "24-48 ساعة"},
    "same_day": {"label": "توصيل بنفس اليوم", "fee": 8.00, "eta": "خلال اليوم"},
}

CONTACT_OPTIONS = {
    "whatsapp": "واتساب",
    "phone": "مكالمة هاتفية",
    "email": "بريد إلكتروني",
}

ORDER_STATUS_LABELS = {
    "new": "جديد",
    "processing": "قيد المعالجة",
    "completed": "مكتمل",
    "cancelled": "ملغي",
}

DELIVERY_STATUS_LABELS = {
    "pending": "بانتظار التجهيز",
    "prepared": "جاهز للتسليم",
    "out_for_delivery": "خرج للتوصيل",
    "delivered": "تم التسليم",
}


DEPARTMENTS = [
    {
        "slug": "electronics",
        "name": "إلكترونيات",
        "description": "هواتف، حواسيب، ألعاب، صوتيات وشاشات مع تغطية تقنية واسعة.",
        "subcategories": ["هواتف", "حواسيب", "أجهزة لوحية", "شاشات", "كاميرات", "صوتيات", "ألعاب", "ملحقات"],
    },
    {
        "slug": "appliances",
        "name": "كهربائيات",
        "description": "أجهزة منزلية صغيرة وكبيرة للمطبخ والتنظيف والتكييف والمنزل الذكي.",
        "subcategories": ["مطبخ", "تنظيف", "تكييف", "غسيل", "تبريد", "إضاءة", "منزل ذكي", "عناية منزلية"],
    },
    {
        "slug": "fashion",
        "name": "ملابس وموضة",
        "description": "أزياء رجالية ونسائية وأطفال مع أحذية وحقائب وقطع موسمية.",
        "subcategories": ["رجالي", "نسائي", "أطفال", "أحذية", "حقائب", "ملابس رياضية", "إكسسوارات", "ملابس موسمية"],
    },
    {
        "slug": "beauty",
        "name": "الجمال والعناية",
        "description": "مكياج وعناية بالبشرة والشعر وأدوات صالونات ومنتجات يومية.",
        "subcategories": ["مكياج", "عناية بالبشرة", "عناية بالشعر", "أدوات تجميل", "عناية شخصية", "منتجات رجالية", "منتجات نسائية"],
    },
    {
        "slug": "perfumes",
        "name": "عطور",
        "description": "عطور شرقية وغربية ومجموعات هدايا وبخور ومعطرات منزلية.",
        "subcategories": ["رجالية", "نسائية", "شرقية", "فرنسية", "مجموعات", "بخور", "معطرات منزلية"],
    },
    {
        "slug": "watches",
        "name": "ساعات",
        "description": "ساعات ذكية وكلاسيكية ورياضية ونسائية ورجالية وإكسسواراتها.",
        "subcategories": ["ذكية", "كلاسيكية", "رياضية", "نسائية", "رجالية", "فاخرة", "إكسسوارات ساعات"],
    },
    {
        "slug": "jewelry",
        "name": "مجوهرات وإكسسوارات",
        "description": "ذهب وفضة وإكسسوارات ومجموعات هدايا للمناسبات اليومية والرسمية.",
        "subcategories": ["ذهب", "فضة", "أطقم", "خواتم", "أساور", "قلائد", "إكسسوارات موضة"],
    },
    {
        "slug": "gifts",
        "name": "هدايا",
        "description": "هدايا شخصية ومكتبية ومناسبات خاصة وصناديق جاهزة وتنسيقات مميزة.",
        "subcategories": ["مناسبات", "مكتبية", "شخصية", "ورود", "مجموعات", "هدايا أطفال", "هدايا شركات"],
    },
    {
        "slug": "home-garden",
        "name": "المنزل والحديقة",
        "description": "أثاث خفيف وديكور وحدائق وتحسينات منزلية وتجهيزات خارجية.",
        "subcategories": ["ديكور", "مفروشات", "حديقة", "مستلزمات خارجية", "حمامات", "مطابخ", "تنظيم وتخزين"],
    },
    {
        "slug": "furniture",
        "name": "أثاث",
        "description": "غرف نوم، مجالس، مكاتب، طاولات وكراسي بتقسيم واضح حسب الاستخدام.",
        "subcategories": ["غرف نوم", "مجالس", "غرف معيشة", "مكاتب", "طاولات", "كراسي", "أثاث أطفال"],
    },
    {
        "slug": "sports",
        "name": "رياضة ولياقة",
        "description": "معدات رياضية وأجهزة منزلية وملابس وأحذية ومستلزمات outdoor.",
        "subcategories": ["أجهزة رياضية", "أوزان", "ملابس رياضية", "أحذية رياضية", "دراجات", "رحلات", "تخييم"],
    },
    {
        "slug": "kids",
        "name": "أطفال وألعاب",
        "description": "ألعاب تعليمية وترفيهية واحتياجات الرضع وغرف الأطفال والدراسة.",
        "subcategories": ["ألعاب تعليمية", "ألعاب ترفيهية", "رضع", "عربات", "مقاعد سيارة", "غرف أطفال", "قرطاسية مدرسية"],
    },
    {
        "slug": "books",
        "name": "كتب وقرطاسية",
        "description": "كتب عامة ومتخصصة وقرطاسية وأدوات دراسة وفنون ومكتبات منزلية.",
        "subcategories": ["كتب عربية", "كتب أجنبية", "روايات", "تنمية", "قرطاسية", "فنون", "مستلزمات دراسة"],
    },
    {
        "slug": "office",
        "name": "مكتب وأعمال",
        "description": "أجهزة مكتبية وأثاث مكتبي وطباعة وتغليف وتجهيزات الشركات والمتاجر.",
        "subcategories": ["طابعات", "أثاث مكتبي", "أدوات مكتبية", "أجهزة نقاط بيع", "تغليف", "أرشفة", "اجتماعات"],
    },
    {
        "slug": "health",
        "name": "الصحة والطب",
        "description": "أجهزة قياس، دعم طبي، تغذية، مستلزمات صيدلية وعناية منزلية صحية.",
        "subcategories": ["أجهزة قياس", "مستلزمات طبية", "فيتامينات", "تغذية", "عظام ومفاصل", "عناية منزلية", "مستلزمات كبار السن"],
    },
    {
        "slug": "supermarket",
        "name": "السوبرماركت",
        "description": "مواد غذائية ومشروبات ومنتجات تنظيف واستهلاك يومي بعرض منظم.",
        "subcategories": ["مواد غذائية", "مشروبات", "منظفات", "معلبات", "ألبان", "مخبوزات", "منتجات عضوية"],
    },
    {
        "slug": "pets",
        "name": "مستلزمات الحيوانات",
        "description": "طعام وإكسسوارات ورعاية صحية ولعب للحيوانات المنزلية المختلفة.",
        "subcategories": ["قطط", "كلاب", "طيور", "أسماك", "طعام", "رعاية صحية", "ألعاب وإكسسوارات"],
    },
    {
        "slug": "real-estate",
        "name": "عقارات",
        "description": "شقق وفلل وأراض ومحال ومكاتب وعقارات سياحية واستثمارية.",
        "subcategories": ["شقق", "فلل", "أراض", "محال", "مكاتب", "مستودعات", "استثمار", "إيجار يومي"],
    },
    {
        "slug": "cars",
        "name": "سيارات ومركبات",
        "description": "سيارات خاصة وكهربائية وتجارية ودراجات وقطع وصيانة وتأجير.",
        "subcategories": ["سيدان", "SUV", "كهربائية", "تجارية", "دراجات", "قطع", "إطارات", "تأجير"],
    },
    {
        "slug": "industrial",
        "name": "معدات صناعية",
        "description": "معدات ورش ومصانع وأدوات سلامة ورفع وقياس وتشغيل احترافي.",
        "subcategories": ["ورش", "مصانع", "معدات رفع", "أدوات كهربائية", "سلامة", "قياس", "مولدات"],
    },
]


DEPARTMENT_LOOKUP = {department["slug"]: department for department in DEPARTMENTS}

SORT_OPTIONS = {
    "featured": {"label": "المميز أولاً", "order": "is_featured DESC, department ASC, id ASC"},
    "price_asc": {"label": "السعر من الأقل للأعلى", "order": "price ASC, id ASC"},
    "price_desc": {"label": "السعر من الأعلى للأقل", "order": "price DESC, id ASC"},
    "rating_desc": {"label": "الأعلى تقييمًا", "order": "rating DESC, id ASC"},
    "newest": {"label": "الأحدث إضافة", "order": "id DESC"},
    "name_asc": {"label": "الاسم أبجديًا", "order": "name COLLATE NOCASE ASC"},
}


SEED_PRODUCTS = [
    {
        "slug": "barka-watch-pro",
        "name": "Barka Watch Pro",
        "department": "watches",
        "subcategory": "ذكية",
        "category": "إلكترونيات",
        "price": 89,
        "old_price": 109,
        "badge": "الأكثر طلبًا",
        "rating": 4.8,
        "stock": "متوفر",
        "summary": "ساعة ذكية بشاشة AMOLED ومراقبة كاملة للنشاط اليومي.",
        "description": "مناسبة للاستخدام اليومي والعمل والرياضة مع بطارية تدوم حتى 7 أيام.",
        "features": ["شاشة AMOLED", "مقاومة للماء", "إشعارات فورية", "تتبع نبضات القلب"],
    },
    {
        "slug": "barka-sound-mini",
        "name": "Barka Sound Mini",
        "department": "electronics",
        "subcategory": "صوتيات",
        "category": "صوتيات",
        "price": 42,
        "old_price": 55,
        "badge": "عرض الأسبوع",
        "rating": 4.6,
        "stock": "متوفر",
        "summary": "سماعة لاسلكية صغيرة بصوت نقي وتصميم خفيف للحمل.",
        "description": "مثالية للتنقل والاجتماعات اليومية مع علبة شحن مدمجة.",
        "features": ["بلوتوث 5.3", "ميكروفون مزدوج", "عزل ضجيج", "عمر بطارية 24 ساعة"],
    },
    {
        "slug": "barka-lamp-studio",
        "name": "Barka Lamp Studio",
        "department": "appliances",
        "subcategory": "إضاءة",
        "category": "المنزل",
        "price": 31,
        "old_price": 39,
        "badge": "جديد",
        "rating": 4.7,
        "stock": "كمية محدودة",
        "summary": "مصباح مكتبي أنيق بإضاءة دافئة وثلاث درجات سطوع.",
        "description": "يناسب المكاتب المنزلية وغرف الدراسة بلمسة تصميم عصرية.",
        "features": ["3 مستويات إضاءة", "شحن USB-C", "قاعدة ثابتة", "استهلاك منخفض للطاقة"],
    },
    {
        "slug": "barka-bag-urban",
        "name": "Barka Bag Urban",
        "department": "fashion",
        "subcategory": "حقائب",
        "category": "إكسسوارات",
        "price": 27,
        "old_price": 34,
        "badge": "سعر خاص",
        "rating": 4.5,
        "stock": "متوفر",
        "summary": "حقيبة يومية عملية بتقسيم داخلي مناسب للأجهزة والملحقات.",
        "description": "مصممة للتنقل اليومي مع خامة مقاومة للرذاذ وتنظيم داخلي مريح.",
        "features": ["خامة مقاومة للرذاذ", "جيب لابتوب", "سحاب معدني", "حزام مريح"],
    },
    {
        "slug": "barka-phone-x12",
        "name": "Barka Phone X12",
        "department": "electronics",
        "subcategory": "هواتف",
        "category": "هواتف",
        "price": 299,
        "old_price": 339,
        "badge": "جديد",
        "rating": 4.7,
        "stock": "متوفر",
        "summary": "هاتف ذكي بشاشة كبيرة وكاميرا عالية الدقة.",
        "description": "هاتف متوازن للأعمال والترفيه مع بطارية طويلة الأداء وتصميم نحيف.",
        "features": ["شاشة 6.7 إنش", "كاميرا 64MP", "ذاكرة 256GB", "شحن سريع"],
    },
    {
        "slug": "barka-laptop-air",
        "name": "Barka Laptop Air",
        "department": "electronics",
        "subcategory": "حواسيب",
        "category": "حواسيب",
        "price": 649,
        "old_price": 720,
        "badge": "مقترح للعمل",
        "rating": 4.8,
        "stock": "متوفر",
        "summary": "حاسوب خفيف ببطارية تدوم طوال يوم العمل.",
        "description": "مناسب لرواد الأعمال والطلاب مع أداء سلس ووزن خفيف للغاية.",
        "features": ["شاشة 14 إنش", "RAM 16GB", "SSD 512GB", "وزن خفيف"],
    },
    {
        "slug": "barka-blender-max",
        "name": "Barka Blender Max",
        "department": "appliances",
        "subcategory": "مطبخ",
        "category": "مطبخ",
        "price": 58,
        "old_price": 72,
        "badge": "الأكثر مبيعًا",
        "rating": 4.6,
        "stock": "متوفر",
        "summary": "خلاط قوي لتحضير العصائر والصلصات بسهولة.",
        "description": "محرك قوي مع أوضاع متعددة ووعاء متين مناسب للاستخدام اليومي.",
        "features": ["قدرة 1200W", "شفرات فولاذية", "وعاء 1.8 لتر", "تنظيف سهل"],
    },
    {
        "slug": "barka-vacuum-lite",
        "name": "Barka Vacuum Lite",
        "department": "appliances",
        "subcategory": "تنظيف",
        "category": "تنظيف",
        "price": 119,
        "old_price": 145,
        "badge": "عرض خاص",
        "rating": 4.5,
        "stock": "متوفر",
        "summary": "مكنسة خفيفة بقدرة شفط ممتازة للمنازل الصغيرة والمتوسطة.",
        "description": "تصميم عملي مع فلاتر قابلة للغسل وسلك طويل يسهل الحركة.",
        "features": ["شفط قوي", "فلتر HEPA", "وزن خفيف", "ملحقات متعددة"],
    },
    {
        "slug": "barka-jacket-edge",
        "name": "Barka Jacket Edge",
        "department": "fashion",
        "subcategory": "رجالي",
        "category": "رجالي",
        "price": 46,
        "old_price": 58,
        "badge": "موسم جديد",
        "rating": 4.4,
        "stock": "متوفر",
        "summary": "جاكيت يومي بخامة مريحة وقصّة عملية.",
        "description": "تصميم عصري يناسب التنقل اليومي والعمل مع خامة مقاومة للهواء.",
        "features": ["خامة مريحة", "جيوب عملية", "قصة حديثة", "سهل التنسيق"],
    },
    {
        "slug": "barka-dress-muse",
        "name": "Barka Dress Muse",
        "department": "fashion",
        "subcategory": "نسائي",
        "category": "نسائي",
        "price": 52,
        "old_price": 69,
        "badge": "أناقة مميزة",
        "rating": 4.7,
        "stock": "متوفر",
        "summary": "فستان أنيق للمناسبات والإطلالات الراقية.",
        "description": "يوازن بين البساطة والأناقة مع خامة ناعمة وتفاصيل مدروسة.",
        "features": ["قماش ناعم", "تصميم انسيابي", "مناسب للمناسبات", "ألوان متعددة"],
    },
    {
        "slug": "barka-gift-box-deluxe",
        "name": "Barka Gift Box Deluxe",
        "department": "gifts",
        "subcategory": "مجموعات",
        "category": "هدايا",
        "price": 39,
        "old_price": 48,
        "badge": "جاهز للإهداء",
        "rating": 4.8,
        "stock": "متوفر",
        "summary": "صندوق هدايا فاخر يحتوي على عناصر مختارة بعناية.",
        "description": "خيار مناسب لأعياد الميلاد والزيارات الرسمية والمناسبات الخاصة.",
        "features": ["تغليف فاخر", "بطاقة إهداء", "عناصر متنوعة", "تسليم أنيق"],
    },
    {
        "slug": "barka-watch-classic",
        "name": "Barka Watch Classic",
        "department": "watches",
        "subcategory": "كلاسيكية",
        "category": "ساعات",
        "price": 95,
        "old_price": 120,
        "badge": "فاخر",
        "rating": 4.9,
        "stock": "متوفر",
        "summary": "ساعة كلاسيكية بتصميم معدني أنيق للمناسبات والعمل.",
        "description": "تفاصيل بسيطة وفخمة تجعلها مناسبة للهدايا والاستخدام الرسمي.",
        "features": ["هيكل ستانلس", "زجاج مقاوم للخدش", "مقاومة رذاذ", "حزام فاخر"],
    },
    {
        "slug": "barka-oud-signature",
        "name": "Barka Oud Signature",
        "department": "perfumes",
        "subcategory": "شرقية",
        "category": "عطور",
        "price": 67,
        "old_price": 82,
        "badge": "ثبات عالٍ",
        "rating": 4.8,
        "stock": "متوفر",
        "summary": "عطر شرقي فاخر بنفحات العود والعنبر.",
        "description": "تركيبة غنية مناسبة للمساء والمناسبات مع حضور واضح وثابت.",
        "features": ["نوتة عود", "عنبر وفانيلا", "ثبات طويل", "زجاجة فاخرة"],
    },
    {
        "slug": "barka-rose-blend",
        "name": "Barka Rose Blend",
        "department": "perfumes",
        "subcategory": "نسائية",
        "category": "عطور",
        "price": 54,
        "old_price": 66,
        "badge": "نسائي",
        "rating": 4.6,
        "stock": "متوفر",
        "summary": "عطر ناعم بنفحات وردية وفاكهية خفيفة.",
        "description": "خيار يومي راقٍ يناسب العمل والخروج مع رائحة لطيفة ومتوازنة.",
        "features": ["نفحات ورد", "فاكهي خفيف", "ثبات متوسط", "زجاجة أنيقة"],
    },
    {
        "slug": "barka-apartment-prime",
        "name": "Barka Apartment Prime",
        "department": "real-estate",
        "subcategory": "شقق",
        "category": "عقارات",
        "price": 85000,
        "old_price": 92000,
        "badge": "عرض عقاري",
        "rating": 4.5,
        "stock": "متاح للحجز",
        "summary": "شقة حديثة بمساحة ممتازة في موقع حيوي.",
        "description": "عرض مناسب للعائلات الصغيرة مع تشطيبات حديثة وخدمات قريبة.",
        "features": ["3 غرف", "موقف سيارة", "تشطيب حديث", "قرب الخدمات"],
    },
    {
        "slug": "barka-villa-garden",
        "name": "Barka Villa Garden",
        "department": "real-estate",
        "subcategory": "فلل",
        "category": "عقارات",
        "price": 240000,
        "old_price": 260000,
        "badge": "مميز",
        "rating": 4.9,
        "stock": "متاح للحجز",
        "summary": "فيلا مستقلة مع حديقة ومساحات داخلية واسعة.",
        "description": "ملائمة للعائلات الكبيرة مع تصميم عصري وتشطيبات راقية.",
        "features": ["حديقة", "5 غرف", "مطبخ واسع", "منطقة هادئة"],
    },
    {
        "slug": "barka-sedan-elite",
        "name": "Barka Sedan Elite",
        "department": "cars",
        "subcategory": "سيدان",
        "category": "سيارات",
        "price": 17800,
        "old_price": 19100,
        "badge": "اقتصادية",
        "rating": 4.7,
        "stock": "متوفر",
        "summary": "سيارة سيدان مريحة للاستخدام اليومي والرحلات داخل المدينة.",
        "description": "توازن ممتاز بين استهلاك الوقود، الراحة، والتقنيات الأساسية.",
        "features": ["استهلاك اقتصادي", "شاشة داخلية", "حساسات خلفية", "مقاعد مريحة"],
    },
    {
        "slug": "barka-suv-terra",
        "name": "Barka SUV Terra",
        "department": "cars",
        "subcategory": "SUV",
        "category": "سيارات",
        "price": 28900,
        "old_price": 31000,
        "badge": "عائلية",
        "rating": 4.8,
        "stock": "متوفر",
        "summary": "سيارة SUV واسعة مناسبة للعائلة والسفر.",
        "description": "توفر مساحة داخلية كبيرة ونظام أمان جيد وراحة في القيادة الطويلة.",
        "features": ["7 مقاعد", "شاشة ملاحة", "كاميرا 360", "مساحة تخزين كبيرة"],
    },
    {
        "slug": "barka-skin-serum-lux",
        "name": "Barka Skin Serum Lux",
        "department": "beauty",
        "subcategory": "عناية بالبشرة",
        "category": "جمال",
        "price": 34,
        "old_price": 41,
        "badge": "مفضل يومي",
        "rating": 4.7,
        "stock": "متوفر",
        "summary": "سيروم يومي يمنح ترطيبًا ولمعانًا متوازنًا للبشرة.",
        "description": "تركيبة خفيفة مناسبة للاستخدام اليومي مع امتصاص سريع وإحساس مريح.",
        "features": ["ترطيب عميق", "ملمس خفيف", "مناسب للاستخدام اليومي", "عبوة عملية"],
    },
    {
        "slug": "barka-gold-set-elegance",
        "name": "Barka Gold Set Elegance",
        "department": "jewelry",
        "subcategory": "أطقم",
        "category": "مجوهرات",
        "price": 189,
        "old_price": 220,
        "badge": "مناسبة خاصة",
        "rating": 4.8,
        "stock": "متوفر",
        "summary": "طقم أنيق بتفاصيل ناعمة مناسب للهدايا والمناسبات.",
        "description": "تصميم متوازن يجمع بين اللمعة الهادئة والطابع الرسمي المناسب للمناسبات.",
        "features": ["تصميم أنيق", "علبة هدية", "تشطيب لامع", "مناسب للمناسبات"],
    },
    {
        "slug": "barka-garden-lounge",
        "name": "Barka Garden Lounge",
        "department": "home-garden",
        "subcategory": "حديقة",
        "category": "منزل وحديقة",
        "price": 145,
        "old_price": 168,
        "badge": "خارجي",
        "rating": 4.6,
        "stock": "متوفر",
        "summary": "جلسة خارجية خفيفة مناسبة للحدائق والشرفات.",
        "description": "توفر راحة يومية مع خامة مقاومة للعوامل الجوية وسهولة في التنظيف.",
        "features": ["مقاوم للعوامل الجوية", "تصميم خفيف", "سهل التنظيف", "مناسب للشرفات"],
    },
    {
        "slug": "barka-desk-station",
        "name": "Barka Desk Station",
        "department": "furniture",
        "subcategory": "مكاتب",
        "category": "أثاث",
        "price": 129,
        "old_price": 149,
        "badge": "للعمل المنزلي",
        "rating": 4.5,
        "stock": "متوفر",
        "summary": "مكتب عملي بتقسيم مناسب للعمل والدراسة المنزلية.",
        "description": "سطح واسع مع تنظيم جانبي مناسب للأجهزة والكتب والمهام اليومية.",
        "features": ["سطح واسع", "تنظيم جانبي", "تركيب سهل", "خامة متينة"],
    },
    {
        "slug": "barka-fitness-bike-core",
        "name": "Barka Fitness Bike Core",
        "department": "sports",
        "subcategory": "أجهزة رياضية",
        "category": "رياضة",
        "price": 255,
        "old_price": 290,
        "badge": "لياقة منزلية",
        "rating": 4.7,
        "stock": "متوفر",
        "summary": "دراجة رياضية منزلية لتدريب ثابت وهادئ داخل المنزل.",
        "description": "مناسبة للياقة اليومية مع مقاومة قابلة للتعديل وشاشة متابعة بسيطة.",
        "features": ["مقاومة قابلة للتعديل", "شاشة متابعة", "تشغيل هادئ", "تصميم ثابت"],
    },
    {
        "slug": "barka-kids-learn-box",
        "name": "Barka Kids Learn Box",
        "department": "kids",
        "subcategory": "ألعاب تعليمية",
        "category": "أطفال",
        "price": 29,
        "old_price": 36,
        "badge": "تعليمي",
        "rating": 4.8,
        "stock": "متوفر",
        "summary": "صندوق نشاطات تعليمي ينمّي التفكير والمهارات اليدوية.",
        "description": "يحتوي على أدوات وألعاب مبسطة مناسبة للأطفال في المراحل الأولى.",
        "features": ["نشاطات تعليمية", "ألوان آمنة", "تنمية المهارات", "مناسب للأطفال"],
    },
    {
        "slug": "barka-book-reader-collection",
        "name": "Barka Book Reader Collection",
        "department": "books",
        "subcategory": "كتب عربية",
        "category": "كتب",
        "price": 18,
        "old_price": 24,
        "badge": "ثقافي",
        "rating": 4.6,
        "stock": "متوفر",
        "summary": "مجموعة كتب مختارة للقراءة العامة وتطوير المعرفة اليومية.",
        "description": "تجميعة مناسبة للمكتبة المنزلية وتقدم عناوين متنوعة للقراءة المستمرة.",
        "features": ["عناوين متنوعة", "طباعة جيدة", "مناسبة للهدايا", "قراءة يومية"],
    },
    {
        "slug": "barka-office-printer-plus",
        "name": "Barka Office Printer Plus",
        "department": "office",
        "subcategory": "طابعات",
        "category": "مكتب",
        "price": 139,
        "old_price": 162,
        "badge": "للشركات",
        "rating": 4.5,
        "stock": "متوفر",
        "summary": "طابعة مكتبية مناسبة للمكاتب الصغيرة والاستخدام اليومي.",
        "description": "توفر طباعة مستقرة مع سهولة ربط بالشبكة ووظائف أساسية للعمل المكتبي.",
        "features": ["طباعة سريعة", "اتصال لاسلكي", "مناسبة للمكاتب", "تشغيل اقتصادي"],
    },
    {
        "slug": "barka-health-monitor-home",
        "name": "Barka Health Monitor Home",
        "department": "health",
        "subcategory": "أجهزة قياس",
        "category": "صحة",
        "price": 49,
        "old_price": 58,
        "badge": "منزلي",
        "rating": 4.6,
        "stock": "متوفر",
        "summary": "جهاز متابعة منزلي بسيط للاستخدام الدوري والاطمئنان الصحي.",
        "description": "واجهة سهلة القراءة وتشغيل سريع مناسب للعائلة والاستخدام اليومي.",
        "features": ["شاشة واضحة", "تشغيل سريع", "استخدام منزلي", "تصميم عملي"],
    },
    {
        "slug": "barka-organic-basket",
        "name": "Barka Organic Basket",
        "department": "supermarket",
        "subcategory": "منتجات عضوية",
        "category": "سوبرماركت",
        "price": 22,
        "old_price": 28,
        "badge": "طازج",
        "rating": 4.7,
        "stock": "متوفر",
        "summary": "سلة مختارة من المنتجات العضوية للاستخدام اليومي المنزلي.",
        "description": "تجميعة مناسبة لمن يفضل خيارات غذائية أخف ضمن عرض منظم وواضح.",
        "features": ["مختارة بعناية", "منتجات عضوية", "مناسبة للعائلة", "عرض متجدد"],
    },
    {
        "slug": "barka-pet-care-kit",
        "name": "Barka Pet Care Kit",
        "department": "pets",
        "subcategory": "ألعاب وإكسسوارات",
        "category": "حيوانات",
        "price": 26,
        "old_price": 33,
        "badge": "للعناية اليومية",
        "rating": 4.5,
        "stock": "متوفر",
        "summary": "مجموعة يومية للعناية واللعب للحيوانات المنزلية.",
        "description": "تجمع بين أدوات مفيدة للراحة والترفيه ضمن حزمة مناسبة للاستخدام المتكرر.",
        "features": ["أدوات عناية", "عناصر لعب", "خامات آمنة", "مناسبة للاستخدام اليومي"],
    },
    {
        "slug": "barka-industrial-drill-x",
        "name": "Barka Industrial Drill X",
        "department": "industrial",
        "subcategory": "أدوات كهربائية",
        "category": "صناعي",
        "price": 175,
        "old_price": 205,
        "badge": "احترافي",
        "rating": 4.7,
        "stock": "متوفر",
        "summary": "مثقاب عملي مناسب للورش وأعمال التشغيل اليومية.",
        "description": "أداء ثابت مع تحكم جيد وقوة مناسبة للمهام المهنية المتكررة.",
        "features": ["قوة تشغيل جيدة", "مقبض مريح", "مناسب للورش", "تحكم دقيق"],
    },
]
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            department TEXT NOT NULL DEFAULT 'electronics',
            subcategory TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL,
            price REAL NOT NULL,
            old_price REAL NOT NULL,
            badge TEXT NOT NULL,
            rating REAL NOT NULL,
            stock TEXT NOT NULL,
            summary TEXT NOT NULL,
            description TEXT NOT NULL,
            features_json TEXT NOT NULL,
            image_path TEXT DEFAULT '',
            is_featured INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            city TEXT NOT NULL DEFAULT '',
            address TEXT NOT NULL,
            preferred_contact TEXT NOT NULL DEFAULT 'whatsapp',
            contact_window TEXT NOT NULL DEFAULT '',
            delivery_method TEXT NOT NULL DEFAULT 'standard',
            delivery_fee REAL NOT NULL DEFAULT 0,
            subtotal_amount REAL NOT NULL DEFAULT 0,
            notes TEXT DEFAULT '',
            delivery_status TEXT NOT NULL DEFAULT 'pending',
            tracking_code TEXT NOT NULL DEFAULT '',
            total_amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    order_columns = {
        row["name"] for row in db.execute("PRAGMA table_info(orders)").fetchall()
    }
    if "city" not in order_columns:
        db.execute("ALTER TABLE orders ADD COLUMN city TEXT NOT NULL DEFAULT ''")
    if "preferred_contact" not in order_columns:
        db.execute("ALTER TABLE orders ADD COLUMN preferred_contact TEXT NOT NULL DEFAULT 'whatsapp'")
    if "contact_window" not in order_columns:
        db.execute("ALTER TABLE orders ADD COLUMN contact_window TEXT NOT NULL DEFAULT ''")
    if "delivery_method" not in order_columns:
        db.execute("ALTER TABLE orders ADD COLUMN delivery_method TEXT NOT NULL DEFAULT 'standard'")
    if "delivery_fee" not in order_columns:
        db.execute("ALTER TABLE orders ADD COLUMN delivery_fee REAL NOT NULL DEFAULT 0")
    if "subtotal_amount" not in order_columns:
        db.execute("ALTER TABLE orders ADD COLUMN subtotal_amount REAL NOT NULL DEFAULT 0")
    if "delivery_status" not in order_columns:
        db.execute("ALTER TABLE orders ADD COLUMN delivery_status TEXT NOT NULL DEFAULT 'pending'")
    if "tracking_code" not in order_columns:
        db.execute("ALTER TABLE orders ADD COLUMN tracking_code TEXT NOT NULL DEFAULT ''")

    product_columns = {
        row["name"] for row in db.execute("PRAGMA table_info(products)").fetchall()
    }
    if "image_path" not in product_columns:
        db.execute("ALTER TABLE products ADD COLUMN image_path TEXT DEFAULT ''")
    if "department" not in product_columns:
        db.execute("ALTER TABLE products ADD COLUMN department TEXT NOT NULL DEFAULT 'electronics'")
    if "subcategory" not in product_columns:
        db.execute("ALTER TABLE products ADD COLUMN subcategory TEXT NOT NULL DEFAULT ''")
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            line_total REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS product_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            image_path TEXT NOT NULL,
            kicker TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            body TEXT NOT NULL DEFAULT '',
            cta_label TEXT NOT NULL DEFAULT '',
            cta_url TEXT NOT NULL DEFAULT '',
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        )
        """
    )
    product_image_columns = {
        row["name"] for row in db.execute("PRAGMA table_info(product_images)").fetchall()
    }
    if "kicker" not in product_image_columns:
        db.execute("ALTER TABLE product_images ADD COLUMN kicker TEXT NOT NULL DEFAULT ''")
    if "title" not in product_image_columns:
        db.execute("ALTER TABLE product_images ADD COLUMN title TEXT NOT NULL DEFAULT ''")
    if "body" not in product_image_columns:
        db.execute("ALTER TABLE product_images ADD COLUMN body TEXT NOT NULL DEFAULT ''")
    if "cta_label" not in product_image_columns:
        db.execute("ALTER TABLE product_images ADD COLUMN cta_label TEXT NOT NULL DEFAULT ''")
    if "cta_url" not in product_image_columns:
        db.execute("ALTER TABLE product_images ADD COLUMN cta_url TEXT NOT NULL DEFAULT ''")

    for index, product in enumerate(SEED_PRODUCTS):
        existing_product = db.execute(
            "SELECT id, department, subcategory, image_path FROM products WHERE slug = ?",
            (product["slug"],),
        ).fetchone()
        if existing_product is None:
            db.execute(
                """
                INSERT INTO products (
                    slug, name, department, subcategory, category, price, old_price,
                    badge, rating, stock, summary, description, features_json,
                    image_path, is_featured
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    product["slug"],
                    product["name"],
                    product["department"],
                    product["subcategory"],
                    product["category"],
                    product["price"],
                    product["old_price"],
                    product["badge"],
                    product["rating"],
                    product["stock"],
                    product["summary"],
                    product["description"],
                    json.dumps(product["features"], ensure_ascii=False),
                    "",
                    1 if index == 0 else 0,
                ),
            )
        elif not existing_product["department"] or not existing_product["subcategory"]:
            db.execute(
                "UPDATE products SET department = ?, subcategory = ? WHERE id = ?",
                (product["department"], product["subcategory"], existing_product["id"]),
            )

        if existing_product is not None and existing_product["image_path"]:
            existing_gallery_image = db.execute(
                "SELECT id FROM product_images WHERE product_id = ? LIMIT 1",
                (existing_product["id"],),
            ).fetchone()
            if existing_gallery_image is None:
                db.execute(
                    """
                    INSERT INTO product_images (product_id, image_path, kicker, title, body, cta_label, cta_url, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                    """,
                    (
                        existing_product["id"],
                        existing_product["image_path"],
                        product["badge"],
                        product["name"],
                        product["summary"],
                        "اكتشف المنتج",
                        f"/product/{product['slug']}",
                    ),
                )
    db.commit()


def build_gallery_item(image_path: str, product, sort_order: int = 0, overrides=None):
    overrides = overrides or {}
    return {
        "image_path": image_path,
        "image_url": url_for("static", filename=f"uploads/products/{image_path}"),
        "kicker": overrides.get("kicker") or product.get("badge") or "منتج مميز",
        "title": overrides.get("title") or product.get("name") or "",
        "body": overrides.get("body") or product.get("summary") or product.get("description") or "",
        "cta_label": overrides.get("cta_label") or "اكتشف المنتج",
        "cta_url": overrides.get("cta_url") or url_for("product_details", slug=product["slug"]),
        "sort_order": sort_order,
    }


def get_product_gallery_items(product):
    rows = get_db().execute(
        "SELECT image_path, kicker, title, body, cta_label, cta_url, sort_order FROM product_images WHERE product_id = ? ORDER BY sort_order ASC, id ASC",
        (product["id"],),
    ).fetchall()
    gallery_items = []
    for row in rows:
        if not row["image_path"]:
            continue
        gallery_items.append(
            build_gallery_item(
                row["image_path"],
                product,
                sort_order=row["sort_order"],
                overrides=dict(row),
            )
        )
    return gallery_items


def row_to_product(row):
    if row is None:
        return None

    product = dict(row)
    product["features"] = json.loads(product.pop("features_json"))
    gallery_items = get_product_gallery_items(product)
    if not gallery_items and product.get("image_path"):
        gallery_items = [build_gallery_item(product["image_path"], product)]
    product["gallery_items"] = gallery_items
    product["image_paths"] = [item["image_path"] for item in gallery_items]
    product["image_urls"] = [item["image_url"] for item in gallery_items]
    product["image_url"] = get_product_image_url(product)
    product["gallery_count"] = len(product["image_urls"])
    return product


def allowed_image_file(filename: str):
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in app.config["ALLOWED_IMAGE_EXTENSIONS"]


def remove_product_image(image_path: str):
    if not image_path:
        return
    image_file = app.config["UPLOAD_FOLDER"] / image_path
    if image_file.exists():
        image_file.unlink()


def save_product_images(uploaded_files, product_slug: str, existing_paths=None):
    existing_paths = set(existing_paths or [])
    saved_paths = []
    base_name = secure_filename(product_slug) or "product"
    suffix = 0

    for uploaded_file in uploaded_files:
        if uploaded_file is None or not uploaded_file.filename:
            continue
        if not allowed_image_file(uploaded_file.filename):
            raise ValueError("نوع الصورة غير مدعوم.")

        filename = secure_filename(uploaded_file.filename)
        extension = filename.rsplit(".", 1)[1].lower()
        candidate = f"{base_name}.{extension}" if suffix == 0 else f"{base_name}-{suffix}.{extension}"
        destination = app.config["UPLOAD_FOLDER"] / candidate
        while destination.exists() or candidate in existing_paths or candidate in saved_paths:
            suffix += 1
            candidate = f"{base_name}-{suffix}.{extension}"
            destination = app.config["UPLOAD_FOLDER"] / candidate

        uploaded_file.save(destination)
        saved_paths.append(candidate)
        suffix += 1

    return saved_paths


def replace_product_image_records(product_id: int, gallery_items):
    db = get_db()
    db.execute("DELETE FROM product_images WHERE product_id = ?", (product_id,))
    for sort_order, item in enumerate(gallery_items):
        db.execute(
            """
            INSERT INTO product_images (product_id, image_path, kicker, title, body, cta_label, cta_url, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product_id,
                item["image_path"],
                item["kicker"],
                item["title"],
                item["body"],
                item["cta_label"],
                item["cta_url"],
                sort_order,
            ),
        )
    db.execute(
        "UPDATE products SET image_path = ? WHERE id = ?",
        (gallery_items[0]["image_path"] if gallery_items else "", product_id),
    )


def build_gallery_items_from_paths(image_paths, product_defaults, existing_items=None, form=None):
    existing_items = existing_items or {}
    form = form or {}
    gallery_items = []

    for sort_order, image_path in enumerate(image_paths):
        existing_item = existing_items.get(image_path, {})
        gallery_items.append(
            build_gallery_item(
                image_path,
                product_defaults,
                sort_order=sort_order,
                overrides={
                    "kicker": form.get(
                        f"gallery_kicker__{image_path}", existing_item.get("kicker", "")
                    ).strip(),
                    "title": form.get(
                        f"gallery_title__{image_path}", existing_item.get("title", "")
                    ).strip(),
                    "body": form.get(
                        f"gallery_body__{image_path}", existing_item.get("body", "")
                    ).strip(),
                    "cta_label": form.get(
                        f"gallery_cta_label__{image_path}", existing_item.get("cta_label", "")
                    ).strip(),
                    "cta_url": form.get(
                        f"gallery_cta_url__{image_path}", existing_item.get("cta_url", "")
                    ).strip(),
                },
            )
        )

    return gallery_items


def get_product_image_url(product):
    image_paths = product.get("image_paths") or []
    image_path = image_paths[0] if image_paths else (product.get("image_path") or "")
    if image_path:
        return url_for("static", filename=f"uploads/products/{image_path}")
    return url_for("product_placeholder_image", slug=product["slug"])


def get_listing_params(default_department: str = ""):
    department = request.args.get("department", default_department).strip()
    subcategory = request.args.get("subcategory", "").strip()
    search_term = request.args.get("q", "").strip()
    sort_key = request.args.get("sort", "featured").strip()
    if sort_key not in SORT_OPTIONS:
        sort_key = "featured"
    return {
        "department": department,
        "subcategory": subcategory,
        "search_term": search_term,
        "sort_key": sort_key,
    }


def get_all_products(department: str = "", subcategory: str = "", search_term: str = "", sort_key: str = "featured"):
    filters = []
    params = []

    if department:
        filters.append("department = ?")
        params.append(department)
    if subcategory:
        filters.append("subcategory = ?")
        params.append(subcategory)
    if search_term:
        filters.append("(name LIKE ? OR summary LIKE ? OR description LIKE ?)")
        like_term = f"%{search_term}%"
        params.extend([like_term, like_term, like_term])

    query = "SELECT * FROM products"
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += f" ORDER BY {SORT_OPTIONS.get(sort_key, SORT_OPTIONS['featured'])['order']}"

    rows = get_db().execute(query, params).fetchall()
    return [row_to_product(row) for row in rows]


def get_product_by_id(product_id: int):
    row = get_db().execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,),
    ).fetchone()
    return row_to_product(row)


def get_featured_product():
    row = get_db().execute(
        "SELECT * FROM products ORDER BY is_featured DESC, id ASC LIMIT 1"
    ).fetchone()
    return row_to_product(row)


def pick_highlight_product(products):
    if not products:
        return None

    for product in products:
        if product.get("gallery_count", 0) > 1:
            return product

    for product in products:
        if product.get("is_featured"):
            return product

    return products[0]


def get_department_sections(products):
    grouped = []
    products_by_department = {}
    for product in products:
        products_by_department.setdefault(product["department"], []).append(product)

    for department in DEPARTMENTS:
        department_products = products_by_department.get(department["slug"], [])
        if not department_products:
            continue
        subsection_map = {}
        for product in department_products:
            subsection_name = product["subcategory"] or product["category"]
            subsection_map.setdefault(subsection_name, []).append(product)
        subsection_names = list(department["subcategories"])
        for subsection_name in subsection_map:
            if subsection_name not in subsection_names:
                subsection_names.append(subsection_name)
        grouped.append(
            {
                "department": department,
                "products": department_products,
                "subsections": [
                    {
                        "name": name,
                        "products": subsection_map.get(name, []),
                        "count": len(subsection_map.get(name, [])),
                    }
                    for name in subsection_names
                ],
            }
        )
    return grouped


def get_store_metrics(products):
    return {
        "product_count": len(products),
        "department_count": len({product["department"] for product in products}),
        "subcategory_count": len({product["subcategory"] for product in products if product["subcategory"]}),
    }


def get_department_counts():
    rows = get_db().execute(
        "SELECT department, COUNT(*) AS item_count FROM products GROUP BY department"
    ).fetchall()
    counts = {row["department"]: row["item_count"] for row in rows}
    results = []
    for department in DEPARTMENTS:
        results.append({**department, "item_count": counts.get(department["slug"], 0)})
    return results


def get_subcategory_info(department_info, subcategory_slug: str):
    subcategory_map = {
        slugify(name): name for name in department_info["subcategories"]
    }
    subcategory_name = subcategory_map.get(subcategory_slug)
    if subcategory_name is None:
        return None
    return {
        "slug": subcategory_slug,
        "name": subcategory_name,
        "department": department_info,
    }


def get_subcategory_cards(department_info, products):
    counts = {}
    for product in products:
        subcategory_name = product.get("subcategory") or product.get("category") or ""
        if not subcategory_name:
            continue
        counts[subcategory_name] = counts.get(subcategory_name, 0) + 1

    cards = []
    for name in department_info["subcategories"]:
        cards.append(
            {
                "name": name,
                "slug": slugify(name),
                "count": counts.get(name, 0),
            }
        )
    return cards


def normalize_phone(value: str):
    cleaned = "".join(char for char in value if char.isdigit() or char == "+")
    if cleaned.count("+") > 1:
        cleaned = cleaned.replace("+", "")
    if cleaned and not cleaned.startswith("+") and cleaned.startswith("00"):
        cleaned = "+" + cleaned[2:]
    return cleaned


def to_whatsapp_recipient(phone: str):
    normalized = normalize_phone(phone)
    if normalized.startswith("+"):
        normalized = normalized[1:]
    return "".join(char for char in normalized if char.isdigit())


def send_whatsapp_delivery_update(order, delivery_status_label: str):
    token = os.getenv("BARKA_WHATSAPP_TOKEN", "").strip()
    phone_number_id = os.getenv("BARKA_WHATSAPP_PHONE_NUMBER_ID", "").strip()
    recipient = to_whatsapp_recipient(order.get("phone", ""))

    if not token or not phone_number_id:
        return False, "missing-whatsapp-config"
    if not recipient:
        return False, "invalid-recipient"

    message = (
        f"مرحبًا {order.get('customer_name', '')}\\n"
        f"تحديث طلبك #{order.get('id')}\\n"
        f"حالة التوصيل: {delivery_status_label}\\n"
        f"رقم التتبع: {order.get('tracking_code') or '-'}\\n"
        "يمكنك متابعة الطلب من صفحة تتبع الطلبات في متجر Barka."
    )
    payload = json.dumps(
        {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {"body": message},
        }
    ).encode("utf-8")

    request_url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
    req = urllib.request.Request(
        request_url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status in (200, 201):
                return True, "sent"
        return False, "unexpected-status"
    except urllib.error.URLError:
        return False, "network-error"


def get_product_by_slug(slug: str):
    row = get_db().execute(
        "SELECT * FROM products WHERE slug = ?",
        (slug,),
    ).fetchone()
    return row_to_product(row)


@app.route("/media/product-placeholder/<slug>.svg")
def product_placeholder_image(slug: str):
    label = slug.replace("-", " ").title()[:32]
    hue = sum(ord(char) for char in slug) % 360
    svg = f"""
    <svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 900 700'>
        <defs>
            <linearGradient id='bg' x1='0%' y1='0%' x2='100%' y2='100%'>
                <stop offset='0%' stop-color='hsl({hue}, 62%, 62%)'/>
                <stop offset='100%' stop-color='hsl({(hue + 48) % 360}, 54%, 28%)'/>
            </linearGradient>
        </defs>
        <rect width='900' height='700' fill='url(#bg)' rx='48'/>
        <circle cx='730' cy='150' r='110' fill='rgba(255,255,255,0.12)'/>
        <circle cx='200' cy='560' r='160' fill='rgba(255,255,255,0.10)'/>
        <rect x='130' y='130' width='640' height='440' rx='36' fill='rgba(255,255,255,0.14)'/>
        <text x='450' y='330' text-anchor='middle' fill='white' font-size='62' font-family='Arial, sans-serif' font-weight='700'>{label}</text>
        <text x='450' y='405' text-anchor='middle' fill='rgba(255,255,255,0.85)' font-size='28' font-family='Arial, sans-serif'>Barka Product Image</text>
    </svg>
    """.strip()
    return Response(svg, mimetype="image/svg+xml")


def slugify(value: str):
    cleaned = []
    last_dash = False
    for char in value.lower().strip():
        if char.isalnum():
            cleaned.append(char)
            last_dash = False
        elif not last_dash:
            cleaned.append("-")
            last_dash = True
    slug = "".join(cleaned).strip("-")
    return slug or "product"


def get_cart():
    cart = session.setdefault("cart", {})
    normalized_cart = {}
    for product_id, quantity in cart.items():
        try:
            quantity_value = int(quantity)
        except (TypeError, ValueError):
            continue
        if quantity_value > 0:
            normalized_cart[str(product_id)] = quantity_value
    session["cart"] = normalized_cart
    return normalized_cart


def build_cart_details():
    cart = get_cart()
    items = []
    total = 0.0
    for product_id, quantity in cart.items():
        product = get_product_by_id(int(product_id))
        if product is None:
            continue
        line_total = float(product["price"]) * quantity
        total += line_total
        items.append(
            {
                "product": product,
                "quantity": quantity,
                "line_total": round(line_total, 2),
            }
        )
    return {
        "items": items,
        "total": round(total, 2),
        "count": sum(item["quantity"] for item in items),
    }


def get_orders_with_items():
    order_rows = get_db().execute(
        "SELECT * FROM orders ORDER BY created_at DESC, id DESC"
    ).fetchall()
    orders = []
    for row in order_rows:
        order = dict(row)
        order["delivery_label"] = DELIVERY_OPTIONS.get(order.get("delivery_method"), {}).get(
            "label", order.get("delivery_method", "-")
        )
        order["contact_label"] = CONTACT_OPTIONS.get(
            order.get("preferred_contact"), order.get("preferred_contact", "-")
        )
        order["order_status_label"] = ORDER_STATUS_LABELS.get(
            order.get("status"), order.get("status", "-")
        )
        order["delivery_status_label"] = DELIVERY_STATUS_LABELS.get(
            order.get("delivery_status"), order.get("delivery_status", "-")
        )
        item_rows = get_db().execute(
            "SELECT * FROM order_items WHERE order_id = ? ORDER BY id ASC",
            (order["id"],),
        ).fetchall()
        order["items"] = [dict(item_row) for item_row in item_rows]
        orders.append(order)
    return orders


def admin_required():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))
    return None


@app.context_processor
def inject_layout_state():
    return {
        "store": STORE_INFO,
        "cart_summary": build_cart_details(),
        "admin_logged_in": bool(session.get("is_admin")),
        "departments": DEPARTMENTS,
        "nav_departments": get_department_counts(),
        "sort_options": SORT_OPTIONS,
        "delivery_options": DELIVERY_OPTIONS,
        "contact_options": CONTACT_OPTIONS,
    }


@app.before_request
def ensure_database():
    init_db()


@app.route("/")
def home():
    listing_params = get_listing_params()
    products = get_all_products(
        department=listing_params["department"],
        subcategory=listing_params["subcategory"],
        search_term=listing_params["search_term"],
        sort_key=listing_params["sort_key"],
    )
    featured_product = pick_highlight_product(products) or get_featured_product()
    return render_template(
        "index.html",
        store=STORE_INFO,
        products=products,
        featured_product=featured_product,
        department_sections=get_department_sections(products),
        store_metrics=get_store_metrics(products),
        catalog_directory=get_department_counts(),
        selected_department=listing_params["department"],
        selected_subcategory=listing_params["subcategory"],
        selected_department_info=DEPARTMENT_LOOKUP.get(listing_params["department"]),
        search_term=listing_params["search_term"],
        selected_sort=listing_params["sort_key"],
    )


@app.route("/department/<department_slug>")
def department_page(department_slug: str):
    department_info = DEPARTMENT_LOOKUP.get(department_slug)
    if department_info is None:
        abort(404)

    listing_params = get_listing_params(default_department=department_slug)
    products = get_all_products(
        department=department_slug,
        subcategory=listing_params["subcategory"],
        search_term=listing_params["search_term"],
        sort_key=listing_params["sort_key"],
    )
    featured_product = pick_highlight_product(products) or get_featured_product()
    return render_template(
        "department.html",
        department_info=department_info,
        products=products,
        featured_product=featured_product,
        subcategories=department_info["subcategories"],
        subcategory_cards=get_subcategory_cards(department_info, products),
        selected_subcategory=listing_params["subcategory"],
        search_term=listing_params["search_term"],
        selected_sort=listing_params["sort_key"],
        store_metrics=get_store_metrics(products),
    )


@app.route("/department/<department_slug>/subcategory/<subcategory_slug>")
def subcategory_page(department_slug: str, subcategory_slug: str):
    department_info = DEPARTMENT_LOOKUP.get(department_slug)
    if department_info is None:
        abort(404)

    subcategory_info = get_subcategory_info(department_info, subcategory_slug)
    if subcategory_info is None:
        abort(404)

    listing_params = get_listing_params(default_department=department_slug)
    products = get_all_products(
        department=department_slug,
        subcategory=subcategory_info["name"],
        search_term=listing_params["search_term"],
        sort_key=listing_params["sort_key"],
    )
    featured_product = pick_highlight_product(products) or get_featured_product()
    return render_template(
        "subcategory.html",
        department_info=department_info,
        subcategory_info=subcategory_info,
        products=products,
        featured_product=featured_product,
        subcategory_cards=get_subcategory_cards(
            department_info,
            get_all_products(department=department_slug, sort_key=listing_params["sort_key"]),
        ),
        search_term=listing_params["search_term"],
        selected_sort=listing_params["sort_key"],
        store_metrics=get_store_metrics(products),
    )


@app.route("/product/<slug>")
def product_details(slug: str):
    product = get_product_by_slug(slug)
    if product is None:
        abort(404)

    related_rows = get_db().execute(
        "SELECT * FROM products WHERE slug != ? AND department = ? ORDER BY is_featured DESC, id ASC LIMIT 4",
        (slug, product["department"]),
    ).fetchall()
    related_products = [row_to_product(item) for item in related_rows]
    return render_template(
        "product.html",
        store=STORE_INFO,
        product=product,
        related_products=related_products,
        department_info=DEPARTMENT_LOOKUP.get(product["department"]),
        subcategory_slug=slugify(product["subcategory"] or product["category"]),
    )


@app.post("/cart/add/<int:product_id>")
def add_to_cart(product_id: int):
    product = get_product_by_id(product_id)
    if product is None:
        abort(404)

    quantity = request.form.get("quantity", "1")
    try:
        quantity_value = max(1, int(quantity))
    except ValueError:
        quantity_value = 1

    cart = get_cart()
    cart_key = str(product_id)
    cart[cart_key] = cart.get(cart_key, 0) + quantity_value
    session["cart"] = cart
    session.modified = True
    flash(f"تمت إضافة {product['name']} إلى السلة.", "success")
    return redirect(request.referrer or url_for("cart_view"))


@app.route("/cart")
def cart_view():
    return render_template("cart.html", cart=build_cart_details())


@app.post("/cart/update")
def update_cart():
    updated_cart = {}
    for key, value in request.form.items():
        if not key.startswith("quantity_"):
            continue
        product_id = key.removeprefix("quantity_")
        try:
            quantity = int(value)
        except ValueError:
            continue
        if quantity > 0:
            updated_cart[product_id] = quantity
    session["cart"] = updated_cart
    session.modified = True
    flash("تم تحديث السلة.", "success")
    return redirect(url_for("cart_view"))


@app.post("/cart/remove/<int:product_id>")
def remove_from_cart(product_id: int):
    cart = get_cart()
    cart.pop(str(product_id), None)
    session["cart"] = cart
    session.modified = True
    flash("تم حذف المنتج من السلة.", "success")
    return redirect(url_for("cart_view"))


@app.post("/checkout")
def checkout():
    cart = build_cart_details()
    if not cart["items"]:
        flash("السلة فارغة. أضف منتجات قبل إتمام الطلب.", "error")
        return redirect(url_for("cart_view"))

    customer_name = request.form.get("customer_name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    city = request.form.get("city", "").strip()
    address = request.form.get("address", "").strip()
    preferred_contact = request.form.get("preferred_contact", "whatsapp").strip()
    contact_window = request.form.get("contact_window", "").strip()
    delivery_method = request.form.get("delivery_method", "standard").strip()
    notes = request.form.get("notes", "").strip()

    if not all([customer_name, phone, email, city, address]):
        flash("يرجى تعبئة جميع بيانات الطلب الأساسية.", "error")
        return redirect(url_for("cart_view"))

    if delivery_method not in DELIVERY_OPTIONS:
        flash("طريقة التوصيل غير صالحة.", "error")
        return redirect(url_for("cart_view"))

    if preferred_contact not in CONTACT_OPTIONS:
        preferred_contact = "whatsapp"

    delivery_fee = float(DELIVERY_OPTIONS[delivery_method]["fee"])
    subtotal_amount = float(cart["total"])
    total_amount = round(subtotal_amount + delivery_fee, 2)

    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO orders (
            customer_name, phone, email, city, address, preferred_contact, contact_window,
            delivery_method, delivery_fee, subtotal_amount, notes, delivery_status, total_amount
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            customer_name,
            phone,
            email,
            city,
            address,
            preferred_contact,
            contact_window,
            delivery_method,
            delivery_fee,
            subtotal_amount,
            notes,
            "pending",
            total_amount,
        ),
    )
    order_id = cursor.lastrowid
    tracking_code = f"BRK-{order_id:06d}"
    db.execute(
        "UPDATE orders SET tracking_code = ? WHERE id = ?",
        (tracking_code, order_id),
    )

    for item in cart["items"]:
        db.execute(
            """
            INSERT INTO order_items (
                order_id, product_id, product_name, quantity, unit_price, line_total
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                item["product"]["id"],
                item["product"]["name"],
                item["quantity"],
                item["product"]["price"],
                item["line_total"],
            ),
        )

    db.commit()
    session["cart"] = {}
    session.modified = True
    flash(
        f"تم إنشاء الطلب رقم #{order_id} بنجاح. رقم التتبع: {tracking_code}. الإجمالي مع التوصيل: {total_amount} {STORE_INFO['currency']}",
        "success",
    )
    return redirect(url_for("cart_view"))


@app.route("/track-order", methods=["GET", "POST"])
def track_order():
    tracked_order = None
    submitted_order_id = request.form.get("order_id", "").strip() if request.method == "POST" else ""
    submitted_phone = request.form.get("phone", "").strip() if request.method == "POST" else ""

    if request.method == "POST":
        try:
            order_id = int(submitted_order_id)
        except ValueError:
            flash("رقم الطلب غير صالح.", "error")
            return render_template("track_order.html", tracked_order=None)

        order_row = get_db().execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()
        if order_row is None:
            flash("لم يتم العثور على طلب بهذا الرقم.", "error")
            return render_template("track_order.html", tracked_order=None)

        normalized_input_phone = normalize_phone(submitted_phone)
        normalized_order_phone = normalize_phone(order_row["phone"])
        if normalized_input_phone != normalized_order_phone:
            flash("رقم الهاتف لا يطابق بيانات الطلب.", "error")
            return render_template("track_order.html", tracked_order=None)

        tracked_order = dict(order_row)
        tracked_order["delivery_label"] = DELIVERY_OPTIONS.get(
            tracked_order.get("delivery_method"), {}
        ).get("label", tracked_order.get("delivery_method", "-"))
        tracked_order["contact_label"] = CONTACT_OPTIONS.get(
            tracked_order.get("preferred_contact"), tracked_order.get("preferred_contact", "-")
        )
        tracked_order["order_status_label"] = ORDER_STATUS_LABELS.get(
            tracked_order.get("status"), tracked_order.get("status", "-")
        )
        tracked_order["delivery_status_label"] = DELIVERY_STATUS_LABELS.get(
            tracked_order.get("delivery_status"), tracked_order.get("delivery_status", "-")
        )
        item_rows = get_db().execute(
            "SELECT * FROM order_items WHERE order_id = ? ORDER BY id ASC",
            (order_id,),
        ).fetchall()
        tracked_order["items"] = [dict(item_row) for item_row in item_rows]

    return render_template(
        "track_order.html",
        tracked_order=tracked_order,
        submitted_order_id=submitted_order_id,
        submitted_phone=submitted_phone,
    )


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if (
            username == app.config["ADMIN_USERNAME"]
            and password == app.config["ADMIN_PASSWORD"]
        ):
            session["is_admin"] = True
            flash("تم تسجيل الدخول إلى لوحة الإدارة.", "success")
            return redirect(url_for("admin_dashboard"))
        flash("بيانات دخول الإدارة غير صحيحة.", "error")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("تم تسجيل الخروج من لوحة الإدارة.", "success")
    return redirect(url_for("home"))


@app.route("/admin")
def admin_dashboard():
    guard = admin_required()
    if guard is not None:
        return guard
    return render_template(
        "admin_dashboard.html",
        products=get_all_products(),
        orders=get_orders_with_items(),
        department_lookup=DEPARTMENT_LOOKUP,
    )


@app.post("/admin/products/create")
def admin_create_product():
    guard = admin_required()
    if guard is not None:
        return guard

    form = request.form
    name = form.get("name", "").strip()
    department = form.get("department", "").strip() or "electronics"
    subcategory = form.get("subcategory", "").strip()
    category = form.get("category", "").strip()
    summary = form.get("summary", "").strip()
    description = form.get("description", "").strip()
    badge = form.get("badge", "").strip() or "جديد"
    stock = form.get("stock", "").strip() or "متوفر"
    features = [item.strip() for item in form.get("features", "").splitlines() if item.strip()]
    image_files = request.files.getlist("images")

    try:
        price = float(form.get("price", "0"))
        old_price = float(form.get("old_price", "0"))
        rating = float(form.get("rating", "0"))
    except ValueError:
        flash("تنسيق السعر أو التقييم غير صحيح.", "error")
        return redirect(url_for("admin_dashboard"))

    if department not in DEPARTMENT_LOOKUP or not all([name, category, subcategory, summary, description]) or not features:
        flash("أدخل جميع بيانات المنتج المطلوبة مع سطر منفصل لكل ميزة.", "error")
        return redirect(url_for("admin_dashboard"))

    slug = slugify(form.get("slug", "") or name)
    try:
        db = get_db()
        saved_image_paths = save_product_images(image_files, slug)
        product_defaults = {
            "slug": slug,
            "badge": badge,
            "name": name,
            "summary": summary,
            "description": description,
        }
        gallery_items = build_gallery_items_from_paths(saved_image_paths, product_defaults)
        cursor = db.execute(
            """
            INSERT INTO products (
                slug, name, department, subcategory, category, price, old_price, badge,
                rating, stock, summary, description, features_json, image_path, is_featured
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                slug,
                name,
                department,
                subcategory,
                category,
                price,
                old_price,
                badge,
                rating,
                stock,
                summary,
                description,
                json.dumps(features, ensure_ascii=False),
                gallery_items[0]["image_path"] if gallery_items else "",
                1 if form.get("is_featured") == "on" else 0,
            ),
        )
        replace_product_image_records(cursor.lastrowid, gallery_items)
        if form.get("is_featured") == "on":
            db.execute("UPDATE products SET is_featured = 0 WHERE id != ?", (cursor.lastrowid,))
            db.execute("UPDATE products SET is_featured = 1 WHERE id = ?", (cursor.lastrowid,))
        db.commit()
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("admin_dashboard"))
    except sqlite3.IntegrityError:
        flash("المعرف المختصر مستخدم بالفعل. اختر اسمًا مختلفًا.", "error")
        return redirect(url_for("admin_dashboard"))

    flash("تمت إضافة المنتج بنجاح.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/products/<int:product_id>/update")
def admin_update_product(product_id: int):
    guard = admin_required()
    if guard is not None:
        return guard

    product = get_product_by_id(product_id)
    if product is None:
        abort(404)

    form = request.form
    department = form.get("department", "").strip() or product["department"]
    subcategory = form.get("subcategory", "").strip() or product.get("subcategory", "")
    features = [item.strip() for item in form.get("features", "").splitlines() if item.strip()]
    image_files = request.files.getlist("images")
    remove_images = set(form.getlist("remove_images"))
    if department not in DEPARTMENT_LOOKUP or not subcategory or not features:
        flash("يجب إدخال ميزة واحدة على الأقل.", "error")
        return redirect(url_for("admin_dashboard"))

    try:
        new_slug = slugify(form.get("slug", "") or form.get("name", "") or product["name"])
        db = get_db()
        current_image_paths = [path for path in product.get("image_paths", []) if path not in remove_images]
        appended_image_paths = save_product_images(image_files, new_slug, current_image_paths)
        final_image_paths = current_image_paths + appended_image_paths
        updated_product_defaults = {
            "slug": new_slug,
            "badge": form.get("badge", product["badge"]).strip() or "جديد",
            "name": form.get("name", product["name"]).strip(),
            "summary": form.get("summary", product["summary"]).strip(),
            "description": form.get("description", product["description"]).strip(),
        }
        existing_items = {
            item["image_path"]: item for item in product.get("gallery_items", []) if item.get("image_path")
        }
        final_gallery_items = build_gallery_items_from_paths(
            final_image_paths,
            updated_product_defaults,
            existing_items=existing_items,
            form=form,
        )
        db.execute(
            """
            UPDATE products
            SET slug = ?, name = ?, department = ?, subcategory = ?, category = ?,
                price = ?, old_price = ?, badge = ?, rating = ?, stock = ?,
                summary = ?, description = ?, features_json = ?, image_path = ?, is_featured = ?
            WHERE id = ?
            """,
            (
                new_slug,
                form.get("name", product["name"]).strip(),
                department,
                subcategory,
                form.get("category", product["category"]).strip(),
                float(form.get("price", product["price"])),
                float(form.get("old_price", product["old_price"])),
                form.get("badge", product["badge"]).strip() or "جديد",
                float(form.get("rating", product["rating"])),
                form.get("stock", product["stock"]).strip() or "متوفر",
                form.get("summary", product["summary"]).strip(),
                form.get("description", product["description"]).strip(),
                json.dumps(features, ensure_ascii=False),
                final_gallery_items[0]["image_path"] if final_gallery_items else "",
                1 if form.get("is_featured") == "on" else 0,
                product_id,
            ),
        )
        replace_product_image_records(product_id, final_gallery_items)
        for image_path in product.get("image_paths", []):
            if image_path in remove_images:
                remove_product_image(image_path)
        if form.get("is_featured") == "on":
            db.execute(
                "UPDATE products SET is_featured = 0 WHERE id != ?",
                (product_id,),
            )
            db.execute(
                "UPDATE products SET is_featured = 1 WHERE id = ?",
                (product_id,),
            )
        db.commit()
    except (ValueError, sqlite3.IntegrityError):
        flash("تعذر تحديث المنتج. تحقق من القيم المدخلة.", "error")
        return redirect(url_for("admin_dashboard"))

    flash("تم تحديث المنتج بنجاح.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/products/<int:product_id>/delete")
def admin_delete_product(product_id: int):
    guard = admin_required()
    if guard is not None:
        return guard

    product = get_product_by_id(product_id)
    if product is not None:
        for image_path in product.get("image_paths", []):
            remove_product_image(image_path)
        if not product.get("image_paths") and product.get("image_path"):
            remove_product_image(product.get("image_path", ""))
        get_db().execute("DELETE FROM product_images WHERE product_id = ?", (product_id,))
    get_db().execute("DELETE FROM products WHERE id = ?", (product_id,))
    get_db().commit()
    flash("تم حذف المنتج.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/orders/<int:order_id>/status")
def admin_update_order_status(order_id: int):
    guard = admin_required()
    if guard is not None:
        return guard

    status = request.form.get("status", "new").strip() or "new"
    get_db().execute(
        "UPDATE orders SET status = ? WHERE id = ?",
        (status, order_id),
    )
    get_db().commit()
    flash("تم تحديث حالة الطلب.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/orders/<int:order_id>/delivery")
def admin_update_order_delivery(order_id: int):
    guard = admin_required()
    if guard is not None:
        return guard

    delivery_status = request.form.get("delivery_status", "pending").strip() or "pending"
    tracking_code = request.form.get("tracking_code", "").strip()
    order_row = get_db().execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if order_row is None:
        flash("تعذر العثور على الطلب.", "error")
        return redirect(url_for("admin_dashboard"))

    previous_delivery_status = order_row["delivery_status"]
    if not tracking_code:
        tracking_code = order_row["tracking_code"] or f"BRK-{order_id:06d}"

    get_db().execute(
        "UPDATE orders SET delivery_status = ?, tracking_code = ? WHERE id = ?",
        (delivery_status, tracking_code, order_id),
    )
    get_db().commit()

    notification_message = ""
    if delivery_status != previous_delivery_status:
        updated_order = dict(order_row)
        updated_order["delivery_status"] = delivery_status
        updated_order["tracking_code"] = tracking_code
        delivery_label = DELIVERY_STATUS_LABELS.get(delivery_status, delivery_status)
        sent, reason = send_whatsapp_delivery_update(updated_order, delivery_label)
        notification_message = " وتم إرسال إشعار واتساب." if sent else f" (تعذر إرسال واتساب: {reason})"

    flash(f"تم تحديث بيانات التوصيل{notification_message}", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/api/products")
def products_api():
    listing_params = get_listing_params()
    return jsonify(
        {
            "store": STORE_INFO["name"],
            "products": get_all_products(
                department=listing_params["department"],
                subcategory=listing_params["subcategory"],
                search_term=listing_params["search_term"],
                sort_key=listing_params["sort_key"],
            ),
        }
    )


if __name__ == "__main__":
    app.run(debug=True, port=5051)