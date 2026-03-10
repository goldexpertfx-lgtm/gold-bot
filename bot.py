#!/usr/bin/env python3
"""
GOLD BOT ULTIMATE - UNLIMITED API AUTO-SWITCH
Fixed Version - No Syntax Errors
"""

import asyncio
import logging
import time
import re
from datetime import datetime
from typing import Optional, Dict, List, Tuple
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

# UNLIMITED API LIST
API_PROVIDERS = [
    ("ExchangeRate", "https://api.exchangerate-api.com/v4/latest/XAU", 10),
    ("FloatRates", "https://www.floatrates.com/daily/xau.json", 5),
    ("FawazAhmed", "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/xau.json", 5),
    ("ExchangeRateHost", "https://api.exchangerate.host/convert?from=XAU&to=USD", 5),
]

API_KEYS = {}

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

# ================= API MANAGER =================
class APIManager:
    def __init__(self):
        self.apis = API_PROVIDERS.copy()
        self.current_index = 0
        self.failed_apis = {}
        self.success_count = {name: 0 for name, _, _ in self.apis}
        self.fail_count = {name: 0 for name, _, _ in self.apis}
        self.last_used = {name: 0 for name, _, _ in self.apis}
        self.cooldown_seconds = 60
        
    def get_working_api(self):
        now = time.time()
        attempts = 0
        max_attempts = len(self.apis) * 2
        
        while attempts < max_attempts:
            name, url, weight = self.apis[self.current_index]
            
            if name in self.failed_apis:
                if now - self.failed_apis[name] < self.cooldown_seconds:
                    self.current_index = (self.current_index + 1) % len(self.apis)
                    attempts += 1
                    continue
                else:
                    del self.failed_apis[name]
                    logger.info(f"API {name} cooldown over")
            
            time_since_last = now - self.last_used.get(name, 0)
            min_interval = 2
            
            if time_since_last < min_interval:
                self.current_index = (self.current_index + 1) % len(self.apis)
                attempts += 1
                continue
            
            self.last_used[name] = now
            return name, url
        
        logger.warning("All APIs in cooldown, forcing first")
        name, url, _ = self.apis[0]
        self.last_used[name] = now
        return name, url
    
    def mark_failed(self, name: str):
        self.failed_apis[name] = time.time()
        self.fail_count[name] = self.fail_count.get(name, 0) + 1
        logger.warning(f"API {name} failed")
        self.current_index = (self.current_index + 1) % len(self.apis)
    
    def mark_success(self, name: str):
        self.success_count[name] = self.success_count.get(name, 0) + 1
        logger.info(f"API {name} success")
    
    def get_stats(self) -> str:
        stats = "API Stats:\n"
        for name, _, _ in self.apis:
            succ = self.success_count.get(name, 0)
            fail = self.fail_count.get(name, 0)
            status = "OK" if name not in self.failed_apis else "COOL"
            stats += f"{name}: {succ}OK {fail}FAIL ({status})\n"
        return stats

api_manager = APIManager()

# ================= PRICE FETCH =================
async def fetch_price() -> Optional[float]:
    max_retries = len(API_PROVIDERS)
    attempted = set()
    
    for _ in range(max_retries):
        api_name, api_url = api_manager.get_working_api()
        
        if api_name in attempted:
            continue
        attempted.add(api_name)
        
        try:
            price = await try_fetch_from_api(api_name, api_url)
            if price and 1800 < price < 10000:
                api_manager.mark_success(api_name)
                return round(price, 2)
        except Exception as e:
            logger.error(f"API {api_name} error: {e}")
            api_manager.mark_failed(api_name)
            continue
    
    logger.critical("ALL APIs FAILED")
    return last_known_price

async def try_fetch_from_api(name: str, url: str) -> Optional[float]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0"
    }
    
    if name in API_KEYS and API_KEYS[name]:
        if "?" in url:
            url = url.replace("YOUR_KEY", API_KEYS[name])
        headers["x-access-token"] = API_KEYS.get(name, "")
    
    timeout = aiohttp.ClientTimeout(total=10)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}")
            
            data = await response.json()
            return parse_price_from_response(name, data)

def parse_price_from_response(api_name: str, data: dict) -> Optional[float]:
    try:
        if api_name == "ExchangeRate":
            return float(data["rates"]["USD"])
        elif api_name == "FloatRates":
            return float(data["usd"]["rate"])
        elif api_name == "FawazAhmed":
            return float(data["usd"])
        elif api_name == "ExchangeRateHost":
            return float(data["result"])
    except Exception as e:
        logger.error(f"Parse error {api_name}: {e}")
    
    return None

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Gold Bot ULTIMATE Online!\n\n"
        "Unlimited APIs Active\n"
        "Auto-failover Enabled\n\n"
        "Commands:\n"
        "BUY 5078 - Create signal\n"
        "SELL 5080 - Create signal\n"
        "PRICE - Check price\n"
        "STATS - API statistics",
        parse_mode="HTML"
    )

