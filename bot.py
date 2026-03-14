import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Config
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5072932186
WHATSAPP_LINK = "https://whatsapp.com/channel/0029Vb5eRVjGzzKNnL7c050y"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    
    # --- MESSAGE 1: Greeting ---
    await update.message.reply_text(f"Hey, <b>{user_name}</b> !", parse_mode='HTML')
    
    # --- MESSAGE 2: Join Text with Inline Button ---
    join_keyboard = [[InlineKeyboardButton("JOIN NOW 👇✅", url=WHATSAPP_LINK)]]
    await update.message.reply_text(
        text="<b>Join Whatsapp Channel 👇👇</b>",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(join_keyboard)
    )

    # --- MESSAGE 3: Reply Keyboard Button (Niche wala bada button) ---
    # Ye button keyboard ki jagah show hoga
    reply_keyboard = [["GOLD SIGNALS ✅"]]
    await update.message.reply_text(
        text="Click below to get signals anytime 👇",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    text = update.message.text

    # Agar koi "GOLD SIGNALS ✅" button dabaye
    if text == "GOLD SIGNALS ✅":
        signal_msg = f"<b>{user_name}</b> Here is our Gold Signals link For You 🤗"
        keyboard = [[InlineKeyboardButton("JOIN NOW ✅", url=WHATSAPP_LINK)]]
        
        await update.message.reply_text(
            text=signal_msg,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Admin Signal Logic (BUY/SELL)
    if user_id == ADMIN_ID:
        cmd = text.upper()
        if "BUY" in cmd or "SELL" in cmd:
            # Yahan purana price fetch aur signal posting ka logic aayega
            await update.message.reply_text("✅ Admin Signal Received (Logic Active)")

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN is missing!")
    else:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("Bot is running perfectly...")
        app.run_polling(drop_pending_updates=True)
        
