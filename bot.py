#!/usr/bin/env python3
"""
GOLD BOT - PYTHON 3.14 COMPATIBLE
"""

import threading
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
BOT_TOKEN = "8284715892:AAHOugCMkrfFK0Ehd6WVlYgW5CfMSU9K-5M"
CHANNEL_ID = -1003742118245
ADMIN_ID = 5072932186

# APIs
API_URLS = [
    "https://api.exchangerate-api.com/v4/latest/XAU",
    "https://www.floatrates.com/daily/xau.json",
    "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/xau.json",
]

# ================= LOGGING =================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================= STATE =================
active_trade = None
last_sent_price = None
tracking_running = False
trade_counter = 0
last_known_price = None
bot_instance = None

# ================= PRICE FETCH =================
def fetch_price():
    global last_known_price
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for url in API_URLS:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                price = None
                
                if "rates" in data and "USD" in data["rates"]:
                    price = float(data["rates"]["USD"])
                elif "usd" in data:
                    if isinstance(data["usd"], dict) and "rate" in data["usd"]:
                        price = float(data["usd"]["rate"])
                    else:
                        price = float(data["usd"])
                
                if price and 1800 < price < 10000:
                    last_known_price = round(price, 2)
                    return last_known_price
                    
        except Exception as e:
            logger.error(f"API failed: {e}")
            continue
    
    return last_known_price

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Gold Bot Online!\n\n"
        "Commands:\n"
        "BUY 5078 - Create signal\n"
        "SELL 5080 - Create signal\n"
        "PRICE - Check price"
    )

async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = fetch_price()
    if price:
        await update.message.reply_text(f"Live Price: {price}")
    else:
        await update.message.reply_text("Failed to fetch")

# ================= AUTO JOIN =================
async def approve_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.approve_chat_join_request(
            chat_id=update.chat_join_request.chat.id,
            user_id=update.chat_join_request.from_user.id,
        )
    except:
        pass

# ================= MESSAGE HANDLER =================
async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_trade, last_sent_price, tracking_running, trade_counter, last_known_price, bot_instance
    
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if user_id != ADMIN_ID:
        return
    
    text_upper = text.upper()
    
    if text_upper == "/START":
        await start(update, context)
        return
    
    if text_upper == "PRICE":
        await price_cmd(update, context)
        return
    
    trade_type = None
    if text_upper.startswith("BUY"):
        trade_type = "BUY"
    elif text_upper.startswith("SELL"):
        trade_type = "SELL"
    
    if not trade_type:
        return
    
    numbers = re.findall(r'\d{4}\.?\d{0,2}', text)
    manual_price = None
    if numbers:
        try:
            p = float(numbers[0])
            if 1800 < p < 10000:
                manual_price = p
        except:
            pass
    
    if manual_price:
        price = manual_price
    else:
        price = fetch_price()
    
    if not price:
        await update.message.reply_text("Failed to get price")
        return
    
    entry = round(price, 2)
    
    if active_trade:
        old_id = active_trade.get("trade_id")
        try:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"Trade #{old_id} stopped"
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
        "trade_id": trade_counter,
        "type": trade_type,
        "entry": entry,
        "tp1": tp1,
        "tp2": tp2,
        "sl": sl,
        "tp1_hit": False,
        "tp2_hit": False,
        "sl_hit": False,
        "message_id": None
    }
    
    last_sent_price = entry
    last_known_price = entry
    
    try:
        msg = await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"XAUUSD {trade_type} {entry}\n\nTP {tp1}\nTP {tp2}\n\nSL {sl}"
        )
        
        active_trade["message_id"] = msg_id = msg.message_id
        
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text="Use lot size according to account equity",
            reply_to_message_id=msg_id
        )
        
        if not tracking_running:
            tracking_running = True
            threading.Thread(target=tracker, daemon=True).start()
        
        await update.message.reply_text(
            f"Signal #{trade_counter} Active\nEntry: {entry} | TP1: {tp1} | TP2: {tp2} | SL: {sl}"
        )
        
    except Exception as e:
        logger.error(f"Error: {e}")
        active_trade = None

