"""
Toyota Defective Car Listings Telegram Bot

This bot scrapes ss.lv for Toyota Land Cruiser and Hilux listings
that mention "defekti" (defects) and sends them to Telegram users.
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from dotenv import load_dotenv
import asyncio
import time

# Fix encoding issues on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# Configure logging with more detailed output
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('toyota_bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Disable httpx INFO logs to reduce noise
logging.getLogger('httpx').setLevel(logging.WARNING)

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SS_LV_URLS = [
    'https://www.ss.lv/lv/transport/cars/toyota/today/sell/filter/',
    'https://www.ss.lv/lv/transport/other/transport-with-defects-or-after-crash/sell/filter/',
    'https://www.ss.lv/lv/transport/cars/toyota/hilux/sell/filter/',
    'https://www.ss.lv/lv/transport/cars/toyota/land-cruiser/sell/filter/'
]
REQUEST_TIMEOUT = 10  # seconds
CHECK_INTERVAL = 30  # Check every 30 seconds for instant notifications
MAX_RETRIES = 3  # Maximum retries for failed requests

# Models to filter
TARGET_MODELS = ['land cruiser', 'hilux', 'toyota']

# Storage for subscribed users and seen listings
subscribed_users = set()
seen_listing_ids = set()


def scrape_listings() -> Optional[List[Dict[str, str]]]:
    """
    Scrape Toyota car listings from multiple ss.lv URLs
    
    Returns:
        List of dictionaries containing title, price, link, and description
        Returns None if all requests fail
    """
    all_listings = []
    
    for url in SS_LV_URLS:
        try:
            logger.info(f"Fetching listings from {url}")
            
            # Set headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all listing rows (ss.lv uses table structure)
            # The listings are typically in a table with id="page_main"
            table_rows = soup.select('tr[id^="tr_"]')
            
            for row in table_rows:
                try:
                    # Extract listing details
                    # Title is typically in the second or third td
                    title_element = row.select_one('td.msg2 a.am, td.msga2 a.am')
                    if not title_element:
                        continue
                    
                    title = title_element.get_text(strip=True)
                    link = title_element.get('href', '')
                    
                    # Extract listing ID from the row id attribute
                    listing_id = row.get('id', '')
                    
                    # Make link absolute if it's relative
                    if link and not link.startswith('http'):
                        link = f"https://www.ss.lv{link}"
                    
                    # Extract price (it's the last td.msga2-o.pp6 cell in the row)
                    price_elements = row.select('td.msga2-o.pp6')
                    if price_elements:
                        price = price_elements[-1].get_text(strip=True)  # Get the last one (price)
                    else:
                        price = 'N/A'
                    
                    # Clean up price formatting - ensure EUR is present
                    if price != 'N/A' and 'EUR' not in price.upper() and '€' not in price:
                        # Check if it's a numeric price (may contain spaces, commas, dots)
                        price_clean = price.replace(' ', '').replace(',', '').replace('.', '').replace('?', '')
                        if price_clean.isdigit():
                            price = f"{price} €"
                    
                    # Extract phone number (typically in a td with class 'msga2-o ar' or contains phone icon)
                    phone = 'N/A'
                    phone_element = row.select_one('td.msga2-o.ar')
                    if phone_element:
                        phone_text = phone_element.get_text(strip=True)
                        if phone_text and phone_text != '':
                            phone = phone_text
                    
                    # Extract additional info (description/details)
                    details_elements = row.select('td.msga2')
                    description = ' '.join([el.get_text(strip=True) for el in details_elements])
                    
                    all_listings.append({
                        'id': listing_id,
                        'title': title,
                        'price': price,
                        'phone': phone,
                        'link': link,
                        'description': description
                    })
                    
                except Exception as e:
                    logger.warning(f"Error parsing listing row: {e}")
                    continue
            
            logger.info(f"Successfully scraped {len(table_rows)} listings from {url}")
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout while fetching from {url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error from {url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while scraping {url}: {e}")
    
    if not all_listings:
        logger.error("Failed to fetch listings from all URLs")
        return None
    
    logger.info(f"Total scraped {len(all_listings)} listings from all sources")
    return all_listings


def filter_defective_cars(listings: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Filter listings for Land Cruiser and Hilux with "defekti" keyword
    
    Args:
        listings: List of car listings
        
    Returns:
        Filtered list containing only target models with defects
    """
    if not listings:
        return []
    
    filtered = []
    
    for listing in listings:
        title_lower = listing['title'].lower()
        description_lower = listing['description'].lower()
        combined_text = f"{title_lower} {description_lower}"
        
        # Check if listing is for target models
        is_target_model = any(model in title_lower for model in TARGET_MODELS)
        
        # Check if "defekti" is mentioned
        has_defects = 'defekt' in combined_text  # "defekt" will match "defekti", "defekts", etc.
        
        if is_target_model and has_defects:
            filtered.append(listing)
    
    logger.info(f"Filtered {len(filtered)} defective listings from {len(listings)} total")
    return filtered


