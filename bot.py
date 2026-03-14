import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Config
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5072932186  # Aapka ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # User ka naam nikalna
    user_name = update.effective_user.first_name
    # Greeting Message
    await update.message.reply_text(f"Hey, **{user_name}** !", parse_mode='Markdown')

async def handle_admin_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Yahan aapka signal logic aayega jo maine pehle diya tha
    pass

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN is missing in Environment Variables!")
    else:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_msg))
        app.run_polling()
        
