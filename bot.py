import os
import asyncio
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5072932186
WHATSAPP_LINK = "https://t.me/addlist/h8TIXckNSWdmZTBk"
WEBSITE_LINK = "https://www.brokeraccountguide.com"

# ================= USER STORAGE =================
def load_users():
    try:
        with open("users.json", "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(list(users), f)

USERS = load_users()

# ================= ADMIN MODE =================
ADMIN_BROADCAST_MODE = set()

# ================= FUNCTIONS =================

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    join_kb = [[InlineKeyboardButton("JOIN NOW 👇✅", url=WHATSAPP_LINK)]]
    
    text = "<b>⚠️ Reminder: Join Our Official Channel!</b>\n\nDon't miss our daily Gold Signals and VIP updates. Click below to join now! 🚀"
    
    try:
        await context.bot.send_message(
            chat_id=job.chat_id,
            text=text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(join_kb)
        )
    except:
        pass

# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    chat_id = update.effective_message.chat_id

    # ✅ SAVE USER PERMANENTLY
    USERS.add(chat_id)
    save_users(USERS)

    # 🔻 Keyboard (Admin vs User)
    if update.effective_user.id == ADMIN_ID:
        reply_kb = [
            ["🎁 Claim Your FREE Premium Gold VIP Access Now"],
            ["📢 Admin Broadcast"]
        ]
    else:
        reply_kb = [["🎁 Claim Your FREE Premium Gold VIP Access Now"]]

    bottom_button = ReplyKeyboardMarkup(reply_kb, resize_keyboard=True)

    await update.message.reply_text(
        text=f"Hey, <b>{user_name}</b> !",
        parse_mode='HTML',
        reply_markup=bottom_button
    )

    # WhatsApp Join Button
    join_kb = [[InlineKeyboardButton("JOIN NOW 👇✅", url=WHATSAPP_LINK)]]

    await update.message.reply_text(
        text="<b>Join Our Channel For Daily 3-5 XAUUSD GOLD Signals 👇👇</b>",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(join_kb)
    )

    # Reminder setup
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

    context.job_queue.run_repeating(
        send_reminder,
        interval=900,
        first=900,
        chat_id=chat_id,
        name=str(chat_id)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    text = update.message.text

    # 🎁 Normal Button
    if text == "🎁 Claim Your FREE Premium Gold VIP Access Now":
        response_text = f"<b>{user_name}</b> 🚀 Unlock Your FREE Premium Gold VIP Membership"
        website_button = [[InlineKeyboardButton("JOIN NOW ✅", url=WEBSITE_LINK)]]

        await update.message.reply_text(
            text=response_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(website_button)
        )

    # 📢 Admin Broadcast Button
    elif text == "📢 Admin Broadcast" and user_id == ADMIN_ID:
        ADMIN_BROADCAST_MODE.add(user_id)

        await update.message.reply_text(
            "Send or forward any message now.\nIt will be sent to ALL users 🚀"
        )

    # 📤 Broadcast Mode Active
    elif user_id in ADMIN_BROADCAST_MODE:
        ADMIN_BROADCAST_MODE.remove(user_id)

        for user in USERS:
            try:
                await update.message.copy(chat_id=user)
            except:
                pass

        await update.message.reply_text("✅ Message sent to all users!")

# ================= MAIN =================

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN is missing!")
    else:
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        print("Bot is LIVE 🔥 (Admin Broadcast + Permanent Users)")
        app.run_polling(drop_pending_updates=True)
