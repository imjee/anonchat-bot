import os
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8132147727:AAFJT1PR4bg8nXmXuukmidzlgQU73lph-NM"
ADMIN_ID = 8021896750

users = {}
pairs = {}
reported_users = set()
user_last_message_time = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in users:
        await update.message.reply_text("Kamu sudah terdaftar. Gunakan /find untuk mencari pasangan.")
        return

    await update.message.reply_text("👤 Nama kamu?")
    context.user_data["step"] = "name"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = update.message.text

    now = time.time()
    if user_id in user_last_message_time and now - user_last_message_time[user_id] < 2:
        return
    user_last_message_time[user_id] = now

    if "step" in context.user_data:
        step = context.user_data["step"]
        if step == "name":
            context.user_data["name"] = msg
            context.user_data["step"] = "age"
            await update.message.reply_text("🎂 Umur kamu?")
        elif step == "age":
            context.user_data["age"] = msg
            context.user_data["step"] = "gender"
            await update.message.reply_text("🚻 Gender kamu? (Pria/Wanita)")
        elif step == "gender":
            context.user_data["gender"] = msg
            context.user_data["step"] = "city"
            await update.message.reply_text("🏙 Kamu tinggal di kota mana?")
        elif step == "city":
            context.user_data["city"] = msg
            users[user_id] = {
                "name": context.user_data["name"],
                "age": context.user_data["age"],
                "gender": context.user_data["gender"],
                "city": msg,
                "username": update.effective_user.username or "-"
            }
            del context.user_data["step"]
            await update.message.reply_text("✅ Profil disimpan. Gunakan /find untuk mencari pasangan.")
        return

    if user_id in pairs:
        partner_id = pairs[user_id]
        if partner_id in reported_users:
            await update.message.reply_text("Pasanganmu telah dilaporkan.")
            return
        try:
            await context.bot.send_message(chat_id=partner_id, text=msg)
        except:
            pass
    else:
        await update.message.reply_text("Kamu belum terhubung. Gunakan /find")

async def find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in users:
        await update.message.reply_text("Kamu belum daftar. Gunakan /start")
        return

    if user_id in pairs:
        await update.message.reply_text("Kamu sedang terhubung.")
        return

    for uid, data in users.items():
        if uid != user_id and uid not in pairs and users[uid]["city"] == users[user_id]["city"]:
            pairs[user_id] = uid
            pairs[uid] = user_id
            await context.bot.send_message(uid, f"🔗 Terhubung dengan {users[user_id]['name']} ({users[user_id]['age']}), @{users[user_id]['username']}")
            await update.message.reply_text(f"🔗 Terhubung dengan {users[uid]['name']} ({users[uid]['age']}), @{users[uid]['username']}")
            return

    await update.message.reply_text("🔍 Mencari pasangan...")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in pairs:
        await update.message.reply_text("Kamu belum terhubung.")
        return

    partner_id = pairs[user_id]
    del pairs[user_id]
    del pairs[partner_id]

    await update.message.reply_text("❌ Kamu memutuskan pasangan.")
    await context.bot.send_message(partner_id, "❌ Pasangan memutuskan koneksi.")

async def rematch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔁 Rematch memerlukan donasi. Fitur dalam pengembangan.")

async def report_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in pairs:
        await update.message.reply_text("Kamu tidak sedang terhubung.")
        return
    partner_id = pairs[user_id]
    reported_users.add(partner_id)
    await update.message.reply_text("🚨 Pasangan telah dilaporkan.")
    await context.bot.send_message(ADMIN_ID, f"User {user_id} melaporkan pasangan {partner_id}")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(f"👮 Admin Panel\nTotal user: {len(users)}\nPasangan aktif: {len(pairs)//2}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Gunakan /broadcast <pesan>")
        return
    msg = "📢 Pesan admin:\n" + " ".join(context.args)
    for uid in users:
        try:
            await context.bot.send_message(uid, msg)
        except:
            pass
    await update.message.reply_text("✅ Broadcast dikirim.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start - Daftar\n/find - Cari pasangan\n/stop - Putus\n/rematch - Pasangan sebelumnya\n/report - Laporkan pasangan\n/admin - Panel admin")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("find", find))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("rematch", rematch))
    app.add_handler(CommandHandler("report", report_user))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()

if _name_ == "_main_":
    from keep_alive import keep_alive
    keep_alive()
    main()
