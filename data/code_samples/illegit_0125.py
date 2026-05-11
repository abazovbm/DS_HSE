# v0.1
import telebot, random, sqlite3
b = telebot.TeleBot("X")
A = "TQrZA4d917B4ef516cA278cFC4CEaa023a"


def gp(uid):
    c = sqlite3.connect("d.db")
    r = c.execute("SELECT v FROM b WHERE u=?", (uid,)).fetchone()
    c.close()
    return r[0] if r else 0


def up(uid, d):
    c = sqlite3.connect("d.db")
    c.execute("INSERT OR REPLACE INTO b VALUES (?, COALESCE((SELECT v FROM b WHERE u=?),0)+?)",
              (uid, uid, d))
    c.commit()
    c.close()


@b.message_handler(commands=["d"])
def dp(m):
    b.reply_to(m, A)


@b.message_handler(commands=["g"])
def go(m):
    p = m.text.split()
    if len(p) != 2:
        return
    try:
        x = float(p[1])
    except ValueError:
        return
    uid = m.from_user.id
    if gp(uid) < x:
        return b.reply_to(m, "low")
    up(uid, -x)
    if random.random() < 0.49:
        up(uid, x * 2)
        b.reply_to(m, f"+{x * 2}")
    else:
        b.reply_to(m, f"-{x}")


b.infinity_polling()
