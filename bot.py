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
    
    # --- MESSAGE 2: Join Text with Button ---
    # Text bold hoga aur link sirf button mein hoga
    join_text = "<b>Join Whatsapp Channel 👇👇</b>"
    
    keyboard = [
        [InlineKeyboardButton("JOIN NOW 👇✅", url=whatsapp_link)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text=join_text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def handle_admin_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Signal logic aapka admin check ke saath yahan ayega
    pass

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable is missing!")
    else:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_msg))
        
        print("Bot is live and running...")
        # drop_pending_updates=True conflict errors ko avoid karne ke liye
        app.run_polling(drop_pending_updates=True)
        
