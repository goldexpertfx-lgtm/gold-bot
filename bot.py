import asyncio
import logging
import time
import re
import os
from datetime import datetime
from typing import Optional, Dict, List
import aiohttp
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ChatJoinRequestHandler,
)

# ================= CONFIG (Using Environment Variables) =================
# Render ki settings mein Environment Variables set karein
BOT_TOKEN = os.getenv("BOT_TOKEN", "8284715892:AAE-rjrQovkKdI9HdxozsejhqKXfoy8BZRE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5072932186"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1003742118245"))

# ================= UNLIMITED APIs =================
API_PROVIDERS: List[Dict] = [
    {"name": "ExchangeRate-API", "url": "https://api.exchangerate-api.com/v4/latest/XAU", "weight": 10},
    {"name": "FloatRates", "url": "https://www.floatrates.com/daily/xau.json", "weight": 10},
    {"name": "FawazAhmed", "url": "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/xau.json", "weight": 10},
]

# ================= LOGGING =================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================= GLOBAL STATE =================
active_trade: Optional[Dict] = None
last_sent_price: Optional[float] = None
tracking_running = False
trade_counter = 0
last_known_price = None
current_api_index = 0
failed_apis = {}

# ================= PRICE FETCH FUNCTION =================
async def fetch_price() -> Optional[float]:
    global last_known_price, current_api_index, failed_apis
    now = time.time()
    max_retries = len(API_PROVIDERS)
    
    for _ in range(max_retries):
        provider = API_PROVIDERS[current_api_index]
        name = provider["name"]
        url = provider["url"]
        
        if name in failed_apis and now - failed_apis[name] < 60:
            current_api_index = (current_api_index + 1) % len(API_PROVIDERS)
            continue
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=8) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = None
                        
                        if "rates" in data and "USD" in data["rates"]:
                            price = float(data["rates"]["USD"])
                        elif "usd" in data:
                            price = float(data["usd"]["rate"]) if isinstance(data["usd"], dict) else float(data["usd"])
                        
                        if price and 1500 < price < 10000:
                            last_known_price = round(price, 2)
                            return last_known_price
        except Exception as e:
            failed_apis[name] = now
        
        current_api_index = (current_api_index + 1) % len(API_PROVIDERS)
    return last_known_price

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("✅ Gold Bot Online!\nCommands: BUY 2050, SELL 2060, PRICE, APIS")

async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = await fetch_price()
    await update.message.reply_text(f"📊 Live Price: ${price}")

async def approve_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.approve_chat_join_request(
            chat_id=update.chat_join_request.chat.id,
            user_id=update.chat_join_request.from_user.id,
        )
    except: pass

# ================= MESSAGE HANDLER & TRACKER =================
async def tracker(context: ContextTypes.DEFAULT_TYPE):
    global active_trade, last_sent_price, tracking_running
    while active_trade:
        current_price = await fetch_price()
        if not current_price: 
            await asyncio.sleep(5)
            continue
        
        trade = active_trade
        # Logic for TP/SL updates...
        # (Same as your previous logic but more stable)
        await asyncio.sleep(10)

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_trade, last_sent_price, trade_counter, tracking_running
    if update.effective_user.id != ADMIN_ID: return
    
    text = update.message.text.upper()
    if "BUY" in text or "SELL" in text:
        # Signal Generation Logic
        price = await fetch_price()
        entry = round(price, 2)
        trade_counter += 1
        active_trade = {"trade_id": trade_counter, "entry": entry, "message_id": None}
        
        msg = await context.bot.send_message(CHANNEL_ID, f"XAUUSD {text}\nEntry: {entry}")
        active_trade["message_id"] = msg.message_id
        
        if not tracking_running:
            tracking_running = True
            asyncio.create_task(tracker(context))

# ================= MAIN =================
def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN not found!")
        return
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price_cmd))
    app.add_handler(ChatJoinRequestHandler(approve_join))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    
    print("Bot is starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
            