# ================= TRACKER =================
def tracker():
    global active_trade, last_sent_price, tracking_running, last_known_price
    
    logger.info("Tracker started")
    
    while True:
        try:
            if not active_trade:
                time.sleep(2)
                continue
            
            trade = active_trade
            trade_id = trade["trade_id"]
            msg_id = trade["message_id"]
            
            current_price = fetch_price()
            
            if not current_price:
                time.sleep(5)
                continue
            
            if not active_trade or active_trade.get("trade_id") != trade_id:
                break
            
            if trade["type"] == "BUY":
                if current_price >= last_sent_price + 1:
                    new_level = int(current_price)
                    temp = int(last_sent_price) + 1
                    
                    while temp <= new_level:
                        try:
                            bot_instance.send_message(
                                chat_id=CHANNEL_ID,
                                text=f"XAUUSD active Price {temp}",
                                reply_to_message_id=msg_id
                            )
                            last_sent_price = temp
                        except Exception as e:
                            logger.error(f"Send error: {e}")
                        
                        temp += 1
                        time.sleep(0.3)
                
                if current_price >= trade["tp1"] and not trade["tp1_hit"]:
                    trade["tp1_hit"] = True
                    try:
                        bot_instance.send_message(
                            chat_id=CHANNEL_ID,
                            text="XAUUSD TP1 hit 50+ pips",
                            reply_to_message_id=msg_id
                        )
                    except:
                        pass
                
                if current_price >= trade["tp2"] and not trade["tp2_hit"]:
                    trade["tp2_hit"] = True
                    try:
                        bot_instance.send_message(
                            chat_id=CHANNEL_ID,
                            text="XAUUSD TP2 hit 100+ pips",
                            reply_to_message_id=msg_id
                        )
                    except:
                        pass
                    active_trade = None
                    break
                
                if current_price <= trade["sl"] and not trade["sl_hit"]:
                    trade["sl_hit"] = True
                    try:
                        bot_instance.send_message(
                            chat_id=CHANNEL_ID,
                            text="SL HIT",
                            reply_to_message_id=msg_id
                        )
                    except:
                        pass
                    active_trade = None
                    break
            
            else:  # SELL
                if current_price <= last_sent_price - 1:
                    new_level = int(current_price)
                    temp = int(last_sent_price) - 1
                    
                    while temp >= new_level:
                        try:
                            bot_instance.send_message(
                                chat_id=CHANNEL_ID,
                                text=f"XAUUSD active Price {temp}",
                                reply_to_message_id=msg_id
                            )
                            last_sent_price = temp
                        except Exception as e:
                            logger.error(f"Send error: {e}")
                        
                        temp -= 1
                        time.sleep(0.3)
                
                if current_price <= trade["tp1"] and not trade["tp1_hit"]:
                    trade["tp1_hit"] = True
                    try:
                        bot_instance.send_message(
                            chat_id=CHANNEL_ID,
                            text="XAUUSD TP1 hit 50+ pips",
                            reply_to_message_id=msg_id
                        )
                    except:
                        pass
                
                if current_price <= trade["tp2"] and not trade["tp2_hit"]:
                    trade["tp2_hit"] = True
                    try:
                        bot_instance.send_message(
                            chat_id=CHANNEL_ID,
                            text="XAUUSD TP2 hit 100+ pips",
                            reply_to_message_id=msg_id
                        )
                    except:
                        pass
                    active_trade = None
                    break
                
                if current_price >= trade["sl"] and not trade["sl_hit"]:
                    trade["sl_hit"] = True
                    try:
                        bot_instance.send_message(
                            chat_id=CHANNEL_ID,
                            text="SL HIT",
                            reply_to_message_id=msg_id
                        )
                    except:
                        pass
                    active_trade = None
                    break
            
            last_known_price = current_price
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"Tracker error: {e}")
            time.sleep(5)
    
    tracking_running = False
    logger.info("Tracker stopped")

# ================= MAIN =================
def main():
    global bot_instance
    
    logger.info("Starting Gold Bot")
    
    application = Application.builder().token(BOT_TOKEN).build()
    bot_instance = application.bot
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("price", price_cmd))
    application.add_handler(ChatJoinRequestHandler(approve_join))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    
    logger.info("Bot is running")
    
    application.run_polling()

if __name__ == "__main__":
    main()
        
