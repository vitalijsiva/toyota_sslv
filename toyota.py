"""
Toyota Filtered Listings Telegram Bot – STABLE + SMART FILTER VERSION

Rules:
- ALL Hilux
- ALL Land Cruiser
- ALL Toyota defects (only Toyota, petrol only)
- ONLY petrol for other Toyota
- EXCLUDE hybrids
- EXCLUDE diesels (except Hilux/LC)
"""

import os
import sys
import logging
import asyncio
import time
import signal
import random
import re
import json
from pathlib import Path
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)
import telegram.error
from dotenv import load_dotenv


# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Load env
load_dotenv()

# ===========================================
# CONFIG
# ===========================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHECK_INTERVAL = 20  # base interval between checks
REQUEST_TIMEOUT = 25
LOCK_FILE = Path("toyota_bot.lock")

# File to persist already-seen listings between restarts
SEEN_FILE = Path("toyota_seen.json")

AUTO_NOTIFY = True

# Берём все Toyota из общего списка + дефекты
SS_LV_URLS = [
    "https://www.ss.lv/lv/transport/cars/toyota/sell/",
    "https://www.ss.lv/lv/transport/other/transport-with-defects-or-after-crash/sell/"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0"
]

subscribed_users: set[int] = set()
seen_listing_ids: set[str] = set()

# In-memory cache для типа топлива: key = listing_id, value = fuel_type
fuel_cache: Dict[str, str] = {}

start_time = time.time()


# ===========================================
# LOCK & SIGNAL HANDLING
# ===========================================
def create_lock_file():
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
        with open(LOCK_FILE, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass


def remove_lock_file():
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception:
        pass


def signal_handler(signum, frame):
    remove_lock_file()
    save_seen_ids()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ===========================================
# LOGGING
# ===========================================
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ===========================================
# STATE PERSISTENCE
# ===========================================
def load_seen_ids():
    """Load seen listing IDs from file to avoid ресендов после рестарта."""
    global seen_listing_ids
    if not SEEN_FILE.exists():
        return
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            seen_listing_ids = set(data)
        logger.info(f"Loaded {len(seen_listing_ids)} seen IDs from file")
    except Exception as e:
        logger.error(f"Failed to load seen IDs: {e}")


def save_seen_ids():
    """Persist seen listing IDs to file."""
    try:
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(seen_listing_ids), f, ensure_ascii=False)
        logger.debug(f"Saved {len(seen_listing_ids)} seen IDs")
    except Exception as e:
        logger.error(f"Failed to save seen IDs: {e}")


# ===========================================
# SCRAPER HELPERS
# ===========================================
def extract_fuel_type(soup: BeautifulSoup) -> str:
    """
    Пытаемся вытащить тип топлива из разных возможных разметок ss.lv:
    - классическая таблица (td.ads_opt_name / td.ads_opt)
    - мобильная разметка (div.row-label / div.row-value)
    """
    # 1) Стандартная таблица ss.lv
    for td in soup.select("td.ads_opt_name"):
        name = td.get_text(strip=True).lower()
        if "motors" in name or "dzinējs" in name:
            value_td = td.find_next_sibling("td", class_="ads_opt")
            if value_td:
                return value_td.get_text(strip=True)

    # 2) Мобильная/альтернативная разметка
    row_labels = soup.select("div.row-label")
    row_values = soup.select("div.row-value")

    for label, value in zip(row_labels, row_values):
        lbl = label.get_text(strip=True).lower()
        if "motors" in lbl or "dzinējs" in lbl:
            return value.get_text(strip=True)

    return ""