def filter_benzina_toyotas(listings: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Filter listings for:
    1. All petrol/gasoline Toyotas
    2. Diesel Hilux
    3. Diesel Land Cruiser
    
    Args:
        listings: List of car listings from Toyota section
        
    Returns:
        Filtered list matching the criteria
    """
    if not listings:
        return []
    
    filtered = []
    
    for listing in listings:
        title_lower = listing['title'].lower()
        description_lower = listing['description'].lower()
        combined_text = f"{title_lower} {description_lower}"
        
        # Check if it's a Toyota (should be since we're in Toyota section)
        is_toyota = 'toyota' in combined_text
        
        # Check if it's Hilux or Land Cruiser
        is_hilux = 'hilux' in combined_text
        is_land_cruiser = 'land cruiser' in combined_text or 'landcruiser' in combined_text
        
        # Check fuel type - petrol/gasoline
        is_petrol = any(keyword in combined_text for keyword in ['benzīn', 'benz.', 'benz', 'petrol', 'gas'])
        
        # Check fuel type - diesel
        is_diesel = any(keyword in combined_text for keyword in ['dīzel', 'diesel', 'diz.'])
        
        # Include if:
        # 1. Any Toyota with petrol/gasoline, OR
        # 2. Hilux with diesel, OR
        # 3. Land Cruiser with diesel
        if (is_toyota and is_petrol) or (is_hilux and is_diesel) or (is_land_cruiser and is_diesel):
            filtered.append(listing)
    
    logger.info(f"Filtered {len(filtered)} matching listings (petrol Toyotas + diesel Hilux/Land Cruiser) from {len(listings)} total")
    return filtered


def format_listings_message(listings: List[Dict[str, str]]) -> str:
    """
    Format listings into a clean Telegram message
    
    Args:
        listings: List of car listings
        
    Returns:
        Formatted string message
    """
    if not listings:
        return "🔍 No matching listings found at the moment.\n\nLooking for:\n✅ All petrol/gasoline Toyotas\n✅ Diesel Hilux\n✅ Diesel Land Cruiser"
    
    message = f"🚗 Found {len(listings)} listing(s):\n\n"
    
    for i, listing in enumerate(listings, 1):
        message += f"{i}. {listing['title']}\n"
        message += f"💰 {listing['price']}\n"
        message += f"📞 {listing['phone']}\n"
        message += f"🔗 Link: {listing['link']}\n\n"
    
    message += f"⏰ Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    return message


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command - greet user and explain bot usage
    """
    welcome_message = (
        "👋 Welcome to the Toyota Car Notifier Bot!\n\n"
        "This bot monitors ss.lv for Toyota listings.\n\n"
        "📋 Available commands:\n"
        "/start - Show this welcome message\n"
        "/subscribe - Get instant notifications for new listings\n"
        "/unsubscribe - Stop receiving notifications\n"
        "/search - Search current matching listings\n\n"
        "⚡ Instant notifications - get alerts within 30 seconds!\n\n"
        "🔍 Monitoring:\n"
        "• All petrol/gasoline Toyotas\n"
        "• Diesel Hilux\n"
        "• Diesel Land Cruiser\n\n"
        "Happy car hunting! 🚙"
    )
    
    await update.message.reply_text(welcome_message)
    logger.info(f"User {update.effective_user.id} started the bot")


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Subscribe user to instant notifications for new Toyota listings
    """
    user_id = update.effective_user.id
    subscribed_users.add(user_id)
    
    message = (
        "✅ Subscribed to instant notifications!\n\n"
        "You will receive alerts for:\n"
        "• All petrol/gasoline Toyotas\n"
        "• Diesel Hilux\n"
        "• Diesel Land Cruiser\n\n"
        "📬 New listings will be sent instantly!\n\n"
        "Use /unsubscribe to stop notifications."
    )
    
    await update.message.reply_text(message)
    logger.info(f"User {user_id} subscribed to notifications")


async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Unsubscribe user from notifications
    """
    user_id = update.effective_user.id
    if user_id in subscribed_users:
        subscribed_users.remove(user_id)
        message = "❌ Unsubscribed from notifications."
    else:
        message = "You are not currently subscribed to notifications."
    
    await update.message.reply_text(message)
    logger.info(f"User {user_id} unsubscribed from notifications")


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /search command - search for matching Toyota listings
    """
    logger.info(f"User {update.effective_user.id} requested search listings")
    
    await update.message.reply_text("🔍 Searching for matching listings...")
    
    try:
        listings = scrape_listings()
        
        if listings is None:
            error_message = (
                "❌ Failed to fetch listings from ss.lv.\n"
                "Please try again later or check your internet connection."
            )
            await update.message.reply_text(error_message)
            return
        
        benzina_listings = filter_benzina_toyotas(listings)
        message = format_listings_message(benzina_listings)
        
        if len(message) > 4096:
            parts = [message[i:i+4096] for i in range(0, len(message), 4096)]
            for part in parts:
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(message)
            
    except Exception as e:
        logger.error(f"Error in search_command: {e}")
        await update.message.reply_text(
            "❌ An unexpected error occurred. Please try again later."
        )


async def scheduled_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Scheduled task to check for new Toyota listings
    Sends instant notifications to subscribed users for new listings only
    """
    logger.info("Running scheduled check for new Toyota listings")
    
    try:
        listings = scrape_listings()
        
        if listings is None:
            logger.warning("Scheduled check: Failed to fetch listings")
            return
        
        # Filter for matching Toyotas
        defective_listings = filter_benzina_toyotas(listings)
        
        # Find NEW listings (not seen before)
        new_listings = []
        for listing in defective_listings:
            listing_id = listing.get('id', listing['link'])
            if listing_id not in seen_listing_ids:
                new_listings.append(listing)
        
        # Only send notifications if there are subscribed users
        if new_listings and subscribed_users:
            logger.info(f"Found {len(new_listings)} NEW listings - sending to {len(subscribed_users)} users")
            
            # Send each new listing individually
            for listing in new_listings:
                # Mark as seen BEFORE sending (to avoid duplicates if there's an error)
                listing_id = listing.get('id', listing['link'])
                seen_listing_ids.add(listing_id)
                
                notification = (
                    f"🆕 NEW LISTING!\n\n"
                    f"🚗 {listing['title']}\n"
                    f"💰 {listing['price']}\n"
                    f"📞 {listing['phone']}\n"
                    f"🔗 {listing['link']}\n\n"
                    f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                )
                
                # Send to all subscribed users (one by one)
                for user_id in subscribed_users.copy():
                    try:
                        await context.bot.send_message(chat_id=user_id, text=notification)
                        logger.info(f"Sent NEW listing '{listing['title']}' to user {user_id}")
                        # Small delay between messages to avoid rate limiting
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        logger.error(f"Failed to send notification to user {user_id}: {e}")
                        # Remove user if they blocked the bot
                        if "Forbidden" in str(e):
                            subscribed_users.discard(user_id)
        elif new_listings:
            logger.info(f"Found {len(new_listings)} new listings, but no subscribed users")
            # Still mark them as seen
            for listing in new_listings:
                listing_id = listing.get('id', listing['link'])
                seen_listing_ids.add(listing_id)
        else:
            logger.info(f"No new listings found. Total matching: {len(defective_listings)}, all previously seen")
        
        # Update context
        context.bot_data['last_check'] = {
            'time': datetime.now(),
            'total': len(defective_listings),
            'new': len(new_listings)
        }
    
    except Exception as e:
        logger.error(f"Error in scheduled check: {e}")


def main() -> None:
    """
    Main function to run the bot
    """
    # Check if token is configured
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        print("Please set TELEGRAM_BOT_TOKEN in your .env file")
        return
    
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    application.add_handler(CommandHandler("search", search_command))
    
    # Add scheduled job for instant notifications (runs every 30 seconds)
    job_queue = application.job_queue
    job_queue.run_repeating(
        scheduled_check,
        interval=CHECK_INTERVAL,
        first=30  # First run after 30 seconds
    )
    
    logger.info("Bot started successfully with instant notifications!")
    print("🤖 Toyota Notifier Bot is running...")
    print(f"🔍 Monitoring 4 sources:")
    print(f"   1. Toyota section (today/sell)")
    print(f"   2. Transport with defects/after crash (sell)")
    print(f"   3. Toyota Hilux (sell)")
    print(f"   4. Toyota Land Cruiser (sell)")
    print(f"⛽ Filters: Petrol Toyotas + Diesel Hilux/Land Cruiser")
    print(f"⚡ Checking for new cars every {CHECK_INTERVAL} seconds")
    print(f"📝 Logging to: toyota_bot.log")
    print("Press Ctrl+C to stop")
    
    # Run the bot
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")


if __name__ == '__main__':
    main()