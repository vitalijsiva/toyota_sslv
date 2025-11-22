"""
Test JavaScript phone extraction for Toyota bot
"""

from toyota_bot_fixed import extract_phone_with_js, SELENIUM_AVAILABLE

def test_phone_extraction():
    """Test phone extraction with a real SS.lv listing"""
    
    print("=== JAVASCRIPT PHONE EXTRACTION TEST ===")
    print(f"Selenium available: {SELENIUM_AVAILABLE}")
    
    if not SELENIUM_AVAILABLE:
        print("❌ Selenium not available - install selenium and chromedriver")
        return
    
    # Test with a real listing URL
    test_url = "https://www.ss.lv/msg/lv/transport/cars/toyota/corolla/ccnihn.html"
    test_id = "test_listing"
    
    print(f"Testing phone extraction from: {test_url}")
    
    try:
        phone = extract_phone_with_js(test_url, test_id)
        print(f"✅ Phone extracted: {phone}")
        
        if phone and phone not in ['Nav atrasts', 'Skatīt sludinājumā']:
            print("🎯 SUCCESS: Real phone number found!")
        else:
            print("ℹ️ No phone found, but extraction worked")
            
    except Exception as e:
        print(f"❌ Error during phone extraction: {e}")

if __name__ == "__main__":
    test_phone_extraction()