def get_fuel_type_from_detail(listing_id: str, link: str, session: requests.Session) -> str:
    """
    Fetch fuel type from detail page.
    Использует in-memory cache, чтобы не дергать одну и ту же страницу
    каждые 20 секунд.
    """
    if listing_id in fuel_cache:
        return fuel_cache[listing_id]

    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        resp = session.get(link, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        # Небольшая задержка, чтобы не спамить ss.lv
        time.sleep(random.uniform(0.3, 0.7))

        soup = BeautifulSoup(resp.content, "html.parser")

        fuel_text = extract_fuel_type(soup)
        fuel_text = fuel_text.strip()
        fuel_cache[listing_id] = fuel_text
        return fuel_text
    except Exception as e:
        logger.error(f"Error fetching detail page {link}: {e}")
        # Пауза на ошибке, чтобы не ловить бан
        time.sleep(1.0)
        return ""


def scrape_listings() -> Optional[List[Dict[str, str]]]:
    """
    Скрапит все страницы из SS_LV_URLS.
    На этом уровне НЕ фильтруем объявления — только собираем данные.
    """
    all_items: List[Dict[str, str]] = []
    session = requests.Session()

    for url in SS_LV_URLS:
        try:
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            resp = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()

            # Плавное поведение, чтобы не быть похожим на бота
            time.sleep(random.uniform(0.8, 1.5))

            soup = BeautifulSoup(resp.content, "html.parser")
            rows = soup.select('tr[id^="tr_"]')

            for row in rows:
                title_el = row.select_one("a.am")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                link = title_el.get("href")
                if link and not link.startswith("http"):
                    link = "https://www.ss.lv" + link

                listing_id = row.get("id", "").replace("tr_", "").strip()
                if not listing_id:
                    listing_id = link  # safety fallback

                details = " ".join(
                    td.get_text(strip=True) for td in row.select("td.msga2")
                )

                price_el = row.select("td.msga2-o.pp6")
                price = price_el[-1].get_text(strip=True) if price_el else "N/A"

                is_defect = "transport-with-defects" in url

                fuel_type = get_fuel_type_from_detail(listing_id, link, session)

                all_items.append(
                    {
                        "id": listing_id,
                        "title": title,
                        "price": price,
                        "link": link,
                        "description": details,
                        "is_defect": is_defect,
                        "fuel_type": fuel_type,
                    }
                )

        except Exception as e:
            logger.error(f"SCRAPE ERROR for {url}: {e}")
            time.sleep(2.0)

    return all_items


# ===========================================
# FILTERING LOGIC (FINAL)
# ===========================================
def filter_benzina_toyotas(listings: List[Dict[str, str]]):
    """
    Final Rules:
    - Hilux → ALL
    - Land Cruiser → ALL
    - Toyota defects → petrol only
    - Other Toyota → petrol only
    - Exclude hybrids everywhere
    - Exclude diesels (except Hilux / LC)
    """

    filtered: List[Dict[str, str]] = []

    petrol_keywords = ["benz", "benzin", "benzīn", "benzīns", "petrol", "gas"]
    diesel_keywords = ["diesel", "dīze", "dize", "dīzel", "d-4d", "d4d", "tdi", "dci"]
    hybrid_keywords = ["hybrid", "hibr", "phev", "plug-in"]

    def detect_fallback(text: str):
        text = text.lower()
        if "benz" in text:
            return "petrol"
        if "diesel" in text or "dīze" in text:
            return "diesel"
        if "hybrid" in text or "hibr" in text:
            return "hybrid"
        return ""

    for item in listings:
        link = item["link"].lower()
        text = (item["title"] + " " + item["description"]).lower()
        fuel_type = (item.get("fuel_type") or "").lower()

        # Fallback если fuel_type пустой
        if not fuel_type:
            fallback = detect_fallback(text)
            if fallback:
                fuel_type = fallback

        # 1) Hilux/LC → always include (any fuel)
        if "/hilux/" in link or "/land-cruiser/" in link:
            filtered.append(item)
            continue

        # 2) Exclude hybrids everywhere
        if any(h in fuel_type for h in hybrid_keywords):
            continue

        # 3) Defects → only Petrol Toyota
        if item["is_defect"]:
            if "toyota" not in text:
                continue

            is_petrol = any(p in fuel_type for p in petrol_keywords)
            is_diesel = any(d in fuel_type for d in diesel_keywords)

            if is_petrol and not is_diesel:
                filtered.append(item)

            continue

        # 4) Regular Toyota → only petrol (diesel only allowed for Hilux/LC, уже обработаны)
        is_petrol = any(p in fuel_type for p in petrol_keywords)
        is_diesel = any(d in fuel_type for d in diesel_keywords)

        if not is_petrol:
            continue

        if is_diesel:
            continue

        filtered.append(item)

    return filtered


# ===========================================
# MESSAGE FORMATTER
# ===========================================
async def format_listing_message(item: Dict[str, str]):
    text = (item["title"] + " " + item["description"]).lower()
    fuel_type_raw = (item.get("fuel_type") or "").strip()

    # Detect year
    year = "N/A"
    m = re.search(r"\b(19|20)\d{2}\b", item["title"])
    if m:
        year = m.group(0)

    # Detect fuel (сначала по fuel_type, потом — backup по тексту)
    fuel = "N/A"
    fuel_l = fuel_type_raw.lower()
    if any(x in fuel_l for x in ["benz", "petrol", "gas"]):
        fuel = "Petrol"
    elif any(x in fuel_l for x in ["dīze", "diesel", "d4d", "d-4d", "tdi", "dci"]):
        fuel = "Diesel"
    elif any(x in fuel_l for x in ["hybrid", "hibr", "phev"]):
        fuel = "Hybrid"
    else:
        if "benz" in text:
            fuel = "Petrol"
        elif "diesel" in text or "dīze" in text:
            fuel = "Diesel"
        elif "hybrid" in text or "hibr" in text:
            fuel = "Hybrid"

    if item["is_defect"]:
        msg = "⚠️ <b>Defekts / Crash Toyota</b>\n"
    else:
        msg = "🚗 <b>Toyota</b>\n"

    msg += f"<b>{item['title']}</b>\n"
    msg += f"📅 Gads: <b>{year}</b>\n"
    msg += f"⛽ Dzinējs: <b>{fuel}</b>\n"
    msg += f"💰 Cena: <b>{item['price']}</b>"

    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔗 Atvērt sludinājumu", url=item["link"])],
            [
                InlineKeyboardButton(
                    "🔍 Visas Toyota",
                    url="https://www.ss.lv/lv/transport/cars/toyota/sell/",
                )
            ],
        ]
    )

    return msg, kb


