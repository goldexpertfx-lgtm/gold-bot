import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Config
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5072932186

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # User ka naam nikalna
    user_name = update.effective_user.first_name
    
    # WhatsApp Link
    whatsapp_link = "https://whatsapp.com/channel/0029Vb5eRVjGzzKNnL7c050y"
    
    # --- MESSAGE 1: Greeting ---
    greeting_text = f"Hey, <b>{user_name}</b> !"
    await update.message.reply_text(text=greeting_text, parse_mode='HTML')
    
    # --- MESSAGE 2: Button Wala Message ---
    # Is mein link text bold hai aur sath button bhi hai
    button_text = f"<b>{whatsapp_link}</b>"
    
    keyboard = [
        [InlineKeyboardButton("JOIN NOW 👇✅", url=whatsapp_link)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text=button_text,
        parse_mode='HTML',
        reply_markup=reply_markup,
        disable_web_page_preview=True # Preview off taaki button saaf dikhayi de
    )

async def handle_admin_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Signal logic yahan add karein
    pass

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN is missing!")
    else:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_msg))
        
        print("Bot is starting...")
        # drop_pending_updates=True conflict error fix karne ke liye
        app.run_polling(drop_pending_updates=True)
        
