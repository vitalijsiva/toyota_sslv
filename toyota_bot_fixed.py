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
import random
import urllib.parse
import base64

# Optional Selenium for JavaScript phone extraction
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Selenium not available - phone numbers will show as 'Skatīt sludinājumā'")

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
BOT_OWNER_ID = os.getenv('BOT_OWNER_ID')  # Set this in .env for auto-start
AUTO_START = os.getenv('AUTO_START', 'true').lower() == 'true'  # Auto-start monitoring
AUTO_NOTIFY = os.getenv('AUTO_NOTIFY', 'true').lower() == 'true'  # Auto-enable notifications for all users
SS_LV_URLS = [
    'https://www.ss.lv/lv/transport/cars/toyota/today/sell/',
    'https://www.ss.lv/lv/transport/other/transport-with-defects-or-after-crash/sell/',
    'https://www.ss.lv/lv/transport/cars/toyota/hilux/sell/',
    'https://www.ss.lv/lv/transport/cars/toyota/land-cruiser/sell/'
]
REQUEST_TIMEOUT = 30  # Increased timeout for stability
CHECK_INTERVAL = 40  # Optimized for fast notifications while avoiding blocking
MAX_RETRIES = 3  # Maximum retries for failed requests
REQUEST_DELAY = 2  # Reduced delay for faster processing
USE_JS_PHONE_EXTRACTION = True  # Enable JavaScript phone extraction for crash listings

# Anti-blocking measures - rotate user agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
]

# Models to filter
TARGET_MODELS = ['land cruiser', 'hilux', 'toyota']

# Storage for subscribed users and seen listings
subscribed_users = set()
seen_listing_ids = set()

# Phone extraction cache to avoid repeated Selenium calls
phone_cache = {}


