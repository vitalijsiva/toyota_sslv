import sys
import asyncio
sys.path.insert(0, '.')
from toyota import scrape_listings, filter_benzina_toyotas, format_listing_message
from telegram import Bot
import os
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = input("Enter your Telegram chat ID: ")

async def send_not_sent_listings():
    print("Scraping all listings...")
    listings = scrape_listings()
    print(f"Total scraped: {len(listings)}")
    
    print("\nFiltering...")
    filtered = filter_benzina_toyotas(listings)
    print(f"Filtered (normally sent): {len(filtered)}")
    
    # Find what's NOT being sent
    not_sent = [l for l in listings if l not in filtered]
    print(f"\nNOT being sent: {len(not_sent)}")
    
    if not not_sent:
        print("No listings to send!")
        return
    
    print(f"\n🤖 Sending {len(not_sent)} listings to Telegram...")
    
    bot = Bot(token=TELEGRAM_TOKEN)
    
    for i, listing in enumerate(not_sent, 1):
        try:
            message, reply_markup = await format_listing_message(listing)
            
            # Add reason tag
            text = (listing['title'] + ' ' + listing['description']).lower()
            reason = ""
            if 'hybrid' in text or 'hibr' in text:
                reason = "⚠️ HYBRID"
            elif any(d in text for d in ['diesel', 'dīzeļ', 'd-4d', 'd4d']):
                reason = "⚠️ DIESEL"
            else:
                reason = "❓ UNKNOWN FUEL TYPE"
            
            message = f"{reason}\n\n{message}"
            
            await bot.send_message(
                chat_id=CHAT_ID,
                text=message,
                parse_mode='HTML',
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            print(f"  ✅ Sent {i}/{len(not_sent)}: {listing['title'][:50]}...")
            await asyncio.sleep(1)  # Delay to avoid rate limits
            
        except Exception as e:
            print(f"  ❌ Error sending {i}: {e}")
    
    print(f"\n✅ Done! Sent {len(not_sent)} listings")

if __name__ == "__main__":
    asyncio.run(send_not_sent_listings())
