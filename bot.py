import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5072932186
WHATSAPP_LINK = "https://whatsapp.com/channel/0029Vb5eRVjGzzKNnL7c050y"

# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    
    # --- MESSAGE 1: Greeting (Bold Name) ---
    await update.message.reply_text(f"Hey, <b>{user_name}</b> !", parse_mode='HTML')
    
    # --- MESSAGE 2: Join Whatsapp Message (Bold Text + Button) ---
    # Saath mein niche bada 'GOLD SIGNALS' button bhi attach kar diya hai
    join_kb = [[InlineKeyboardButton("JOIN NOW 👇✅", url=WHATSAPP_LINK)]]
    
    reply_kb = [["GOLD SIGNALS ✅"]]
    
    await update.message.reply_text(
        text="<b>Join Whatsapp Channel 👇👇</b>",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(join_kb)
    )
    
    # Niche wala bada button (Reply Keyboard) baghair kisi extra text ke bhejna
    await update.message.reply_text(
        text=".", # Chota sa dot ya koi emoji de dein taaki button show ho jaye
        reply_markup=ReplyKeyboardMarkup(reply_keyboard=reply_kb, resize_keyboard=True)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    text = update.message.text

    # Jab koi "GOLD SIGNALS ✅" button press kare
    if text == "GOLD SIGNALS ✅":
        response_text = f"<b>{user_name}</b> Here is our Gold Signals link For You 🤗"
        button = [[InlineKeyboardButton("JOIN NOW ✅", url=WHATSAPP_LINK)]]
        
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
        
        print("Bot is live...")
        app.run_polling(drop_pending_updates=True)
        
