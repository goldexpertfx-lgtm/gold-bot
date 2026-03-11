import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= CONFIG =================
# Ye Token Render ki Environment Settings se uthayega
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Yahan apne asli links aur codes likhein
EXNESS_LINK = "https://one.exnessonelink.com/a/gtxdy70by3"
XM_LINK = "https://www.xmwebsite.net/referral?token=E3IeNfn7aa2gpzT6hOA1Iw"
OCTAFX_LINK = "https://octasl.click/iGWPxkbrznp"

PARTNER_CODES = """
✨ **Official Partner Codes** ✨

🔹 **Exness:** `gtxdy70by3`
🔹 **XM:** `E3IeNfn7aa2gpzT6hOA1Iw`
🔹 **OctaFX:** `iGWPxkbrznp`

*Copy and use these codes during registration.*
"""

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💎 Open Exness Account", url=EXNESS_LINK)],
        [InlineKeyboardButton("📈 Open XM Account", url=XM_LINK)],
        [InlineKeyboardButton("🌍 Open OctaFX Account", url=OCTAFX_LINK)],
        [InlineKeyboardButton("📋 View Partner Codes", callback_data='show_codes')],
        [InlineKeyboardButton("👨‍💻 Contact Support", url="https://t.me/FxJack")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "👋 **Welcome to Gold Expert FX!**\n\n"
        "Start trading with the world's most trusted brokers. "
        "Register using our links below to join our **VIP Signal Group** for free!"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(PARTNER_CODES, parse_mode='Markdown')

def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN is missing!")
        return
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("codes", codes))
    
    print("Bot is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
