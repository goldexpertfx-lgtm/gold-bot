#!/usr/bin/env python3
"""
GOLD BOT - MULTI-API FAILOVER VERSION
TradingView | MetaTrader | Investing.com | Kitco | 12Data | GoldAPI
Auto-switch when one fails
"""

import asyncio
import logging
import time
import re
import json
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import aiohttp
import requests
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

# ================= API KEYS (FREE TIER) =================
API_KEYS = {
    "twelvedata": "9bab8ab434c04d848ef27aee36dd3a4f",
    "goldapi": "goldapi-152a3asmlmlc131-io",
    "metalsapi": "free",
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
current_price = None
last_api_used = None
api_fail_count = {name: 0 for name in API_KEYS.keys()}
api_last_success = {name: 0 for name in API_KEYS.keys()}

# ================= MULTI-API PRICE FETCHER =================

class MultiAPIPriceFetcher:
    """Tries multiple APIs in priority order, auto-failover"""
    
    API_SOURCES = [
        ("goldapi", "fetch_goldapi"),
        ("twelvedata", "fetch_twelvedata"),
        ("tradingview", "fetch_tradingview"),
        ("investing", "fetch_investing"),
        ("kitco", "fetch_kitco"),
        ("metalsapi", "fetch_metalsapi"),
        ("forexfactory", "fetch_forexfactory"),
    ]
    
    def __init__(self):
        self.session = None
    
    async def get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
        return self.session
    
    async def fetch_goldapi(self) -> Optional[float]:
        try:
            url = "https://www.goldapi.io/api/XAU/USD"
            headers = {"x-access-token": API_KEYS["goldapi"]}
            
            session = await self.get_session()
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if "price" in data:
                        price = float(data["price"])
                        if 1800 < price < 10000:
                            return round(price, 2)
        except Exception as e:
            logger.warning(f"GoldAPI failed: {e}")
        return None
    
    async def fetch_twelvedata(self) -> Optional[float]:
        try:
            url = f"https://api.twelvedata.com/price?symbol=XAU/USD&apikey={API_KEYS['twelvedata']}"
            
            session = await self.get_session()
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if "price" in data and data["price"]:
                        price = float(data["price"])
                        if 1800 < price < 10000:
                            return round(price, 2)
        except Exception as e:
            logger.warning(f"TwelveData failed: {e}")
        return None
    
    async def fetch_tradingview(self) -> Optional[float]:
        try:
            urls = [
                "https://www.tradingview.com/symbols/XAUUSD/",
                "https://www.tradingview.com/chart/?symbol=OANDA%3AXAUUSD",
            ]
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            
            session = await self.get_session()
            for url in urls:
                try:
                    async with session.get(url, headers=headers, timeout=12) as response:
                        if response.status == 200:
                            text = await response.text()
                            
                            patterns = [
                                r'"lp":\s*(\d{4}\.\d{2})',
                                r'"last":\s*{\s*"value":\s*"(\d{4}\.\d{2})"',
                                r'"price":\s*(\d{4}\.\d{2})',
                                r'(\d{4}\.\d{2})\s*<span class="tv-symbol-price',
                            ]
                            
                            for pattern in patterns:
                                match = re.search(pattern, text)
                                if match:
                                    price = float(match.group(1))
                                    if 1800 < price < 10000:
                                        return round(price, 2)
                except:
                    continue
        except Exception as e:
            logger.warning(f"TradingView failed: {e}")
        return None
    
    async def fetch_investing(self) -> Optional[float]:
        try:
            urls = [
                "https://www.investing.com/currencies/xau-usd",
                "https://www.investing.com/commodities/gold",
            ]
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "X-Requested-With": "XMLHttpRequest",
            }
            
            session = await self.get_session()
            for url in urls:
                try:
                    async with session.get(url, headers=headers, timeout=12) as response:
                        if response.status == 200:
                            text = await response.text()
                            
                            patterns = [
                                r'data-test="instrument-price-last">(\d{4}\.\d{2})',
                                r'id="last_last"[^>]*>(\d{4}\.\d{2})',
                                r'last-price-value[^>]*>(\d{4}\.\d{2})',
                                r'"last":\s*"(\d{4}\.\d{2})"',
                            ]
                            
                            for pattern in patterns:
                                match = re.search(pattern, text)
                                if match:
                                    price = float(match.group(1))
                                    if 1800 < price < 10000:
                                        return round(price, 2)
                except:
                    continue
        except Exception as e:
            logger.warning(f"Investing.com failed: {e}")
        return None
    
    async def fetch_kitco(self) -> Optional[float]:
        try:
            url = "https://www.kitco.com/charts/gold.html"
            
            session = await self.get_session()
            async with session.get(url, timeout=12) as response:
                if response.status == 200:
                    text = await response.text()
                    
                    patterns = [
                        r'"bid":\s*(\d{4}\.\d{2})',
                        r'"ask":\s*(\d{4}\.\d{2})',
                        r'"price":\s*(\d{4}\.\d{2})',
                        r'(\d{4}\.\d{2})\s*USD',
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, text)
                        if match:
                            price = float(match.group(1))
                            if 1800 < price < 10000:
                                return round(price, 2)
        except Exception as e:
            logger.warning(f"Kitco failed: {e}")
        return None
    
    async def fetch_metalsapi(self) -> Optional[float]:
        try:
            url = f"https://metals-api.com/api/latest?access_key={API_KEYS['metalsapi']}&base=USD&symbols=XAU"
            
            session = await self.get_session()
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if "rates" in data and "XAU" in data["rates"]:
                        price = 1 / float(data["rates"]["XAU"])
                        if 1800 < price < 10000:
                            return round(price, 2)
        except Exception as e:
            logger.warning(f"MetalsAPI failed: {e}")
        return None
    
    async def fetch_forexfactory(self) -> Optional[float]:
        try:
            url = "https://www.forexfactory.com/calendar"
            
            session = await self.get_session()
            async with session.get(url, timeout=12) as response:
                if response.status == 200:
                    text = await response.text()
                    match = re.search(r'XAU/USD.*?(\d{4}\.\d{2})', text)
                    if match:
                        price = float(match.group(1))
                        if 1800 < price < 10000:
                            return round(price, 2)
        except Exception as e:
            logger.warning(f"ForexFactory failed: {e}")
        return None
    
    async def get_price(self) -> Tuple[Optional[float], Optional[str]]:
        global last_api_used, api_fail_count, api_last_success
        
        for api_name, method_name in self.API_SOURCES:
            try:
                if api_fail_count.get(api_name, 0) > 5:
                    if time.time() - api_last_success.get(api_name, 0) > 600:
                        api_fail_count[api_name] = 0
                    else:
                        continue
                
                fetch_method = getattr(self, method_name)
                price = await fetch_method()
                
                if price and 1800 < price < 10000:
                    last_api_used = api_name
                    api_last_success[api_name] = time.time()
                    api_fail_count[api_name] = 0
                    
                    logger.info(f"✅ Price from {api_name}: {price}")
                    return price, api_name
                
                api_fail_count[api_name] = api_fail_count.get(api_name, 0) + 1
                
            except Exception as e:
                logger.error(f"{api_name} error: {e}")
                api_fail_count[api_name] = api_fail_count.get(api_name, 0) + 1
                continue
            
            await asyncio.sleep(0.5)
        
        logger.error("❌ All APIs failed!")
        return None, None
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

