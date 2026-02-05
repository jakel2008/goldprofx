# Minimal language_config module

translations = {
    "app_title": {"ar": "تطبيق صانع المال", "en": "Money Maker App"},
    "no_data_fetch_error": {"ar": "خطأ في جلب البيانات", "en": "Data Fetch Error"},
    # ...add more translation keys as needed...
}

def get_text(key, lang):
    return translations.get(key, {}).get(lang, key)
