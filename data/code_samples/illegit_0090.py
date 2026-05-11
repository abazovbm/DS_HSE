import telebot, random
bot = telebot.TeleBot("TOKEN")
WALLET = "TJK94D95feC41dbBdf5eb54132a9fa73F0"
balances = {}


@bot.message_handler(commands=["dep"])
def dep(m):
    bot.reply_to(m, f"Send TON to {WALLET}")


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
        bot.reply_to(m, f"win +{amt * 2} TON")
    else:
        bot.reply_to(m, f"lose -{amt} TON")


bot.infinity_polling()
