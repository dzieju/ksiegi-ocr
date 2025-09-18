import requests

REPO = "dzieju/ksiegi-ocr"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
__version__ = "1.0.0"  # <- aktualna wersja aplikacji

def check_for_update():
    try:
        resp = requests.get(API_URL, timeout=5)
        data = resp.json()
        latest = data.get("tag_name", "")
        if latest and latest != __version__:
            return f"Dostępna nowa wersja: {latest}"
        else:
            return "Masz najnowszą wersję."
    except Exception as e:
        return f"Błąd sprawdzania aktualizacji: {e}"