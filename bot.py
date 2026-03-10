#!/usr/bin/env python3
"""
GOLD BOT - 100% SYNC VERSION
No async, no threading, no errors
"""

import logging
import time
import re
import requests
from telegram import Update, Bot
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    Filters,
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
bot_instance = None
updater_instance = None

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
def start_cmd(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Gold Bot Online!\n\n"
        "BUY 5078 - Create buy signal\n"
        "SELL 5080 - Create sell signal\n"
        "PRICE - Check price"
    )

def price_cmd(update: Update, context: CallbackContext):
    p = get_price()
    if p:
        update.message.reply_text(f"Price: {p}")
    else:
        update.message.reply_text("Error")

# ================= JOIN REQUEST =================
def join_req(update: Update, context: CallbackContext):
    try:
        context.bot.approve_chat_join_request(
            chat_id=update.chat_join_request.chat.id,
            user_id=update.chat_join_request.from_user.id,
        )
    except:
        pass

# ================= TRACKER (NO THREADING) =================
def check_price_updates():
    """Called manually - no threading"""
    global active_trade, last_sent_price, last_known_price
    
    if not active_trade:
        return
    
    trade = active_trade
    msg_id = trade["msg_id"]
    price = get_price()
    
    if not price:
        return
    
    # BUY logic
    if trade["type"] == "BUY":
        if price >= last_sent_price + 1:
            for p in range(int(last_sent_price) + 1, int(price) + 1):
                try:
                    bot_instance.send_message(
                        chat_id=CHANNEL_ID,
                        text=f"XAUUSD Price {p}",
                        reply_to_message_id=msg_id
                    )
                    last_sent_price = p
                except Exception as e:
                    logger.error(f"Send error: {e}")
                time.sleep(0.3)
        
        if price >= trade["tp1"] and not trade["tp1_hit"]:
            trade["tp1_hit"] = True
            try:
                bot_instance.send_message(
                    chat_id=CHANNEL_ID,
                    text="TP1 HIT - 50 pips",
                    reply_to_message_id=msg_id
                )
            except:
                pass
        
        if price >= trade["tp2"] and not trade["tp2_hit"]:
            trade["tp2_hit"] = True
            try:
                bot_instance.send_message(
                    chat_id=CHANNEL_ID,
                    text="TP2 HIT - 100 pips",
                    reply_to_message_id=msg_id
                )
            except:
                pass
            active_trade = None
            return
        
        if price <= trade["sl"] and not trade["sl_hit"]:
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
            return
    
    # SELL logic
    else:
        if price <= last_sent_price - 1:
            for p in range(int(last_sent_price) - 1, int(price) - 1, -1):
                try:
                    bot_instance.send_message(
                        chat_id=CHANNEL_ID,
                        text=f"XAUUSD Price {p}",
                        reply_to_message_id=msg_id
                    )
                    last_sent_price = p
                except Exception as e:
                    logger.error(f"Send error: {e}")
                time.sleep(0.3)
        
        if price <= trade["tp1"] and not trade["tp1_hit"]:
            trade["tp1_hit"] = True
            try:
                bot_instance.send_message(
                    chat_id=CHANNEL_ID,
                    text="TP1 HIT - 50 pips",
                    reply_to_message_id=msg_id
                )
            except:
                pass
        
        if price <= trade["tp2"] and not trade["tp2_hit"]:
            trade["tp2_hit"] = True
            try:
                bot_instance.send_message(
                    chat_id=CHANNEL_ID,
                    text="TP2 HIT - 100 pips",
                    reply_to_message_id=msg_id
                )
            except:
                pass
            active_trade = None
            return
        
        if price >= trade["sl"] and not trade["sl_hit"]:
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
            return
    
    last_known_price = price

# ================= MESSAGE HANDLER =================
def msg_handler(update: Update, context: CallbackContext):
    global active_trade, last_sent_price, trade_counter, last_known_price, bot_instance
    
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    
    text = update.message.text.strip().upper()
    
    if text == "/START":
        start_cmd(update, context)
        return
    
    if text == "PRICE":
        price_cmd(update, context)
        return
    
    # Manual update command
    if text == "UPDATE":
        if active_trade:
            check_price_updates()
            update.message.reply_text("Updated")
        else:
            update.message.reply_text("No active trade")
        return
    
    trade_type = None
    if text.startswith("BUY"):
        trade_type = "BUY"
    elif text.startswith("SELL"):
        trade_type = "SELL"
    
    if not trade_type:
        return
    
    # Get price
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
        update.message.reply_text("Failed to get price")
        return
    
    entry = round(price, 2)
    
    # Stop old trade
    if active_trade:
        try:
            bot_instance.send_message(
                chat_id=CHANNEL_ID,
                text=f"Trade #{active_trade['id']} stopped"
            )
        except:
            pass
        active_trade = None
        time.sleep(1)
    
    # Calculate
    if trade_type == "BUY":
        tp1 = round(entry + 5, 2)
        tp2 = round(entry + 10, 2)
        sl = round(entry - 10, 2)
    else:
        tp1 = round(entry - 5, 2)
        tp2 = round(entry - 10, 2)
        sl = round(entry + 10, 2)
    
    # Create trade
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
    
    # Send signal
    try:
        msg = bot_instance.send_message(
            chat_id=CHANNEL_ID,
            text=f"XAUUSD {trade_type} {entry}\n\nTP {tp1}\nTP {tp2}\n\nSL {sl}"
        )
        active_trade["msg_id"] = msg.message_id
        
        bot_instance.send_message(
            chat_id=CHANNEL_ID,
            text="Use proper lot size",
            reply_to_message_id=msg.message_id
        )
        
        update.message.reply_text(
            f"Signal #{trade_counter} Active\nEntry: {entry}\nTP1: {tp1}\nTP2: {tp2}\nSL: {sl}\n\nSend UPDATE to check price"
        )
        
    except Exception as e:
        logger.error(f"Error: {e}")
        active_trade = None

# ================= MAIN =================
def main():
    global bot_instance, updater_instance
    
    logger.info("Gold Bot Starting...")
    
    # Use Updater (sync version)
    updater = Updater(token=BOT_TOKEN, use_context=True)
    updater_instance = updater
    bot_instance = updater.bot
    
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start_cmd))
    dp.add_handler(CommandHandler("price", price_cmd))
    dp.add_handler(ChatJoinRequestHandler(join_req))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, msg_handler))
    
    logger.info("Bot running")
    
    # Start polling (blocking)
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
    
