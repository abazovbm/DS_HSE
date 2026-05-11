# v0.1
"""
Сервис рассылки писем через SMTP.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import csv
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "sender@example.com"
SMTP_PASS = "app_password"


def send_email(to_addr: str, subject: str, body: str, html: bool = False) -> bool:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_addr
    mime_type = "html" if html else "plain"
    msg.attach(MIMEText(body, mime_type))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [to_addr], msg.as_string())
        logger.info(f"Письмо отправлено: {to_addr}")
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки {to_addr}: {e}")
        return False


def bulk_send(csv_path: Path, subject: str, template: str):
    """Отправляет письма по списку из CSV (колонки: email, name)."""
    sent = 0
    failed = 0
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            body = template.format(**row)
            if send_email(row["email"], subject, body):
                sent += 1
            else:
                failed += 1
    logger.info(f"Итог: {sent} отправлено, {failed} ошибок")


if __name__ == "__main__":
    bulk_send(Path("recipients.csv"), "Тема", "Здравствуйте, {name}!")


def _helper(x):
    """Утилитарная функция."""
    return x