async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = await fetch_price()
    if price:
        current_api = api_manager.apis[api_manager.current_index][0]
        await update.message.reply_text(
            f"Live Price: {price}\nSource: {current_api}",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("All APIs failed")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = api_manager.get_stats()
    await update.message.reply_text(stats)

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
    
    if text_upper == "STATS":
        await stats_cmd(update, context)
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
        price = await fetch_price()
    
    if not price:
        await update.message.reply_text("All APIs failed")
        return
    
    entry = round(price, 2)
    
    if active_trade:
        old_id = active_trade.get("trade_id")
        try:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"Trade #{old_id} stopped",
                parse_mode="HTML",
                reply_to_message_id=active_trade.get("message_id")
            )
        except:
            pass
        active_trade = None
        await asyncio.sleep(1)
    
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
            text=f"<b>XAUUSD {trade_type} {entry}</b>\n\n<b>TP {tp1}</b>\n<b>TP {tp2}</b>\n\n<b>SL {sl}</b>",
            parse_mode="HTML"
        )
        
        active_trade["message_id"] = msg_id = msg.message_id
        
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text="<b>Use lot size according to account equity</b>",
            parse_mode="HTML",
            reply_to_message_id=msg_id
        )
        
        if not tracking_running:
            tracking_running = True
            asyncio.create_task(tracker(context))
        
        await update.message.reply_text(
            f"Signal #{trade_counter} Active\nEntry: {entry} | TP1: {tp1} | TP2: {tp2} | SL: {sl}"
        )
        
    except Exception as e:
        logger.error(f"Error: {e}")
        active_trade = None

# ================= TRACKER =================
async def tracker(context: ContextTypes.DEFAULT_TYPE):
    global active_trade, last_sent_price, tracking_running, last_known_price
    
    logger.info("Tracker Started")
    
    while True:
        try:
            if not active_trade:
                await asyncio.sleep(2)
                continue
            
            trade = active_trade
            trade_id = trade["trade_id"]
            msg_id = trade["message_id"]
            
            current_price = await fetch_price()
            
            if not current_price:
                logger.warning("All APIs failed, retrying")
                await asyncio.sleep(5)
                continue
            
            if not active_trade or active_trade.get("trade_id") != trade_id:
                break
            
            if trade["type"] == "BUY":
                if current_price >= last_sent_price + 1:
                    new_level = int(current_price)
                    temp = int(last_sent_price) + 1
                    
                    while temp <= new_level:
                        try:
                            await context.bot.send_message(
                                chat_id=CHANNEL_ID,
                                text=f"<b>XAUUSD active Price {temp}</b>",
                                parse_mode="HTML",
                                reply_to_message_id=msg_id
                            )
                            logger.info(f"Update: {temp}")
                            last_sent_price = temp
                        except Exception as e:
                            logger.error(f"Send error: {e}")
                        
                        temp += 1
                        await asyncio.sleep(0.3)
                
                if current_price >= trade["tp1"] and not trade["tp1_hit"]:
                    trade["tp1_hit"] = True
                    try:
                        await context.bot.send_message(
                            chat_id=CHANNEL_ID,
                            text="<b>XAUUSD TP1 hit 50+ pips</b>",
                            parse_mode="HTML",
                            reply_to_message_id=msg_id
                        )
                    except:
                        pass
                
                if current_price >= trade["tp2"] and not trade["tp2_hit"]:
                    trade["tp2_hit"] = True
                    try:
                        await context.bot.send_message(
                            chat_id=CHANNEL_ID,
                            text="<b>XAUUSD TP2 hit 100+ pips</b>",
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
                            chat_id=CHANNEL_ID,
                            text="<b>SL HIT</b>",
                            parse_mode="HTML",
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
                            await context.bot.send_message(
                                chat_id=CHANNEL_ID,
                                text=f"<b>XAUUSD active Price {temp}</b>",
                                parse_mode="HTML",
                                reply_to_message_id=msg_id
                            )
                            logger.info(f"Update: {temp}")
                            last_sent_price = temp
                        except Exception as e:
                            logger.error(f"Send error: {e}")
                        
                        temp -= 1
                        await asyncio.sleep(0.3)
                
                if current_price <= trade["tp1"] and not trade["tp1_hit"]:
                    trade["tp1_hit"] = True
                    try:
                        await context.bot.send_message(
                            chat_id=CHANNEL_ID,
                            text="<b>XAUUSD TP1 hit 50+ pips</b>",
                            parse_mode="HTML",
                            reply_to_message_id=msg_id
                        )
                    except:
                        pass
                
                if current_price <= trade["tp2"] and not trade["tp2_hit"]:
                    trade["tp2_hit"] = True
                    try:
                        await context.bot.send_message(
                            chat_id=CHANNEL_ID,
                            text="<b>XAUUSD TP2 hit 100+ pips</b>",
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
                            chat_id=CHANNEL_ID,
                            text="<b>SL HIT</b>",
                            parse_mode="HTML",
                            reply_to_message_id=msg_id
                        )
                    except:
                        pass
                    active_trade = None
                    break
            
            last_known_price = current_price
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Tracker error: {e}")
            await asyncio.sleep(5)
    
    tracking_running = False
    logger.info("Tracker stopped")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(ChatJoinRequestHandler(approve_join))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    
    logger.info("=" * 50)
    logger.info("GOLD BOT ULTIMATE - UNLIMITED APIs")
    logger.info(f"Total APIs: {len(API_PROVIDERS)}")
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
            
