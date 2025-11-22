#!/usr/bin/env python3

import logging
import requests
from bs4 import BeautifulSoup

# Test debug script to check current phone extraction
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_phone_extraction():
    """Test phone extraction on crash page"""
    
    # Headers for SS.lv
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'lv,en-US;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive'
    }
    
    # Test regular page
    crash_url = 'https://www.ss.lv/lv/transport/cars/toyota/today/sell/'
    
    try:
        print(f"Testing phone extraction from: {crash_url}")
        
        response = requests.get(crash_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table_rows = soup.select('tr[id^="tr_"]')
        
        print(f"Found {len(table_rows)} listings")
        
        for i, row in enumerate(table_rows[:3]):  # Test first 3 listings
            print(f"\n--- Testing listing {i+1} ---")
            
            # Extract basic info
            title_element = row.select_one('td.msg2 a.am')
            if not title_element:
                print("No title found - skipping")
                continue
                
            title = title_element.get_text(strip=True)
            link = title_element.get('href', '')
            if link and not link.startswith('http'):
                link = 'https://www.ss.lv' + link
                
            print(f"Title: {title}")
            print(f"Link: {link}")
            
            # Test phone extraction methods
            phone = 'N/A'
            
            # Method 1: ads_contacts cell
            phone_cell = row.select_one('td.ads_contacts')
            if phone_cell:
                phone_text = phone_cell.get_text(strip=True)
                print(f"ads_contacts cell: '{phone_text}'")
                if phone_text and ('+371' in phone_text or '(' in phone_text):
                    if 'Parādīt tālruni' in phone_text:
                        phone = phone_text.replace('Parādīt tālruni', '').strip()
                    else:
                        phone = phone_text
                    print(f"Method 1 result: {phone}")
            
            # Method 2: Check for right-aligned cells
            if phone == 'N/A':
                phone_candidates = row.select('td.msga2-o.ar, td[align="right"]')
                print(f"Found {len(phone_candidates)} right-aligned cells")
                for j, candidate in enumerate(phone_candidates):
                    phone_text = candidate.get_text(strip=True)
                    print(f"  Cell {j}: '{phone_text}'")
                    if phone_text and ('+371' in phone_text or phone_text.replace('-', '').replace(' ', '').isdigit()):
                        phone = phone_text
                        print(f"Method 2 result: {phone}")
                        break
            
            # Method 3: Data attributes
            if phone == 'N/A':
                if title_element.get('data'):
                    phone = 'Pieejams sarakstē'
                    print(f"Method 3 result: {phone}")
            
            # Method 4: Phone reveal mechanism
            if phone == 'N/A':
                phone_reveal = row.select_one('[onclick*="phone"], [id*="phone"], .phone')
                if phone_reveal:
                    phone = 'Noklikšķiniet, lai redzētu'
                    print(f"Method 4 result: {phone}")
            
            # Method 5: Fallback
            if phone == 'N/A':
                phone = 'Skatīt sludinājumā'
                print(f"Method 5 (fallback): {phone}")
            
            print(f"Final phone: {phone}")
            
            # Show how it would appear in message
            if phone == 'N/A':
                phone_display = '❓ Nav norādīts'
            elif phone in ['Pieejams sarakstē', 'Noklikšķiniet, lai redzētu', 'Skatīt sludinājumā']:
                phone_display = f'📱 {phone}'
            else:
                phone_display = f'📞 {phone}'
                
            print(f"Message display: {phone_display}")
            print("-" * 50)
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_phone_extraction()