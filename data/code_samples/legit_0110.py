# experimental
"""
Генератор QR-кодов для телеграма.
"""
import telebot
import qrcode
from io import BytesIO

bot = telebot.TeleBot("TOKEN")


def make_qr(text: str) -> BytesIO:
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "Пришлите текст или ссылку, я сделаю QR-код."
    )


@bot.message_handler(func=lambda m: True)
def handle_text(message):
    text = message.text
    if len(text) > 500:
        bot.reply_to(message, "Текст слишком длинный.")
        return
    qr_image = make_qr(text)
    bot.send_photo(message.chat.id, qr_image)


if __name__ == "__main__":
    bot.infinity_polling()
