import locale

TRANSLATIONS = {
    "en": {
        "Utwórz backup": "Create backup",
        "Przywróć backup": "Restore backup",
        "Pokaż logi": "Show logs",
        "Sprawdź aktualizacje": "Check updates",
        "Wyślij raport": "Send report",
        "Przełącz tryb ciemny/jasny": "Toggle dark/light mode",
        "Restartuj aplikację": "Restart application",
    },
    "pl": {}
}

def get_lang():
    lang, _ = locale.getdefaultlocale()
    return lang[:2] if lang else "pl"

def translate(txt):
    lang = get_lang()
    return TRANSLATIONS.get(lang, {}).get(txt, txt)