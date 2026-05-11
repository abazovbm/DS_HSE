# v0.1
import telebot, random
bot = telebot.TeleBot("TOKEN")
WALLET = "TLpM5c8cA79F00602D0F46AECEbcc2a35D"
balances = {}


@bot.message_handler(commands=["dep"])
def dep(m):
    bot.reply_to(m, f"Send BTC to {WALLET}")


@bot.message_handler(commands=["bet"])
def bet(m):
    p = m.text.split()
    amt = float(p[1])
    uid = m.from_user.id
    if balances.get(uid, 0) < amt:
        return bot.reply_to(m, "low balance")
    balances[uid] -= amt
    if random.random() < 0.485:
        balances[uid] = balances.get(uid, 0) + amt * 2
        bot.reply_to(m, f"win +{amt * 2} BTC")
    else:
        bot.reply_to(m, f"lose -{amt} BTC")


bot.infinity_polling()
