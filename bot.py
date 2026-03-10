#!/usr/bin/env python3
"""
GOLD BOT - PYTHON 3.14 COMPATIBLE
"""

import logging
import time
import re
import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ChatJoinRequestHandler,
)

# ================= CONFIG =================
BOT_TOKEN = "8284715892:AAFzE9pOxgamaTvQT1-8vA80F-cnGQ_KsgI"
CHANNEL_ID = -1003742118245
ADMIN_ID = 5072932186

# ================= LOGGING =================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================= STATE =================
active_trade = None
last_sent_price = None
trade_counter = 0
last_known_price = None

# ================= GET PRICE =================
def get_price():
    global last_known_price
    try:
        url = "https://api.exchangerate-api.com/v4/latest/XAU"
        r = requests.get(url, timeout=10)
        data = r.json()
        price = float(data["rates"]["USD"])
        if 1800 < price < 10000:
            last_known_price = round(price, 2)
            return last_known_price
    except Exception as e:
        logger.error(f"Price error: {e}")
    return last_known_price

# ================= COMMANDS =================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Gold Bot Online!\n\n"
        "BUY 5078 - Create buy signal\n"
        "SELL 5080 - Create sell signal\n"
        "PRICE - Check price"
    )

async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = get_price()
    if p:
        await update.message.reply_text(f"Price: {p}")
    else:
        await update.message.reply_text("Error")

# ================= JOIN REQUEST =================
async def join_req(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.approve_chat_join_request(
            chat_id=update.chat_join_request.chat.id,
            user_id=update.chat_join_request.from_user.id,
        )
    except:
        pass

# ================= MESSAGE HANDLER =================
async def msg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_trade, last_sent_price, trade_counter, last_known_price
    
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    
    text = update.message.text.strip().upper()
    
    if text == "/START":
        await start_cmd(update, context)
        return
    
    if text == "PRICE":
        await price_cmd(update, context)
        return
    
    trade_type = None
    if text.startswith("BUY"):
        trade_type = "BUY"
    elif text.startswith("SELL"):
        trade_type = "SELL"
    
    if not trade_type:
        return
    
    nums = re.findall(r'\d{4}\.?\d{0,2}', text)
    manual = None
    if nums:
        try:
            p = float(nums[0])
            if 1800 < p < 10000:
                manual = p
        except:
            pass
    
    price = manual if manual else get_price()
    if not price:
        await update.message.reply_text("Failed to get price")
        return
    
    entry = round(price, 2)
    
    if active_trade:
        try:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"Trade #{active_trade['id']} stopped"
            )
        except:
            pass
        active_trade = None
        time.sleep(1)
    
    if trade_type == "BUY":
        tp1 = round(entry + 5, 2)
        tp2 = round(entry + 10, 2)
        sl = round(entry - 10, 2)
    else:
        tp1 = round(entry - 5, 2)
        tp2 = round(entry - 10, 2)
        sl = round(entry + 10, 2)
    
    trade_counter += 1
    active_trade = {
        "id": trade_counter,
        "type": trade_type,
        "entry": entry,
        "tp1": tp1,
        "tp2": tp2,
        "sl": sl,
        "tp1_hit": False,
        "tp2_hit": False,
        "sl_hit": False,
        "msg_id": None
    }
    
    last_sent_price = entry
    last_known_price = entry
    
    try:
        msg = await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"XAUUSD {trade_type} {entry}\n\nTP {tp1}\nTP {tp2}\n\nSL {sl}"
        )
        active_trade["msg_id"] = msg.message_id
        
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text="Use proper lot size",
            reply_to_message_id=msg.message_id
        )
        
        await update.message.reply_text(
            f"Signal #{trade_counter} Active\nEntry: {entry}\nTP1: {tp1}\nTP2: {tp2}\nSL: {sl}"
        )
        
    except Exception as e:
        logger.error(f"Error: {e}")
        active_trade = None

# ================= MAIN =================
def main():
    logger.info("Gold Bot Starting...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("price", price_cmd))
    app.add_handler(ChatJoinRequestHandler(join_req))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_handler))
    
    logger.info("Bot running")
    app.run_polling()

if __name__ == "__main__":
    main()
    
