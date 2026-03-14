import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5072932186
VIP_LINK = "https://www.brokeraccountguide.com"

# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    
    # 1. Greeting Message (Bold Name)
    await update.message.reply_text(f"Hey, <b>{user_name}</b> !", parse_mode='HTML')
    
    # 2. Bada Button (Niche wala) - Ise hum har message ke saath attach kar sakte hain
    reply_kb = [["🎁 Claim Your FREE Premium Gold VIP Access Now"]]
    # one_time_keyboard=False taaki button hamesha nazar aaye
    main_button = ReplyKeyboardMarkup(reply_kb, resize_keyboard=True, one_time_keyboard=False)
    
    # 3. Join Message (Bold Text + Inline Button)
    join_kb = [[InlineKeyboardButton("JOIN NOW 👇✅", url=VIP_LINK)]]
    
    await update.message.reply_text(
        text="<b>Join Whatsapp Channel 👇👇</b>",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(join_kb)
    )
    
    # Button ko "Force Show" karne ke liye message
    await update.message.reply_text(
        text="👇 Click the button below to claim your access", 
        reply_markup=main_button
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    text = update.message.text

    if text == "🎁 Claim Your FREE Premium Gold VIP Access Now":
        response_text = f"<b>{user_name}</b> 🚀 Unlock Your FREE Premium Gold VIP Membership"
        button = [[InlineKeyboardButton("JOIN NOW ✅", url=VIP_LINK)]]
        
        await update.message.reply_text(
            text=response_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(button)
        )

# ================= MAIN =================

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN is missing!")
    else:
        # drop_pending_updates=True hamesha conflict khatam karne mein madad karta hai
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("Bot is LIVE...")
        app.run_polling(drop_pending_updates=True)
        