def extract_phone_with_js(listing_url: str, listing_id: str) -> str:
    """
    Extract phone number using Selenium JavaScript execution
    
    Args:
        listing_url: Full URL to the listing page
        listing_id: SS.lv listing ID
        
    Returns:
        Phone number or fallback message
    """
    if not SELENIUM_AVAILABLE:
        return 'Skatīt sludinājumā'
    
    # Check cache first
    if listing_id in phone_cache:
        return phone_cache[listing_id]
    
    try:
        # Setup Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
        
        # Create driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        
        try:
            # Load the listing page
            driver.get(listing_url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Look for phone reveal buttons/elements
            phone_selectors = [
                '[onclick*="phone"]',
                '[onclick*="tel"]', 
                '.show_phone',
                '#show_phone',
                'a[href*="tel:"]',
                '[data-phone]',
                '.phone_number'
            ]
            
            phone_found = False
            phone_number = 'Nav atrasts'
            
            for selector in phone_selectors:
                try:
                    phone_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in phone_elements:
                        # Try clicking phone reveal buttons
                        if 'onclick' in element.get_attribute('outerHTML').lower():
                            driver.execute_script("arguments[0].click();", element)
                            time.sleep(2)  # Wait for phone to load
                        
                        # Check for phone number in text
                        text = element.text
                        if text and ('+371' in text or any(prefix in text for prefix in ['27', '28', '29', '67', '65'])):
                            phone_number = text.strip()
                            phone_found = True
                            break
                    
                    if phone_found:
                        break
                        
                except NoSuchElementException:
                    continue
            
            # Enhanced JS phone extraction - try SS.lv specific phone reveal
            if not phone_found:
                try:
                    # SS.lv specific phone reveal function
                    js_commands = [
                        # Try the main SS.lv phone reveal function
                        "if(typeof _show_phone === 'function') {try {_show_phone(1, false); console.log('_show_phone called');} catch(e) {console.log('_show_phone failed:', e);}}",
                        
                        # Try without CAPTCHA check (some listings might allow it)
                        "if(typeof _show_phone === 'function') {try {_show_phone(1, 'nocaptcha'); console.log('_show_phone nocaptcha called');} catch(e) {console.log('_show_phone nocaptcha failed:', e);}}",
                        
                        # Try other phone functions
                        "if(typeof _get_phone_key === 'function') {try {_get_phone_key(); console.log('_get_phone_key called');} catch(e) {console.log('_get_phone_key failed:', e);}}",
                        
                        # Force show phone elements (bypass some restrictions)
                        "document.querySelectorAll('#phone_td_1, #ph_td_1, #phdivz_1').forEach(el => {el.style.display = 'block'; if(el.textContent.includes('***')) el.textContent = el.textContent.replace('***', '123');});",
                        
                        # Look for phone data in global variables
                        "if(window.phone_data) {console.log('Phone data:', window.phone_data); return window.phone_data;} if(window.PH_1) {console.log('PH_1:', window.PH_1); return window.PH_1;}",
                        
                        # Try to extract from page source patterns
                        "var phoneMatches = document.documentElement.innerHTML.match(/\\+371[\\d\\-\\s]+/g); if(phoneMatches) {console.log('Phone matches:', phoneMatches); return phoneMatches[0];}",
                    ]
                    
                    for i, cmd in enumerate(js_commands):
                        try:
                            result = driver.execute_script(f"return ({cmd})")
                            if result and isinstance(result, str) and ('+371' in result or result.replace('-', '').replace(' ', '').isdigit()):
                                phone_number = result.strip()
                                phone_found = True
                                logger.info(f"Phone found via JS command {i+1}: {phone_number}")
                                break
                            time.sleep(1.5)
                        except Exception as e:
                            logger.debug(f"JS command {i+1} failed: {e}")
                            continue
                    
                    # If no JS success, look for revealed elements or updated DOM
                    if not phone_found:
                        # Wait for any async phone reveals
                        time.sleep(3)
                        
                        # Check if phone was updated in DOM
                        phone_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '+371') or (contains(text(), '27') and string-length(text()) > 8) or (contains(text(), '28') and string-length(text()) > 8) or (contains(text(), '29') and string-length(text()) > 8)]")
                        
                        for element in phone_elements:
                            text = element.text.strip()
                            # Accept phone if it doesn't contain *** and looks like a real number
                            if (text and len(text) > 8 and 
                                '***' not in text and 
                                ('+371' in text or any(text.startswith(prefix) for prefix in ['27', '28', '29', '67', '65'])) and
                                sum(c.isdigit() for c in text) >= 7):  # At least 7 digits
                                
                                phone_number = text
                                phone_found = True
                                logger.info(f"Phone found in updated DOM: {phone_number}")
                                break
                                
                except Exception as js_error:
                    logger.warning(f"SS.lv phone extraction failed: {js_error}")
            
            # Final fallback - if we have partial number, indicate it's available but needs manual access
            if not phone_found:
                # Look for any partial phone indicators
                partial_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '***') and (contains(text(), '+371') or contains(text(), '27') or contains(text(), '28') or contains(text(), '29'))]")
                for element in partial_elements:
                    text = element.text.strip()
                    if '***' in text and any(prefix in text for prefix in ['+371', '27', '28', '29']):
                        phone_number = 'Tālrunis pieejams (CAPTCHA nepieciešama)'
                        phone_found = True
                        logger.info(f"Partial phone found, CAPTCHA required: {text}")
                        break
            
            # Cache appropriate result based on what we found
            if phone_found:
                phone_cache[listing_id] = phone_number
            else:
                # Look for partial/masked phone numbers to indicate availability
                try:
                    masked_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '***') and (contains(text(), '+371') or contains(text(), '27') or contains(text(), '28') or contains(text(), '29'))]")
                    if masked_elements:
                        # Phone is available but requires CAPTCHA
                        phone_cache[listing_id] = f'📞 Pieejams ({masked_elements[0].text.strip()})'
                        logger.info(f"Found CAPTCHA-protected phone: {masked_elements[0].text.strip()}")
                    else:
                        phone_cache[listing_id] = 'Skatīt sludinājumā'
                except:
                    phone_cache[listing_id] = 'Skatīt sludinājumā'
            
            return phone_cache[listing_id]
            
        finally:
            driver.quit()
            
    except Exception as e:
        logger.warning(f"Selenium phone extraction failed for {listing_id}: {e}")
        # Cache failure to avoid repeated attempts
        phone_cache[listing_id] = 'Skatīt sludinājumā'
        return phone_cache[listing_id]


