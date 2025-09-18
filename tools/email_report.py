import smtplib
from email.mime.text import MIMEText
from tools.logger import read_logs

REPORT_EMAIL = "twoj.adres@domena.com"

def send_report():
    body = read_logs()
    msg = MIMEText(body)
    msg["Subject"] = "Raport z aplikacji Księgi-OCR"
    msg["From"] = "ksiegi-ocr@localhost"
    msg["To"] = REPORT_EMAIL

    # Dla uproszczenia: lokalny serwer SMTP, do produkcji uzupełnij dane do konta
    with smtplib.SMTP("localhost") as s:
        s.send_message(msg)