import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Config
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5072932186

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # User ka naam nikalna
    user_name = update.effective_user.first_name
    
    # WhatsApp Link
    whatsapp_link = "https://whatsapp.com/channel/0029Vb5eRVjGzzKNnL7c050y"
    
    # Greeting aur Bold Link ka message
    # <b> tag se text Bold ho jata hai
    message_text = (
        f"Hey, <b>{user_name}</b> !\n\n"
        f"<b>{whatsapp_link}</b>"
    )
    
    await update.message.reply_text(
        text=message_text, 
        parse_mode='HTML',
        disable_web_page_preview=False  # Isse link ka preview bhi show hoga
    )

async def handle_admin_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Signal logic yahan rahega
    pass

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN is missing!")
    else:
        # Conflict fix karne ke liye drop_pending_updates zaroori hai
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_msg))
        
        print("Bot is starting...")
        app.run_polling(drop_pending_updates=True)
        
