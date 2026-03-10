#!/usr/bin/env python3
"""
GOLD BOT ULTIMATE - UNLIMITED API AUTO-SWITCH
Never stops, never sleeps, unlimited APIs
"""

import asyncio
import logging
import time
import re
import random
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

# ================= STEP 1: CONFIG - YAHAN SAB DAALO =================

# 🤖 BOT TOKEN
BOT_TOKEN = "8284715892:AAHOugCMkrfFK0Ehd6WVlYgW5CfMSU9K-5M"

# 📢 CHANNEL ID
CHANNEL_ID = -1003742118245

# 👑 ADMIN ID
ADMIN_ID = 5072932186

# 🔑 UNLIMITED API LIST - Jitni marzi daalo, auto-switch hoga
# Format: (name, url, weight)
API_PROVIDERS = [
    # Primary APIs (High priority)
    ("ExchangeRate", "https://api.exchangerate-api.com/v4/latest/XAU", 10),
    ("GoldAPI", "https://www.goldapi.io/api/XAU/USD", 10),
    
    # Backup APIs (Medium priority)
    ("MetalsAPI", "https://metals-api.com/api/latest?access_key=YOUR_KEY&base=XAU&symbols=USD", 5),
    ("CurrencyAPI", "https://api.currencyapi.com/v3/latest?apikey=YOUR_KEY&base_currency=XAU&currencies=USD", 5),
    
    # Free Backups (Lower priority but unlimited)
    ("FloatRates", "https://www.floatrates.com/daily/xau.json", 3),
    ("ExchangeRateHost", "https://api.exchangerate.host/convert?from=XAU&to=USD", 3),
    
    # More free APIs (Add your own)
    ("FawazAhmed", "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/xau.json", 3),
    ("InforEuro", "https://ec.europa.eu/budg/inforeuro/api/public/currencies/xau", 2),
    
    # Premium backups (Add your keys)
    ("Fixer", "http://data.fixer.io/api/latest?access_key=YOUR_KEY&symbols=XAU,USD", 2),
    ("Currencylayer", "http://api.currencylayer.com/live?access_key=YOUR_KEY", 2),
]

# API Keys (Agar premium APIs use karte ho toh yahan daalo)
API_KEYS = {
    "GoldAPI": "YOUR_GOLDAPI_KEY",
    "MetalsAPI": "YOUR_METALS_KEY",
    "CurrencyAPI": "YOUR_CURRENCY_KEY",
    "Fixer": "YOUR_FIXER_KEY",
    "Currencylayer": "YOUR_LAYER_KEY",
}

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

# ================= API MANAGER - THE MAGIC =================
class APIManager:
    """Smart API manager with auto-failover and unlimited switching"""
    
    def __init__(self):
        self.apis = API_PROVIDERS.copy()
        self.current_index = 0
        self.failed_apis = {}  # Track failed APIs with cooldown
        self.success_count = {name: 0 for name, _, _ in self.apis}
        self.fail_count = {name: 0 for name, _, _ in self.apis}
        self.last_used = {name: 0 for name, _, _ in self.apis}
        self.cooldown_seconds = 60  # 1 min cooldown for failed APIs
        
    def get_working_api(self) -> Tuple[str, str]:
        """Get next working API with smart rotation"""
        now = time.time()
        attempts = 0
        max_attempts = len(self.apis) * 2
        
        while attempts < max_attempts:
            name, url, weight = self.apis[self.current_index]
            
            # Check if API is in cooldown
            if name in self.failed_apis:
                if now - self.failed_apis[name] < self.cooldown_seconds:
                    # Skip this API, move to next
                    self.current_index = (self.current_index + 1) % len(self.apis)
                    attempts += 1
                    continue
                else:
                    # Cooldown over, remove from failed
                    del self.failed_apis[name]
                    logger.info(f"🔄 API {name} cooldown over, retrying...")
            
            # Check rate limiting (don't use same API too frequently)
            time_since_last = now - self.last_used.get(name, 0)
            min_interval = 2  # Minimum 2 seconds between same API calls
            
            if time_since_last < min_interval:
                self.current_index = (self.current_index + 1) % len(self.apis)
                attempts += 1
                continue
            
            # This API is good to use
            self.last_used[name] = now
            return name, url
        
        # All APIs exhausted, force use first available
        logger.warning("⚠️ All APIs in cooldown, forcing first available")
        name, url, _ = self.apis[0]
        self.last_used[name] = now
        return name, url
    
    def mark_failed(self, name: str):
        """Mark an API as failed"""
        self.failed_apis[name] = time.time()
        self.fail_count[name] = self.fail_count.get(name, 0) + 1
        logger.warning(f"❌ API {name} failed (Total fails: {self.fail_count[name]})")
        
        # Move to next API immediately
        self.current_index = (self.current_index + 1) % len(self.apis)
    
    def mark_success(self, name: str):
        """Mark an API as successful"""
        self.success_count[name] = self.success_count.get(name, 0) + 1
        logger.info(f"✅ API {name} success (Total: {self.success_count[name]})")
    
    def get_stats(self) -> str:
        """Get API usage statistics"""
        stats = "📊 API Stats:\n"
        for name, _, _ in self.apis:
            succ = self.success_count.get(name, 0)
            fail = self.fail_count.get(name, 0)
            status = "🟢" if name not in self.failed_apis else "🔴"
            stats += f"{status} {name}: ✅{succ} ❌{fail}\n"
        return stats

# Global API manager
api_manager = APIManager()

