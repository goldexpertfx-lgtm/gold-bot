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
    
    # 2. Join Message (Bold Text + Button)
    join_kb = [[InlineKeyboardButton("JOIN NOW 👇✅", url=VIP_LINK)]]
    
    # --- REPLY KEYBOARD (Niche wala bada button jaha message type karte hain) ---
    # resize_keyboard=True se button ka size chota aur sahi ho jata hai
    reply_kb = [["🎁 Claim Your FREE Premium Gold VIP Access Now"]]
    main_button = ReplyKeyboardMarkup(reply_kb, resize_keyboard=True)
    
    await update.message.reply_text(
        text="<b>Join Whatsapp Channel 👇👇</b>",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(join_kb)
    )
    
    # Button ko active karne ke liye ek chota message bhejna
    await update.message.reply_text(
        text="Click the button below to get started! 👇", 
        reply_markup=main_button
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    text = update.message.text

    # Jab koi bada button dabaye
    if text == "🎁 Claim Your FREE Premium Gold VIP Access Now":
        # Name show hoga (Bold) aur phir membership text
        response_text = f"<b>{user_name}</b> 🚀 Unlock Your FREE Premium Gold VIP Membership"
        
        # Link button ke sath
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
        
        print("Bot is running with bottom button...")
        app.run_polling(drop_pending_updates=True)
        
