import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ... (Baaki purana Config aur API logic yahan rahega) ...

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # User ka pehla naam nikalna
    user_name = update.effective_user.first_name
    
    # Bold style mein greeting message
    # Prince ki jagah user ka apna naam aayega
    greeting_text = f"Hey, **{user_name}** !"
    
    await update.message.reply_text(greeting_text, parse_mode='Markdown')

# Main function mein handler add karein
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Start command handler
    app.add_handler(CommandHandler("start", start))
    
    # Admin signal handler (Jo pehle banaya tha)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_msg))
    
    app.run_polling()
    
