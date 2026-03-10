#!/usr/bin/env python3
"""
GOLD BOT - REAL MARKET TRACKING
Only updates when price ACTUALLY changes
"""

import asyncio
import logging
import time
import re
from datetime import datetime
from typing import Optional, Dict
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

# ================= CONFIG =================
BOT_TOKEN = "8284715892:AAHOugCMkrfFK0Ehd6WVlYgW5CfMSU9K-5M"
CHANNEL_ID = -1003742118245
ADMIN_ID = 5072932186

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
last_known_price = None  # Track actual last price

# ================= PRICE FETCH =================
async def fetch_price() -> Optional[float]:
    """Fetch real live price"""
    try:
        url = "https://api.exchangerate-api.com/v4/latest/XAU"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=8) as response:
                if response.status == 200:
                    data = await response.json()
                    if "rates" in data and "USD" in data["rates"]:
                        price = float(data["rates"]["USD"])
                        if 1800 < price < 10000:
                            return round(price, 2)
    except:
        pass
    return None

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ <b>Gold Bot Online!</b>\n\n"
        "Commands:\n"
        "BUY 5078 - Create signal\n"
        "SELL 5080 - Create signal\n"
        "PRICE - Check current price",
        parse_mode="HTML"
    )

async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = await fetch_price()
    if price:
        await update.message.reply_text(f"📊 Live Price: {price}")
    else:
        await update.message.reply_text("❌ Failed to fetch")

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
    global active_trade, last_sent_price, tracking_running, trade_counter, last_known_price
    
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
    
    # Parse trade
    trade_type = None
    if text_upper.startswith("BUY"):
        trade_type = "BUY"
    elif text_upper.startswith("SELL"):
        trade_type = "SELL"
    
    if not trade_type:
        return
    
    # Extract price
    numbers = re.findall(r'\d{4}\.?\d{0,2}', text)
    manual_price = None
    if numbers:
        try:
            p = float(numbers[0])
            if 1800 < p < 10000:
                manual_price = p
        except:
            pass
    
    # Get price
    if manual_price:
        price = manual_price
    else:
        price = await fetch_price()
    
    if not price:
        await update.message.reply_text("❌ Failed. Use: BUY 5078")
        return
    
    entry = round(price, 2)
    
    # Stop old trade
    if active_trade:
        old_id = active_trade.get("trade_id")
        try:
            await context.bot.send_message(
                CHANNEL_ID,
                f"⏹️ Trade #{old_id} stopped...",
                parse_mode="HTML",
                reply_to_message_id=active_trade.get("message_id")
            )
        except:
            pass
        active_trade = None
        await asyncio.sleep(1)
    
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
    
    # Send signal
    try:
        msg = await context.bot.send_message(
            CHANNEL_ID,
            f"<b>XAUUSD {trade_type} {entry}</b>\n\n"
            f"<b>TP {tp1}</b>\n"
            f"<b>TP {tp2}</b>\n\n"
            f"<b>SL {sl}</b>",
            parse_mode="HTML"
        )
        
        active_trade["message_id"] = msg_id = msg.message_id
        
        await context.bot.send_message(
            CHANNEL_ID,
            "<b>⚠️ Use lot size according to your account equity.</b>",
            parse_mode="HTML",
            reply_to_message_id=msg_id
        )
        
        # Start tracker
        if not tracking_running:
            tracking_running = True
            asyncio.create_task(tracker(context))
        
        await update.message.reply_text(
            f"✅ Signal #{trade_counter} Active\n"
            f"Entry: {entry} | TP1: {tp1} | TP2: {tp2} | SL: {sl}\n"
            f"📊 Real market tracking ON"
        )
        
    except Exception as e:
        logger.error(f"Error: {e}")
        active_trade = None

