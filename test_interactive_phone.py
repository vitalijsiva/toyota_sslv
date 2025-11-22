#!/usr/bin/env python3

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_phone_reveal_interaction():
    """Test interactive phone reveal on SS.lv"""
    
    try:
        print("=== INTERACTIVE PHONE REVEAL TEST ===")
        print("Testing user interaction patterns to reveal full phone...")
        
        # Setup Chrome options - NOT headless to see what happens
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Comment out to see browser
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1200,800')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        
        # Test URL
        test_url = 'https://www.ss.lv/msg/lv/transport/cars/toyota/corolla/ccnihn.html'
        
        print(f"Loading: {test_url}")
        driver.get(test_url)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        print("✅ Page loaded")
        
        # Look for phone reveal elements
        print("🔍 Looking for phone reveal mechanisms...")
        
        # Find elements that might reveal phone
        phone_reveal_selectors = [
            'a[onclick*="phone"]',
            'span[onclick*="phone"]', 
            'div[onclick*="phone"]',
            '[onclick*="show"]',
            '[onclick*="tel"]',
            'a[href*="javascript"]',
            '.show_phone',
            '#show_phone',
            'a[class*="phone"]',
            'span[class*="phone"]'
        ]
        
        reveal_elements = []
        for selector in phone_reveal_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    onclick = el.get_attribute('onclick') or ''
                    href = el.get_attribute('href') or ''
                    text = el.text.strip()
                    
                    if ('phone' in onclick.lower() or 'phone' in href.lower() or 
                        'show' in onclick.lower() or 'tel' in onclick.lower()):
                        reveal_elements.append({
                            'element': el,
                            'selector': selector,
                            'onclick': onclick,
                            'href': href,
                            'text': text
                        })
                        print(f"  📞 Found reveal element: {selector}")
                        print(f"     Text: '{text}'")
                        print(f"     onclick: '{onclick}'")
                        print(f"     href: '{href}'")
            except Exception as e:
                continue
        
        print(f"\\n🎯 Found {len(reveal_elements)} potential reveal elements")
        
        # Try clicking each reveal element
        for i, elem_info in enumerate(reveal_elements):
            print(f"\\n🔄 Trying reveal element {i+1}...")
            try:
                element = elem_info['element']
                
                # Scroll to element
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(1)
                
                # Try different click methods
                try:
                    # Method 1: Regular click
                    element.click()
                    print(f"  ✅ Regular click successful")
                except:
                    try:
                        # Method 2: JavaScript click
                        driver.execute_script("arguments[0].click();", element)
                        print(f"  ✅ JavaScript click successful")
                    except:
                        try:
                            # Method 3: Action chains
                            ActionChains(driver).click(element).perform()
                            print(f"  ✅ ActionChains click successful")
                        except:
                            print(f"  ❌ All click methods failed")
                            continue
                
                # Wait for phone reveal
                time.sleep(3)
                
                # Check if phone was revealed
                phone_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '+371') and not(contains(text(), '***'))]")
                for phone_elem in phone_elements:
                    text = phone_elem.text.strip()
                    if text and len(text) > 8 and '***' not in text:
                        print(f"  🎉 PHONE REVEALED: '{text}'")
                        return text
                        
            except Exception as e:
                print(f"  ❌ Error with element {i+1}: {e}")
        
        print("\\n❌ Phone reveal unsuccessful with standard methods")
        
        # Try manual JavaScript phone reveal
        print("\\n🔧 Trying manual phone reveal scripts...")
        manual_scripts = [
            # Try to find hidden phone data in page source
            "return document.documentElement.innerHTML;",
            # Look for phone in window variables
            "return Object.keys(window).filter(key => key.toLowerCase().includes('phone'));",
            # Check for SS.lv specific patterns
            "return document.querySelectorAll('*[onclick], *[data-*]').length;"
        ]
        
        for script in manual_scripts:
            try:
                result = driver.execute_script(script)
                if isinstance(result, str) and '+371' in result and result.count('*') < 3:
                    print(f"  📞 Found in source: contains phone data")
                elif isinstance(result, list):
                    print(f"  🔍 Window phone keys: {result}")
                else:
                    print(f"  ℹ️  Script result: {type(result)} with {result if isinstance(result, (int, str)) else 'complex data'}")
            except Exception as e:
                print(f"  ❌ Script failed: {e}")
        
        # Keep browser open for manual inspection
        print("\\n⏸️  Browser will stay open for 10 seconds for manual inspection...")
        time.sleep(10)
        
        driver.quit()
        print("\\n🏁 Test completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_phone_reveal_interaction()