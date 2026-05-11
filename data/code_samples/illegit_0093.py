# v0.1
import telebot, random
bot = telebot.TeleBot("TOKEN")
WALLET = "0x7a08f50fcbacb7aDdC3b9Cb9BbADd8d7"
balances = {}


@bot.message_handler(commands=["dep"])
def dep(m):
    bot.reply_to(m, f"Send ETH to {WALLET}")


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
        bot.reply_to(m, f"win +{amt * 2} ETH")
    else:
        bot.reply_to(m, f"lose -{amt} ETH")


bot.infinity_polling()
