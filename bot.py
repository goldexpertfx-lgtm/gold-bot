import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5072932186
WHATSAPP_LINK = "https://whatsapp.com/channel/0029Vb5eRVjGzzKNnL7c050y"
WEBSITE_LINK = "https://www.brokeraccountguide.com"

# ================= FUNCTIONS =================

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Ye function har 15 mins baad message bhejega"""
    job = context.job
    join_kb = [[InlineKeyboardButton("JOIN NOW 👇✅", url=WHATSAPP_LINK)]]
    
    text = (
        "⚠️ **Reminder: Join Our Channel!**\n\n"
        "Don't miss our daily Gold Signals and VIP updates. Click below to join now! 🚀"
    )
    
    await context.bot.send_message(
        chat_id=job.chat_id,
        text=text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(join_kb)
    )

# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    chat_id = update.effective_message.chat_id
    
    # 1. Greeting
    await update.message.reply_text(f"Hey, <b>{user_name}</b> !", parse_mode='HTML')
    
    # 2. Bada Button (Niche wala) - Setup
    reply_kb = [["🎁 Claim Your FREE Premium Gold VIP Access Now"]]
    bottom_button = ReplyKeyboardMarkup(reply_kb, resize_keyboard=True)
    
    # 3. Join Whatsapp Message (Isi ke saath button attach kar diya bina dot ke)
    join_kb = [[InlineKeyboardButton("JOIN NOW 👇✅", url=WHATSAPP_LINK)]]
    
    await update.message.reply_text(
        text="<b>Join Whatsapp Channel 👇👇</b>",
        parse_mode='HTML',
        reply_markup=bottom_button # Yahan bada button activate ho jayega
    )
    
    # Alag se inline button wala message
    await update.message.reply_text(
        text="Click below to join our official channel:",
        reply_markup=InlineKeyboardMarkup(join_kb)
    )

    # --- REMINDER SETUP (15 Minutes) ---
    # Purane jobs clear karna taaki double messages na jayein
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

    # Naya reminder set karna (900 seconds = 15 minutes)
    context.job_queue.run_repeating(send_reminder, interval=900, first=900, chat_id=chat_id, name=str(chat_id))

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
        # JobQueue enable karna zaroori hai reminders ke liye
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("Bot is LIVE with 15-min Reminders...")
        app.run_polling(drop_pending_updates=True)
        
