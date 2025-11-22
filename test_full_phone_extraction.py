#!/usr/bin/env python3

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_full_phone_extraction():
    """Test enhanced JavaScript phone extraction with full number reveal"""
    
    try:
        print("=== FULL PHONE NUMBER EXTRACTION TEST ===")
        print("Testing enhanced phone reveal to get complete digits...")
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        
        # Test URL - a real SS.lv Toyota listing
        test_url = 'https://www.ss.lv/msg/lv/transport/cars/toyota/corolla/ccnihn.html'
        
        print(f"Loading: {test_url}")
        driver.get(test_url)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        print("✅ Page loaded, searching for phone...")
        
        # First check what's initially visible
        initial_phone = driver.find_elements(By.XPATH, "//*[contains(text(), '+371') or contains(text(), '27') or contains(text(), '28') or contains(text(), '29')]")
        print(f"📱 Initial phone elements found: {len(initial_phone)}")
        
        for elem in initial_phone:
            text = elem.text.strip()
            if text:
                print(f"  📞 Initial: '{text}'")
                if '***' in text:
                    print(f"  ⚠️  Masked number detected - need to reveal full digits")
        
        # Enhanced phone reveal JavaScript
        print("\\n🔧 Executing enhanced phone reveal scripts...")
        
        js_commands = [
            # Standard SS.lv phone reveal functions
            "if(typeof showPhone === 'function') { console.log('Calling showPhone'); showPhone(); }",
            "if(typeof getPhone === 'function') { console.log('Calling getPhone'); getPhone(); }",
            "if(typeof show_phone === 'function') { console.log('Calling show_phone'); show_phone(); }",
            
            # Try to find and click phone reveal links/buttons
            "document.querySelectorAll('a[onclick*=\"phone\"], a[onclick*=\"tel\"], [onclick*=\"show\"]').forEach(el => { console.log('Clicking phone reveal:', el); el.click(); });",
            
            # Force show hidden phone elements
            "document.querySelectorAll('.phone_hidden, .tel_hidden, [style*=\"display: none\"]').forEach(el => {el.style.display = 'block'; el.style.visibility = 'visible';});",
            
            # Reveal data attributes
            "document.querySelectorAll('[data-phone], [data-tel], [data-number]').forEach(el => {if(el.dataset.phone) el.textContent = el.dataset.phone; if(el.dataset.tel) el.textContent = el.dataset.tel; if(el.dataset.number) el.textContent = el.dataset.number;});",
            
            # Force reveal asterisk-masked phones by triggering onclick handlers
            "document.querySelectorAll('*').forEach(el => {if(el.onclick && el.onclick.toString().includes('phone')) {try {console.log('Triggering onclick for phone reveal'); el.onclick();} catch(e) {console.log('onclick failed:', e);}}});",
            
            # Try specific SS.lv patterns
            "document.querySelectorAll('span, div, a').forEach(el => { if(el.textContent.includes('***') && (el.textContent.includes('+371') || el.textContent.match(/[0-9]/))) { console.log('Found masked phone, trying reveal:', el); if(el.onclick) el.onclick(); else if(el.click) el.click(); } });",
        ]
        
        for i, cmd in enumerate(js_commands):
            try:
                print(f"  🔄 Executing command {i+1}/{len(js_commands)}...")
                driver.execute_script(cmd)
                time.sleep(2)  # Longer wait for phone reveal
            except Exception as e:
                print(f"  ❌ Command {i+1} failed: {e}")
        
        # Wait for AJAX calls and phone reveals
        print("⏳ Waiting for phone reveal (5 seconds)...")
        time.sleep(5)
        
        # Look for full phone numbers (no ***)
        print("\\n🔍 Searching for revealed full phone numbers...")
        
        phone_xpath_patterns = [
            "//*[contains(text(), '+371') and not(contains(text(), '***'))]",
            "//*[contains(text(), '27') and string-length(text()) > 8 and not(contains(text(), '***'))]",
            "//*[contains(text(), '28') and string-length(text()) > 8 and not(contains(text(), '***'))]", 
            "//*[contains(text(), '29') and string-length(text()) > 8 and not(contains(text(), '***'))]",
            "//span[contains(@id, 'phone')]",
            "//div[contains(@id, 'phone')]",
            "//span[contains(@class, 'phone')]",
            "//a[contains(@href, 'tel:')]"
        ]
        
        full_phone_found = False
        best_phone = ""
        
        for i, pattern in enumerate(phone_xpath_patterns):
            try:
                elements = driver.find_elements(By.XPATH, pattern)
                print(f"  📋 Pattern {i+1}: {len(elements)} elements")
                
                for elem in elements:
                    text = elem.text.strip()
                    if (text and len(text) > 8 and 
                        '***' not in text and
                        ('+371' in text or any(text.startswith(prefix) for prefix in ['27', '28', '29', '67', '65']))):
                        
                        print(f"  ✅ FULL PHONE FOUND: '{text}'")
                        best_phone = text
                        full_phone_found = True
                        break
                
                if full_phone_found:
                    break
                    
            except Exception as e:
                print(f"  ❌ Pattern {i+1} failed: {e}")
        
        if full_phone_found:
            print(f"\\n🎯 SUCCESS! Complete phone number: {best_phone}")
            print(f"✅ Length: {len(best_phone)} characters")
            # Count digits
            digits = ''.join(c for c in best_phone if c.isdigit())
            print(f"✅ Digits: {len(digits)} total ({digits})")
        else:
            print("\\n❌ Full phone number not revealed")
            # Show what we did find
            all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '+371') or contains(text(), '27') or contains(text(), '28') or contains(text(), '29')]")
            print(f"\\n📱 All phone-like elements found: {len(all_elements)}")
            for elem in all_elements:
                text = elem.text.strip()
                if text:
                    status = "🔶 PARTIAL" if '***' in text else "✅ COMPLETE"
                    print(f"  {status}: '{text}'")
        
        driver.quit()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_phone_extraction()