# ================= REAL TRACKER =================
async def tracker(context: ContextTypes.DEFAULT_TYPE):
    global active_trade, last_sent_price, tracking_running, last_known_price
    
    logger.info("🚀 Real tracker started")
    
    while True:
        try:
            if not active_trade:
                await asyncio.sleep(2)
                continue
            
            trade = active_trade
            trade_id = trade["trade_id"]
            msg_id = trade["message_id"]
            
            # Fetch REAL price
            current_price = await fetch_price()
            
            # If fetch failed, use last known but DON'T send fake updates
            if not current_price:
                logger.warning("Price fetch failed, waiting...")
                await asyncio.sleep(3)
                continue
            
            # Check if trade replaced
            if not active_trade or active_trade.get("trade_id") != trade_id:
                break
            
            # ONLY send update if price ACTUALLY changed by $1 or more
            if trade["type"] == "BUY":
                # Price went UP by $1 or more
                if current_price >= last_sent_price + 1:
                    # Send update for new price level
                    new_level = int(current_price)  # Round to integer for clean levels
                    
                    # Send all skipped levels
                    temp = int(last_sent_price) + 1
                    while temp <= new_level:
                        try:
                            await context.bot.send_message(
                                CHANNEL_ID,
                                f"<b>XAUUSD trade active Price {temp}</b>",
                                parse_mode="HTML",
                                reply_to_message_id=msg_id
                            )
                            logger.info(f"Real update: {temp}")
                            last_sent_price = temp
                        except Exception as e:
                            logger.error(f"Send error: {e}")
                        
                        temp += 1
                        await asyncio.sleep(0.3)
                
                # Check TP/SL with REAL price
                if current_price >= trade["tp1"] and not trade["tp1_hit"]:
                    trade["tp1_hit"] = True
                    try:
                        await context.bot.send_message(
                            CHANNEL_ID,
                            "<b>XAUUSD\nTP1 hit successful 50+ pips done👑</b>",
                            parse_mode="HTML",
                            reply_to_message_id=msg_id
                        )
                    except:
                        pass
                
                if current_price >= trade["tp2"] and not trade["tp2_hit"]:
                    trade["tp2_hit"] = True
                    try:
                        await context.bot.send_message(
                            CHANNEL_ID,
                            "<b>XAUUSD\nTP2 hit successful 100+ pips done👑</b>",
                            parse_mode="HTML",
                            reply_to_message_id=msg_id
                        )
                    except:
                        pass
                    active_trade = None
                    break
                
                if current_price <= trade["sl"] and not trade["sl_hit"]:
                    trade["sl_hit"] = True
                    try:
                        await context.bot.send_message(
                            CHANNEL_ID,
                            "<b>SL HIT ❌ Wait for recovery</b>",
                            parse_mode="HTML",
                            reply_to_message_id=msg_id
                        )
                    except:
                        pass
                    active_trade = None
                    break
            
            else:  # SELL
                # Price went DOWN by $1 or more
                if current_price <= last_sent_price - 1:
                    new_level = int(current_price)
                    
                    temp = int(last_sent_price) - 1
                    while temp >= new_level:
                        try:
                            await context.bot.send_message(
                                CHANNEL_ID,
                                f"<b>XAUUSD trade active Price {temp}</b>",
                                parse_mode="HTML",
                                reply_to_message_id=msg_id
                            )
                            logger.info(f"Real update: {temp}")
                            last_sent_price = temp
                        except Exception as e:
                            logger.error(f"Send error: {e}")
                        
                        temp -= 1
                        await asyncio.sleep(0.3)
                
                # Check TP/SL
                if current_price <= trade["tp1"] and not trade["tp1_hit"]:
                    trade["tp1_hit"] = True
                    try:
                        await context.bot.send_message(
                            CHANNEL_ID,
                            "<b>XAUUSD\nTP1 hit successful 50+ pips done👑</b>",
                            parse_mode="HTML",
                            reply_to_message_id=msg_id
                        )
                    except:
                        pass
                
                if current_price <= trade["tp2"] and not trade["tp2_hit"]:
                    trade["tp2_hit"] = True
                    try:
                        await context.bot.send_message(
                            CHANNEL_ID,
                            "<b>XAUUSD\nTP2 hit successful 100+ pips done👑</b>",
                            parse_mode="HTML",
                            reply_to_message_id=msg_id
                        )
                    except:
                        pass
                    active_trade = None
                    break
                
                if current_price >= trade["sl"] and not trade["sl_hit"]:
                    trade["sl_hit"] = True
                    try:
                        await context.bot.send_message(
                            CHANNEL_ID,
                            "<b>SL HIT ❌ Wait for recovery</b>",
                            parse_mode="HTML",
                            reply_to_message_id=msg_id
                        )
                    except:
                        pass
                    active_trade = None
                    break
            
            # Update last known price
            last_known_price = current_price
            
            # Wait before next check
            await asyncio.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            logger.error(f"Tracker error: {e}")
            await asyncio.sleep(5)
    
    tracking_running = False
    logger.info("Tracker stopped")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatJoinRequestHandler(approve_join))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    
    logger.info("=" * 50)
    logger.info("🚀 GOLD BOT - REAL MARKET TRACKING")
    logger.info("=" * 50)
    
    app.run_polling(
        poll_interval=1,
        timeout=20,
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            logger.critical(f"CRASH: {e}")
            time.sleep(5)
                    
