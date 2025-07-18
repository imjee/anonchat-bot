import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)
from keep_alive import keep_alive

# Data user & pasangan
users = {}
pairing_queue = []
active_pairs = {}
skipped_pairs = {}

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

def get_user_info(user_id):
    return users.get(user_id, {"name": "", "age": "", "gender": "", "city": ""})

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Selamat datang di Bot Chat Anonim Satu Kota!\n\n"
        "Ketik /daftar untuk mulai dan cari pasangan ngobrol."
    )

async def daftar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users[update.effective_user.id] = {}
    await update.message.reply_text("📛 Masukkan nama kamu:")
    return

async def input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in users:
        await update.message.reply_text("Ketik /daftar dulu.")
        return

    data = users[uid]
    msg = update.message.text.strip()

    if "name" not in data:
        data["name"] = msg
        await update.message.reply_text("🎂 Berapa umur kamu?")
    elif "age" not in data:
        if not msg.isdigit():
            await update.message.reply_text("Umur harus berupa angka.")
            return
        data["age"] = msg
        await update.message.reply_text("🚻 Jenis kelamin? (L/P)")
    elif "gender" not in data:
        if msg.upper() not in ["L", "P"]:
            await update.message.reply_text("Masukkan 'L' atau 'P'")
            return
        data["gender"] = msg.upper()
        await update.message.reply_text("🏙 Kamu tinggal di kota apa?")
    elif "city" not in data:
        data["city"] = msg.lower()
        await update.message.reply_text("✅ Data disimpan. Mencari pasangan...")
        await cari_pasangan(uid, context)

async def cari_pasangan(uid, context):
    user = users[uid]
    for other_id in pairing_queue:
        if other_id != uid and users[other_id]["city"] == user["city"]:
            pairing_queue.remove(other_id)
            active_pairs[uid] = other_id
            active_pairs[other_id] = uid
            await context.bot.send_message(uid, f"🎉 Ditemukan pasangan!\nKamu sedang ngobrol dengan seseorang dari {user['city'].title()}.")
            await context.bot.send_message(other_id, "🎉 Pasangan ditemukan. Selamat ngobrol!")
            return

    pairing_queue.append(uid)
    await context.bot.send_message(uid, "🔍 Menunggu pasangan dari kota yang sama...")

async def kirim_pesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in active_pairs:
        pasangan_id = active_pairs[uid]
        try:
            await context.bot.send_message(pasangan_id, f"💬: {update.message.text}")
        except:
            await update.message.reply_text("❌ Gagal kirim pesan.")
    else:
        await update.message.reply_text("❌ Kamu belum punya pasangan.\nKetik /daftar untuk mulai.")

async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    pasangan = active_pairs.pop(uid, None)
    if pasangan:
        active_pairs.pop(pasangan, None)
        skipped_pairs[uid] = pasangan
        await context.bot.send_message(uid, "⏭ Kamu skip pasangan.")
        await context.bot.send_message(pasangan, "🚫 Pasanganmu meninggalkan chat.")
        await cari_pasangan(uid, context)
        await cari_pasangan(pasangan, context)
    else:
        await update.message.reply_text("❌ Kamu belum sedang chatting.")

async def rematch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in skipped_pairs:
        pasangan = skipped_pairs[uid]
        await context.bot.send_message(uid, "🔄 Untuk rematch, silakan donasi ke: dana 08xxxxxxx (contoh).")
        await context.bot.send_message(uid, "🕐 Setelah donasi, kirim bukti ke admin.")
    else:
        await update.message.reply_text("❌ Tidak ada pasangan yang bisa dirematch.")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in active_pairs:
        pasangan = active_pairs[uid]
        data = users.get(pasangan)
        if data:
            await update.message.reply_text(
                f"ℹ Info pasanganmu:\n"
                f"Nama: {data['name']}\n"
                f"Umur: {data['age']}\n"
                f"Gender: {data['gender']}\n"
                f"Kota: {data['city'].title()}"
            )
        else:
            await update.message.reply_text("❌ Data pasangan tidak ditemukan.")
    else:
        await update.message.reply_text("❌ Kamu belum terhubung dengan pasangan.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    pasangan = active_pairs.pop(uid, None)
    if pasangan:
        active_pairs.pop(pasangan, None)
        await context.bot.send_message(uid, "🚫 Chat dihentikan.")
        await context.bot.send_message(pasangan, "🚫 Pasangan kamu keluar.")
    else:
        await update.message.reply_text("❌ Kamu tidak sedang dalam sesi chat.")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != ADMIN_ID:
        await update.message.reply_text("❌ Akses hanya untuk admin.")
        return
    total_users = len(users)
    total_active = len(active_pairs) // 2
    await update.message.reply_text(
        f"👑 Admin Panel:\n"
        f"- Jumlah user terdaftar: {total_users}\n"
        f"- Chat aktif: {total_active} pasang"
    )

def main():
    keep_alive()
    app = ApplicationBuilder().token(os.getenv("TOKEN")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("daftar", daftar))
    app.add_handler(CommandHandler("skip", skip))
    app.add_handler(CommandHandler("rematch", rematch))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, input_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, kirim_pesan))

    app.run_polling()

if _name_ == "_main_":
    main()
