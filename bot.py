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
    
    # Hey, simple rahega aur name Bold hoga
    # Markdown (V1) use kar rahe hain jo '!' par error nahi deta
    greeting_text = f"Hey, *{user_name}* !"
    
    try:
        await update.message.reply_text(
            text=greeting_text, 
            parse_mode='Markdown'
        )
    except Exception as e:
        # Agar koi masla ho to simple text bhej de
        await update.message.reply_text(f"Hey, {user_name} !")

async def handle_admin_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Aapka signal logic yahan rahega
    pass

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN is missing!")
    else:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_msg))
        
        print("Bot is starting...")
        # drop_pending_updates=True conflict error ko khatam karta hai
        app.run_polling(drop_pending_updates=True)
        