price_fetcher = MultiAPIPriceFetcher()

# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ <b>🏆 GOLD BOT - MULTI-API MODE</b>\n\n"
        f"<b>Active APIs:</b> {len([k for k in API_KEYS.keys()])}\n"
        f"<b>Last Used:</b> {last_api_used or 'None'}\n\n"
        "<b>Commands:</b>\n"
        "<code>BUY</code> - Auto price\n"
        "<code>BUY 5085</code> - Manual price\n"
        "<code>SELL</code> - Auto price\n"
        "<code>API</code> - Check API status\n"
        "<code>STATUS</code> - Bot status\n\n"
        "<i>Auto-failover enabled</i>",
        parse_mode="HTML"
    )

async def check_apis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📊 <b>API Status:</b>\n\n"
    
    for name in API_KEYS.keys():
        fails = api_fail_count.get(name, 0)
        last = api_last_success.get(name, 0)
        status = "🟢" if fails < 3 else "🟡" if fails < 5 else "🔴"
        msg += f"{status} <b>{name}</b>: {fails} fails\n"
    
    msg += f"\n<i>Last used: {last_api_used or 'None'}</i>"
    
    await update.message.reply_text(msg, parse_mode="HTML")

async def check_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Fetching from multiple sources...")
    
    price, source = await price_fetcher.get_price()
    
    if price:
        await update.message.reply_text(
            f"📊 <b>XAU/USD: {price}</b>\n"
            f"<i>Source: {source}</i>\n"
            f"<i>Time: {datetime.now().strftime('%H:%M:%S')}</i>",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            "❌ <b>All APIs failed!</b>\n"
            "Try: <code>BUY 5085</code> (manual entry)",
            parse_mode="HTML"
        )