# ===========================================
# TELEGRAM HELPERS
# ===========================================
async def safe_send_message(app: Application, chat_id: int, text: str, reply_markup=None):
    """
    Отправка сообщения с обработкой FloodWait, Forbidden и пр.
    """
    try:
        await app.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
            reply_markup=reply_markup,
            disable_web_page_preview=False,
        )
    except telegram.error.RetryAfter as e:
        wait_for = int(e.retry_after) + 1
        logger.warning(f"FloodWait for {wait_for}s when sending to {chat_id}")
        await asyncio.sleep(wait_for)
        try:
            await app.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="HTML",
                reply_markup=reply_markup,
                disable_web_page_preview=False,
            )
        except Exception as e2:
            logger.error(f"Failed to resend message to {chat_id}: {e2}")
    except telegram.error.Forbidden:
        logger.info(f"User {chat_id} blocked the bot. Removing from subscribers.")
        subscribed_users.discard(chat_id)
    except Exception as e:
        logger.error(f"Error sending message to {chat_id}: {e}")


# ===========================================
# BOT COMMANDS
# ===========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subscribed_users.add(update.effective_user.id)
    await update.message.reply_text("✅ Abonēts Toyota paziņojumiem!")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subscribed_users.discard(update.effective_user.id)
    await update.message.reply_text("🔕 Abonēšana aptурēta.")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👥 Subscribers: {len(subscribed_users)}\n"
        f"🔎 Seen listings: {len(seen_listing_ids)}"
    )


async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if AUTO_NOTIFY:
        subscribed_users.add(update.effective_user.id)
        await update.message.reply_text("👋 Pievienots paziņojumiem!")


# ===========================================
# MONITOR LOOP
# ===========================================
def scrape_and_process():
    raw = scrape_listings()
    filtered = filter_benzina_toyotas(raw)

    new = []
    for item in filtered:
        if item["id"] not in seen_listing_ids:
            seen_listing_ids.add(item["id"])
            new.append(item)

    return new


async def monitor(app: Application):
    # Initial load
    try:
        logger.info("🔍 Initial check - loading all listings...")
        all_listings = await asyncio.to_thread(scrape_listings)
        all_filtered = await asyncio.to_thread(filter_benzina_toyotas, all_listings)

        for item in all_filtered:
            seen_listing_ids.add(item["id"])

        save_seen_ids()

        if subscribed_users and all_filtered:
            MAX_INITIAL_SEND = 50
            to_send = all_filtered[:MAX_INITIAL_SEND]

            logger.info(
                f"📤 Sending {len(to_send)} existing listings to {len(subscribed_users)} subscribers..."
            )

            for item in to_send:
                msg, kb = await format_listing_message(item)
                msg = f"📋 <b>Existing listing</b>\n\n{msg}"

                for uid in list(subscribed_users):
                    await safe_send_message(app, uid, msg, reply_markup=kb)
                    await asyncio.sleep(0.4)

                await asyncio.sleep(0.8)

            logger.info("✅ Initial listings sent.")
        else:
            logger.info(
                f"✅ Cache populated with {len(all_filtered)} listings (no initial send)."
            )

    except Exception as e:
        logger.error(f"Error in initial send: {e}")

    # Основной мониторинг
    while True:
        try:
            new_items = await asyncio.to_thread(scrape_and_process)

            if new_items:
                logger.info(f"NEW LISTINGS: {len(new_items)}")
                save_seen_ids()

                for item in new_items:
                    msg, kb = await format_listing_message(item)

                    for uid in list(subscribed_users):
                        await safe_send_message(app, uid, msg, reply_markup=kb)
                        await asyncio.sleep(0.3)

        except Exception as e:
            logger.error(f"Monitor error: {e}")
            await asyncio.sleep(5)

        await asyncio.sleep(CHECK_INTERVAL + random.random() * 5)


# ===========================================
# MAIN
# ===========================================
def main():
    if not TELEGRAM_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN is not set in environment.")
        sys.exit(1)

    load_seen_ids()
    create_lock_file()

    async def on_start(app: Application):
        asyncio.create_task(monitor(app))

    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(on_start)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, user_message)
    )

    print("🚀 BOT STARTED")
    try:
        app.run_polling(drop_pending_updates=True)
    finally:
        save_seen_ids()
        remove_lock_file()


if __name__ == "__main__":
    main()
