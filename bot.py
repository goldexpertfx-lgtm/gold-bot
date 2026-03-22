import os
import asyncio
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1826809762
WHATSAPP_LINK = "https://whatsapp.com/channel/0029Vb5eRVjGzzKNnL7c050y"
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

# ================= FUNCTIONS =================

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Har 15 mins baad reminder bhejega"""
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

# ================= BROADCAST =================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    message = " ".join(context.args)

    if not message:
        await update.message.reply_text("Use like:\n/broadcast your message")
        return

    for user in USERS:
        try:
            await context.bot.send_message(
                chat_id=user,
                text=message,
                parse_mode='HTML'
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
    
    # Bottom Bada Button Setup
    reply_kb = [["🎁 Claim Your FREE Premium Gold VIP Access Now"]]
    bottom_button = ReplyKeyboardMarkup(reply_kb, resize_keyboard=True)
    
    await update.message.reply_text(
        text=f"Hey, <b>{user_name}</b> !", 
        parse_mode='HTML',
        reply_markup=bottom_button
    )
    
    join_kb = [[InlineKeyboardButton("JOIN NOW 👇✅", url=WHATSAPP_LINK)]]
    
    await update.message.reply_text(
        text="<b>Join Whatsapp Channel 👇👇</b>",
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
    user_name = update.effective_user.first_name
    text = update.message.text

    if text == "🎁 Claim Your FREE Premium Gold VIP Access Now":
        response_text = f"<b>{user_name}</b> 🚀 Unlock Your FREE Premium Gold VIP Membership"
        website_button = [[InlineKeyboardButton("JOIN NOW ✅", url=WEBSITE_LINK)]]
        
        await update.message.reply_text(
            text=response_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(website_button)
        )

# ================= MAIN =================

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN is missing!")
    else:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("broadcast", broadcast))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("Bot is LIVE 🔥 (Permanent Users Enabled)")
        app.run_polling(drop_pending_updates=True)