# ================= PRICE FETCH - UNLIMITED POWER =================
async def fetch_price() -> Optional[float]:
    """Fetch price with unlimited API auto-switching"""
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
    
    # All APIs failed - emergency fallback
    logger.critical("🚨 ALL APIs FAILED! Using last known price...")
    return last_known_price

async def try_fetch_from_api(name: str, url: str) -> Optional[float]:
    """Try to fetch from specific API"""
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    # Add API keys if needed
    if name in API_KEYS and API_KEYS[name] != f"YOUR_{name.upper()}_KEY":
        if "?" in url:
            url = url.replace("YOUR_KEY", API_KEYS[name])
        headers["x-access-token"] = API_KEYS.get(name, "")
        headers["Authorization"] = f"Bearer {API_KEYS.get(name, '')}"
    
    timeout = aiohttp.ClientTimeout(total=10)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}")
            
            data = await response.json()
            return parse_price_from_response(name, data)

def parse_price_from_response(api_name: str, data: dict) -> Optional[float]:
    """Parse price from different API formats"""
    
    try:
        if api_name == "ExchangeRate":
            return float(data["rates"]["USD"])
        
        elif api_name == "GoldAPI":
            return float(data["price"])
        
        elif api_name == "MetalsAPI":
            return float(data["rates"]["USD"])
        
        elif api_name == "CurrencyAPI":
            return float(data["data"]["USD"]["value"])
        
        elif api_name == "FloatRates":
            return float(data["usd"]["rate"])
        
        elif api_name == "ExchangeRateHost":
            return float(data["result"])
        
        elif api_name == "FawazAhmed":
            return float(data["usd"])
        
        elif api_name == "InforEuro":
            # Parse EUR rate and convert (approximate)
            eur_rate = float(data[0]["amount"])
            return eur_rate * 1.08  # EUR to USD approximate
        
        elif api_name in ["Fixer", "Currencylayer"]:
            if "rates" in data and "XAU" in data["rates"]:
                return float(data["rates"]["XAU"])
            elif "quotes" in data and "USDXAU" in data["quotes"]:
                return 1 / float(data["quotes"]["USDXAU"])
        
        # Generic parsers
        if "price" in data:
            return float(data["price"])
        elif "rate" in data:
            return float(data["rate"])
        elif "rates" in data and "USD" in data["rates"]:
            return float(data["rates"]["USD"])
            
    except Exception as e:
        logger.error(f"Parse error for {api_name}: {e}")
    
    return None

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ <b>Gold Bot ULTIMATE Online!</b>\n\n"
        "🔄 Unlimited APIs Active\n"
        "⚡ Auto-failover Enabled\n\n"
        "Commands:\n"
        "BUY 5078 - Create signal\n"
        "SELL 5080 - Create signal\n"
        "PRICE - Check current price\n"
        "STATS - API statistics",
        parse_mode="HTML"
    )

async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = await fetch_price()
    if price:
        current_api = api_manager.apis[api_manager.current_index][0]
        await update.message.reply_text(
            f"📊 Live Price: <b>{price}</b>\n"
            f"🌐 Source: {current_api}",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("❌ All APIs failed! Retrying...")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show API statistics"""
    stats = api_manager.get_stats()
    await update.message.reply_text(stats, parse_mode="HTML")

async def apis_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available APIs"""
    api_list = "🌐 Available APIs:\n\n"
    for i, (name, url, weight) in enumerate(api_manager.apis, 1):
        status = "🟢 Active" if name not in api_manager.failed_apis else "🔴 Cooldown"
        api_list += f"{i}. {name} ({status})\n"
    
    api_list += f"\n📊 Total: {len(api_manager.apis)} APIs"
    await update.message.reply_text(api_list)

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
    
    if text_upper == "APIS":
        await apis_cmd(update, context)
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
    
    # Get price with unlimited API power
    if manual_price:
        price = manual_price
    else:
        price = await fetch_price()
    
    if not price:
        await update.message.reply_text("❌ All APIs failed! Check STATS")
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
            f"🌐 Unlimited APIs Active"
        )
        
    except Exception as e:
        logger.error(f"Error: {e}")
        active_trade = None

# ================= REAL TRACKER =================
async def tracker(context: ContextTypes.DEFAULT_TYPE):
    global active_trade, last_sent_price, tracking_running, last_known_price
    
    logger.info("🚀 Unlimited Tracker Started")
    
    while True:
        try:
            if not active_trade:
                await asyncio.sleep(2)
                continue
            
            trade = active_trade
            trade_id = trade["trade_id"]
            msg_id = trade["message_id"]
            
            # Fetch with unlimited API power
            current_price = await fetch_price()
            
            if not current_price:
                logger.warning("All APIs failed, retrying in 5s...")
                await asyncio.sleep(5)
                continue
            
            # Check if trade replaced
            if not active_trade or active_trade.get("trade_id") != trade_id:
                break
            
            # Process updates
            if trade["type"] == "BUY":
                if current_price >= last_sent_price + 1:
                    new_level = int(current_price)
                    temp = int(last_sent_price) + 1
                    
                    while temp <= new_level:
                        try:
                            await context.bot.send_message(
                                CHANNEL_ID,
                                f"<b>XAUUSD trade active Price {temp}</b>",
                                parse_mode="HTML",
                                reply_to_message_id=msg_id
                            )
                            logger.info(f"Update: {temp}")
                            last_sent_price = temp
                        except Exception as e:
                            logger.error(f"Send error: {e}")
                        
                        temp += 1
                        await asyncio.sleep(0.3)
                
                # Check TP/SL
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
                            logger.info(f"Update: {temp}")
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
                            repl
