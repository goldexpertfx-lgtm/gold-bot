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
    
    # 2. Join Message (Bold Text + Inline Button)
    # Is ke saath niche bada VIP wala button bhi activate ho jayega
    join_kb = [[InlineKeyboardButton("JOIN NOW 👇✅", url=VIP_LINK)]]
    
    # Bada button niche wala
    reply_kb = [["🎁 Claim Your FREE Premium Gold VIP Access Now"]]
    
    await update.message.reply_text(
        text="<b>Join Whatsapp Channel 👇👇</b>",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(join_kb)
    )
    
    # Bada button show karne ke liye chota sa message
    await update.message.reply_text(
        text=".", 
        reply_markup=ReplyKeyboardMarkup(reply_keyboard=reply_kb, resize_keyboard=True)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    text = update.message.text

    # Jab koi VIP Access wala button dabaye
    if text == "🎁 Claim Your FREE Premium Gold VIP Access Now":
        # Name show hoga phir Membership wala text
        response_text = f"<b>{user_name}</b> 🚀 Unlock Your FREE Premium Gold VIP Membership"
        
        # Button mein Bold text "JOIN NOW ✅"
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
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("Bot is live with VIP features...")
        app.run_polling(drop_pending_updates=True)
        