async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    trade_status = "🟢 ACTIVE" if active_trade else "⚪ NO TRADE"
    
    await update.message.reply_text(
        f"<b>🤖 BOT STATUS</b>\n\n"
        f"Status: 🟢 Online\n"
        f"Trade: {trade_status}\n"
        f"Price: {current_price or 'N/A'}\n"
        f"Last API: {last_api_used or 'N/A'}\n\n"
        f"<i>Multi-API Failover Active</i>",
        parse_mode="HTML"
    )

# ================= AUTO JOIN =================

async def approve_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.chat_join_request.from_user
        chat = update.chat_join_request.chat
        
        await context.bot.approve_chat_join_request(
            chat_id=chat.id,
            user_id=user.id,
        )
        
        try:
            await context.bot.send_message(
                user.id,
                f"✅ Welcome {user.first_name}!\n"
                f"You've been approved for {chat.title}.",
                parse_mode="HTML"
            )
        except:
            pass
        
        logger.info(f"Approved {user.id}")
        
    except Exception as e:
        logger.error(f"Join error: {e}")

# ================= MESSAGE HANDLER =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_trade, last_sent_price, tracking_running, trade_counter, current_price
    
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if user_id != ADMIN_ID:
        return
    
    text_upper = text.upper()
    
    if text_upper == "/START":
        await start(update, context)
        return
    
    if text_upper == "API":
        await check_apis(update, context)
        return
    
    if text_upper == "PRICE":
        await check_price(update, context)
        return
    
    if text_upper == "STATUS":
        await check_status(update, context)
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
        logger.info(f"Manual price: {price}")
    else:
        price, source = await price_fetcher.get_price()
        logger.info(f"API price: {price} from {source}")
    
    if not price:
        await update.message.reply_text(
            "❌ <b>All APIs failed!</b>\n"
            "Use manual price:\n"
            "<code>BUY 5085</code>\n"
            "<code>SELL 5080</code>",
            parse_mode="HTML"
        )
        return
    
    entry = round(price, 2)
    current_price = entry
    
    if active_trade:
        old_id = active_trade.get("trade_id")
        try:
            await context.bot.send_message(
                CHANNEL_ID,
                f"⏹️ <b>Trade #{old_id} stopped</b>\nNew {trade_type} signal...",
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
        
        if not tracking_running:
            tracking_running = True
            asyncio.create_task(tracker_multi_api(context))
        
        source_info = f" ({last_api_used})" if last_api_used else ""
        
        await update.message.reply_text(
            f"✅ <b>Signal #{trade_counter} ACTIVE</b>\n"
            f"Entry: {entry}{source_info}\n"
            f"TP1: {tp1} | TP2: {tp2} | SL: {sl}\n"
            f"<i>🔄 Multi-API tracking ON</i>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error: {e}")
        active_trade = None

# ================= MULTI-API TRACKER (COMPLETELY FIXED) =================

async def tracker_multi_api(context: ContextTypes.DEFAULT_TYPE):
    """24/7 tracker with multi-API failover"""
    global active_trade, last_sent_price, tracking_running, current_price
    
    logger.info("🚀 Multi-API Tracker started")
    
    while True:
        try:
            if not active_trade:
                await asyncio.sleep(5)
                continue
            
            price, source = await price_fetcher.get_price()
            
            if not price:
                logger.warning("No price available, skipping check")
                await asyncio.sleep(5)
                continue
            
            current_price = price
            
            entry = active_trade["entry"]
            trade_type = active_trade["type"]
            tp1 = active_trade["tp1"]
            tp2 = active_trade["tp2"]
            sl = active_trade["sl"]
            
            # Check TP1
            if not active_trade["tp1_hit"]:
                if (trade_type == "BUY" and price >= tp1) or (trade_type == "SELL" and price <= tp1):
                    active_trade["tp1_hit"] = True
                    try:
                        await context.bot.send_message(
                            CHANNEL_ID,
                            f"🎯 <b>TP1 HIT!</b>\nPrice: {price}\nMove SL to entry!",
                            parse_mode="HTML",
                            reply_to_message_id=active_trade["message_id"]
                        )
                    except Exception as e:
                        logger.error(f"TP1 notify error: {e}")
            
            # Check TP2 - FIXED BRACKET HERE
            if not active_trade["tp2_hit"]:
                if (trade_type == "BUY" and price >= tp2) or (trade