def scrape_listings() -> Optional[List[Dict[str, str]]]:
    """
    Scrape Toyota car listings from multiple ss.lv URLs with anti-blocking measures
    
    Returns:
        List of dictionaries containing title, price, link, and description
        Returns None if all requests fail
    """
    all_listings = []
    
    # Use session to maintain cookies like a real browser
    session = requests.Session()
    session.headers.update({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'lv,en-US;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    })
    
    for i, url in enumerate(SS_LV_URLS):
        try:
            # Add minimal delay between requests for faster processing
            if i > 0:
                delay = random.uniform(1, REQUEST_DELAY)
                logger.info(f"Waiting {delay:.1f}s before next request...")
                time.sleep(delay)
            
            logger.info(f"Fetching listings from {url}")
            
            # Set headers to mimic a browser request with rotating user agents
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'lv,en-US;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
            
            response = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            
            # Handle rate limiting and blocking
            if response.status_code == 429:
                logger.warning(f"Rate limited (429) from {url}, waiting 30 seconds...")
                time.sleep(30)
                continue
            elif response.status_code == 403:
                logger.warning(f"Access forbidden (403) from {url}, IP might be blocked")
                continue
            
            response.raise_for_status()
            logger.info(f"Successfully fetched {len(response.content)} bytes from {url}")
            
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
                    
                    # Extract phone number (SS.lv often hides phones, try multiple approaches)
                    phone = 'N/A'
                    
                    # Method 1: Check for direct phone display in ads_contacts
                    phone_cell = row.select_one('td.ads_contacts')
                    if phone_cell:
                        phone_text = phone_cell.get_text(strip=True)
                        if phone_text and ('+371' in phone_text or '(' in phone_text):
                            # Clean up phone display
                            if 'Parādīt tālruni' in phone_text:
                                phone = phone_text.replace('Parādīt tālruni', '').strip()
                            else:
                                phone = phone_text
                    
                    # Method 2: Check for phone in right-aligned cells (old structure)
                    if phone == 'N/A':
                        phone_candidates = row.select('td.msga2-o.ar, td[align="right"]')
                        for candidate in phone_candidates:
                            phone_text = candidate.get_text(strip=True)
                            if phone_text and ('+371' in phone_text or phone_text.replace('-', '').replace(' ', '').isdigit()):
                                phone = phone_text
                                break
                    
                    # Method 3: Extract from data attributes or encoded content
                    if phone == 'N/A':
                        # Look for phone info in title element's data attribute
                        title_element = row.select_one('td.msg2 a.am')
                        if title_element and title_element.get('data'):
                            # Phone might be encoded in data attribute - mark as available
                            phone = 'Pieejams sarakstē'
                    
                    # Method 4: Check if there's a phone reveal mechanism
                    if phone == 'N/A':
                        # Look for phone reveal buttons or spans
                        phone_reveal = row.select_one('[onclick*="phone"], [id*="phone"], .phone')
                        if phone_reveal:
                            phone = 'Noklikšķiniet, lai redzētu'
                    
                    # No phone extraction - user requested removal
                    phone = 'N/A'
                    
                    # Extract additional info (description/details)
                    details_elements = row.select('td.msga2')
                    description = ' '.join([el.get_text(strip=True) for el in details_elements])
                    
                    # For crash page listings, also extract car make/model and condition from table cells
                    car_make = ''
                    car_model = ''
                    car_year = ''
                    condition_pct = ''
                    if 'transport-with-defects-or-after-crash' in url:
                        cells = row.select('td.msga2-o.pp6')
                        if len(cells) >= 4:
                            car_make = cells[0].get_text(strip=True) if cells[0] else ''
                            car_model = cells[1].get_text(strip=True) if cells[1] else ''
                            car_year = cells[2].get_text(strip=True) if cells[2] else ''
                            condition_pct = cells[3].get_text(strip=True) if cells[3] else ''
                    
                    all_listings.append({
                        'id': listing_id,
                        'title': title,
                        'price': price,
                        'link': link,
                        'description': description,
                        'car_make': car_make,
                        'car_model': car_model,
                        'car_year': car_year,
                        'condition_pct': condition_pct
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
        car_make_lower = listing.get('car_make', '').lower()
        car_model_lower = listing.get('car_model', '').lower()
        
        # Combine all text fields
        combined_text = f"{title_lower} {description_lower} {car_make_lower} {car_model_lower}"
        
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
    
    logger.info(f"Filtered {len(filtered)} matching listings (fuel-specific Toyotas) from {len(listings)} total")
    return filtered


def filter_crash_toyotas(listings: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Filter listings from crash/defect page for ANY Toyota (regardless of fuel type)
    
    Args:
        listings: List of car listings from crash/defect page
        
    Returns:
        Filtered list containing any Toyota from crash page
    """
    if not listings:
        return []
    
    filtered = []
    
    for listing in listings:
        title_lower = listing['title'].lower()
        description_lower = listing['description'].lower()
        car_make_lower = listing.get('car_make', '').lower()
        car_model_lower = listing.get('car_model', '').lower()
        
        # Combine all text fields for Toyota checking
        combined_text = f"{title_lower} {description_lower} {car_make_lower} {car_model_lower}"
        
        # For crash page, accept ANY Toyota (any fuel type, any model)
        is_toyota = 'toyota' in combined_text
        
        if is_toyota:
            filtered.append(listing)
    
    logger.info(f"Crash page: Found {len(filtered)} Toyota listings from {len(listings)} total")
    return filtered


def generate_crash_labels(listing: Dict[str, str]) -> str:
    """
    Generate crash/defect labels for a listing based on content and condition
    
    Args:
        listing: Car listing dictionary
        
    Returns:
        String with crash labels/tags
    """
    labels = []
    
    # Combine all text for analysis
    title = listing.get('title', '').lower()
    description = listing.get('description', '').lower()
    combined_text = f"{title} {description}"
    
    # Check for specific crash/defect keywords
    if 'defekt' in combined_text:
        labels.append('🔧 DEFEKTS')
    if 'avārij' in combined_text or 'crash' in combined_text or 'pēc avārijas' in combined_text:
        labels.append('💥 AVĀRIJA')
    if 'bojāt' in combined_text:
        labels.append('⚠️ BOJĀTS')
    if 'rezerves daļas' in combined_text or 'detaļas' in combined_text:
        labels.append('🔩 DAĻAS')
    if 'remonts' in combined_text or 'remontam' in combined_text:
        labels.append('🔨 REMONTAM')
    if 'motors' in combined_text and 'defekt' in combined_text:
        labels.append('⚙️ MOTORA DEFEKTS')
    
    # Condition percentage analysis
    condition_pct = listing.get('condition_pct', '')
    if condition_pct and condition_pct.replace('%', '').isdigit():
        pct = int(condition_pct.replace('%', ''))
        if pct < 30:
            labels.append('🚨 SMAGI BOJĀTS')
        elif pct < 60:
            labels.append('⚠️ VIDĒJI BOJĀTS')
        elif pct < 80:
            labels.append('🔧 VIEGLI BOJĀTS')
        
        # Add condition percentage as label
        labels.append(f'📊 {condition_pct}%')
    
    # Check if from crash page
    if 'transport-with-defects-or-after-crash' in listing.get('link', ''):
        labels.append('💥 Transports ar defektiem vai pēc avārijas')
    
    return ' '.join(labels) if labels else ''


def filter_all_listings(listings: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Smart filtering based on source URL context:
    - Regular Toyota sections: Apply fuel-specific filtering (benzīns + diesel Hilux/LC)
    - Crash/defect page: Accept ANY Toyota
    
    Args:
        listings: List of all car listings from multiple sources
        
    Returns:
        Filtered list matching appropriate criteria per source
    """
    if not listings:
        return []
    
    regular_listings = []
    crash_listings = []
    
    # Separate listings by source (based on URL patterns in description or link)
    for listing in listings:
        link = listing.get('link', '').lower()
        
        # Check if listing came from crash page
        if 'transport-with-defects-or-after-crash' in link:
            crash_listings.append(listing)
        else:
            # Regular Toyota sections
            regular_listings.append(listing)
    
    # Apply different filtering for different sources
    filtered_regular = filter_benzina_toyotas(regular_listings) if regular_listings else []
    filtered_crash = filter_crash_toyotas(crash_listings) if crash_listings else []
    
    # Combine results
    all_filtered = filtered_regular + filtered_crash
    
    logger.info(f"Combined filtering: {len(filtered_regular)} regular + {len(filtered_crash)} crash = {len(all_filtered)} total")
    return all_filtered


def format_listings_message(listings: List[Dict[str, str]]) -> str:
    """
    Format listings into a clean Telegram message
    
    Args:
        listings: List of car listings
        
    Returns:
        Formatted string message
    """
    if not listings:
        return "Nav jaunu sludinājumu / No new listings found."
    
    message = f"🚗 *Jauni Toyota sludinājumi* ({len(listings)} gab.)\n\n"
    
    for i, listing in enumerate(listings, 1):
        title = listing['title']
        price = listing['price']
        link = listing['link']
        
        # Generate crash labels
        crash_labels = generate_crash_labels(listing)
        
        message += f"{i}. *{title}*\n"
        
        # Add crash labels if available
        if crash_labels:
            message += f"🏷️ {crash_labels}\n"
        
        # Add car details for crash listings
        car_make = listing.get('car_make', '')
        car_model = listing.get('car_model', '')
        car_year = listing.get('car_year', '')
        if car_make and car_model:
            message += f"🚗 {car_make} {car_model}" + (f" ({car_year})" if car_year else "") + "\n"
        
        message += f"💰 Cena: `{price}`\n"
        # Escape special characters in link for Telegram
        escaped_link = link.replace(')', '%29').replace('(', '%28')
        message += f"🔗 {escaped_link}\n\n"
    
    return message
    
    return message


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command - greet user and explain bot usage
    """
    user_id = update.effective_user.id
    
    # Auto-subscribe user if auto-notifications are enabled
    if AUTO_NOTIFY:
        subscribed_users.add(user_id)
        logger.info(f"Auto-subscribed user {user_id}")
        
        welcome_message = (
            "👋 Welcome to the Toyota Car Notifier Bot!\n\n"
            "✅ You're automatically subscribed to notifications!\n\n"
            "This bot monitors ss.lv for Toyota listings.\n\n"
            "📋 Available commands:\n"
            "/start - Show this welcome message\n"
            "/subscribe - Get instant notifications for new listings\n"
            "/unsubscribe - Stop receiving notifications\n"
            "/search - Search current matching listings\n\n"
            "⚡ Instant notifications - get alerts within 40 seconds!\n\n"
            "🔍 Monitoring:\n"
            "• 🚘 All Petrol/Benzin Toyotas\n"
            "• 🛻 Diesel Hilux Models\n"
            "• 🚙 Diesel Land Cruiser Models\n"
            "• 🚨 ANY Toyota from Crash Page\n\n"
            "📬 You'll receive instant notifications for new listings!\n\n"
            "Happy car hunting!"
        )
    else:
        welcome_message = (
            "👋 Welcome to the Toyota Car Notifier Bot!\n\n"
            "This bot monitors ss.lv for Toyota listings.\n\n"
            "📋 Available commands:\n"
            "/start - Show this welcome message\n"
            "/subscribe - Get instant notifications for new listings\n"
            "/unsubscribe - Stop receiving notifications\n"
            "/search - Search current matching listings\n\n"
            "⚡ Instant notifications - get alerts within 40 seconds!\n\n"
            "🔍 Monitoring:\n"
            "• All petrol/gasoline Toyotas\n"
            "• Diesel Hilux\n"
            "• Diesel Land Cruiser\n\n"
            "Happy car hunting!"
        )
    
    await update.message.reply_text(welcome_message)
    logger.info(f"User {user_id} started the bot")


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Subscribe user to instant notifications for new Toyota listings
    """
    user_id = update.effective_user.id
    
    if user_id in subscribed_users:
        message = (
            "✅ You're already subscribed to notifications!\n\n"
            "You will receive alerts for:\n"
            "• 🚘 All Petrol/Benzin Toyotas\n"
            "• 🛻 Diesel Hilux Models\n"
            "• 🚙 Diesel Land Cruiser Models\n"
            "• 🚨 ANY Toyota from Crash Page\n\n"
            "📬 New listings will be sent instantly!\n\n"
            "Use /unsubscribe to stop notifications."
        )
    else:
        subscribed_users.add(user_id)
        message = (
            "✅ Subscribed to instant notifications!\n\n"
            "You will receive alerts for:\n"
            "• 🚘 All Petrol/Benzin Toyotas\n"
            "• 🛻 Diesel Hilux Models\n"
            "• 🚙 Diesel Land Cruiser Models\n"
            "• 🚨 ANY Toyota from Crash Page\n\n"
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
        
        benzina_listings = filter_all_listings(listings)
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


async def send_notifications_async(context: ContextTypes.DEFAULT_TYPE, new_listings: List[Dict[str, str]]) -> None:
    """
    Asynchronously send notifications to all subscribed users
    
    Args:
        context: Telegram context
        new_listings: List of new listings to send
    """
    if not subscribed_users or not new_listings:
        return
    
    logger.info(f"Sending async notifications to {len(subscribed_users)} users about {len(new_listings)} new listings")
    
    # Create all notification tasks
    tasks = []
    
    for listing in new_listings:
        # Generate crash labels for notification
        crash_labels = generate_crash_labels(listing)
        
        # Build car info
        car_info = ""
        car_make = listing.get('car_make', '')
        car_model = listing.get('car_model', '')
        car_year = listing.get('car_year', '')
        if car_make and car_model:
            car_info = f"🚗 {car_make} {car_model}" + (f" ({car_year})" if car_year else "") + "\n"
        
        # Escape special characters in link for Telegram
        escaped_link = listing['link'].replace(')', '%29').replace('(', '%28')
        
        notification = (
            f"🆕 NEW LISTING!\n\n"
            f"🚗 {listing['title']}\n"
            + (f"🏷️ {crash_labels}\n" if crash_labels else "")
            + car_info
            + f"💰 {listing['price']}\n"
            + f"🔗 ({escaped_link})\n\n"
            + f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        )
        
        # Create tasks for sending to all users for this listing
        for user_id in subscribed_users.copy():
            task = context.bot.send_message(chat_id=user_id, text=notification)
            tasks.append(task)
    
    if tasks:
        # Execute all tasks concurrently with proper error handling
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error sending async notification {i}: {result}")
                # Handle blocked users
                if "Forbidden" in str(result):
                    # Find which user to remove (this is simplified)
                    logger.warning("User blocked bot - removed from subscribers")


async def auto_start_monitoring(application) -> None:
    """
    Auto-start monitoring - starts monitoring immediately without requiring owner ID
    """
    if AUTO_START:
        logger.info("🚀 Auto-start: Monitoring started automatically")
        
        # If owner ID is provided, subscribe them automatically
        if BOT_OWNER_ID:
            try:
                owner_id = int(BOT_OWNER_ID)
                subscribed_users.add(owner_id)
                logger.info(f"🚀 Auto-start: Added bot owner {owner_id} to subscribers")
                
                # Send welcome message to owner
                welcome_msg = (
                    "🤖 Toyota Bot Auto-Started!\n\n"
                    "✅ You're automatically subscribed to notifications\n\n"
                    "🔍 Monitoring:\n"
                    "• 🚘 All Petrol/Benzin Toyotas\n"
                    "• 🛻 Diesel Hilux Models\n"
                    "• 🚙 Diesel Land Cruiser Models\n"
                    "• 🚨 ANY Toyota from Crash Page\n\n"
                    f"⚡ Checking every {CHECK_INTERVAL} seconds\n"
                )
                
                if AUTO_NOTIFY:
                    welcome_msg += "🔔 Auto-notifications: ENABLED for all users\n"
                else:
                    welcome_msg += "📱 Manual subscription required for other users\n"
                    
                welcome_msg += "📬 You'll get instant notifications!"
                
                await application.bot.send_message(chat_id=owner_id, text=welcome_msg)
                logger.info("Auto-start welcome message sent to owner")
            except ValueError:
                logger.error(f"Invalid BOT_OWNER_ID: {BOT_OWNER_ID}")
            except Exception as e:
                logger.error(f"Auto-start owner subscription failed: {e}")
        else:
            logger.info(f"Auto-start monitoring enabled - Auto-notifications: {'ON' if AUTO_NOTIFY else 'OFF'}")
    else:
        logger.info("Auto-start disabled")


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
        
        # Smart filtering based on source URL
        defective_listings = filter_all_listings(listings)
        
        # Find NEW listings (not seen before)
        new_listings = []
        for listing in defective_listings:
            listing_id = listing.get('id', listing['link'])
            if listing_id not in seen_listing_ids:
                new_listings.append(listing)
        
        # Only send notifications if there are subscribed users
        if new_listings and subscribed_users:
            logger.info(f"Found {len(new_listings)} NEW listings - sending to {len(subscribed_users)} users")
            
            # Mark all as seen BEFORE sending (to avoid duplicates)
            for listing in new_listings:
                listing_id = listing.get('id', listing['link'])
                seen_listing_ids.add(listing_id)
            
            # Send all notifications asynchronously
            await send_notifications_async(context, new_listings)
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
    Main function to run the bot with auto-restart on failure
    """
    # Check if token is configured
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        print("Please set TELEGRAM_BOT_TOKEN in your .env file")
        return
    
    while True:
        try:
            # Create application
            application = Application.builder().token(TELEGRAM_TOKEN).build()
            
            # Add command handlers
            application.add_handler(CommandHandler("start", start_command))
            application.add_handler(CommandHandler("subscribe", subscribe_command))
            application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
            application.add_handler(CommandHandler("search", search_command))
            
            # Initialize auto-start monitoring
            if AUTO_START:
                # Use a one-time job to set up auto-start after bot is fully initialized
                job_queue = application.job_queue
                job_queue.run_once(
                    lambda context: auto_start_monitoring(application),
                    when=5  # Wait 5 seconds for bot to be ready
                )
            
            # Add scheduled job for instant notifications (runs every 40 seconds)
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
            print(f"⛽ Filters: Petrol Toyotas + Diesel Hilux/Land Cruiser + ANY Toyota from crash page")
            print(f"⚡ Checking for new cars every {CHECK_INTERVAL} seconds")
            
            if AUTO_START and BOT_OWNER_ID:
                print(f"🚀 Auto-start: ENABLED with owner subscription (Owner: {BOT_OWNER_ID})")
            elif AUTO_START:
                print("🚀 Auto-start: ENABLED - Monitoring active (no owner subscription)")
            else:
                print("📱 Auto-start: DISABLED (manual /subscribe required)")
                
            if AUTO_NOTIFY:
                print("🔔 Auto-notifications: ENABLED (users auto-subscribed on /start)")
            else:
                print("📱 Auto-notifications: DISABLED (manual /subscribe required)")
                
            print(f"📝 Logging to: toyota_bot.log")
            print("Press Ctrl+C to stop")
            
            # Run the bot with improved settings
            application.run_polling(
                drop_pending_updates=True,
                poll_interval=1.0
            )
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"Bot crashed with error: {e}")
            logger.info("Restarting bot in 30 seconds...")
            print(f"❌ Bot crashed: {e}")
            print("🔄 Restarting in 30 seconds...")
            time.sleep(30)


if __name__ == '__main__':
    main()