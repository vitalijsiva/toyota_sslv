#!/usr/bin/env python3

# Test the complete phone extraction system
import sys
import os
sys.path.append('.')

# Import the bot's extract_phone_with_js function
from toyota_bot_fixed import extract_phone_with_js

def test_complete_phone_system():
    """Test the complete phone extraction system"""
    
    print("=== COMPLETE PHONE EXTRACTION TEST ===")
    print("Testing bot's actual phone extraction function...")
    
    # Test URL
    test_url = 'https://www.ss.lv/msg/lv/transport/cars/toyota/corolla/ccnihn.html'
    test_id = 'test_listing_123'
    
    print(f"Testing: {test_url}")
    
    try:
        # Use the actual bot function
        result = extract_phone_with_js(test_url, test_id)
        
        print(f"✅ Extraction completed!")
        print(f"📱 Result: '{result}'")
        
        # Test phone formatting as bot would do it
        phone = result
        if phone == 'N/A' or not phone:
            phone_display = '❓ Nav norādīts'
        elif phone in ['Pieejams sarakstē', 'Noklikšķiniet, lai redzētu', 'Skatīt sludinājumā']:
            phone_display = f'📱 {phone}'
        elif phone.startswith('📞 Pieejams ('):
            phone_display = phone  # Already has emoji
        elif '+371' in phone and '***' not in phone and any(c.isdigit() for c in phone):
            clean_phone = phone.strip().replace('Parādīt tālruni', '').strip()
            phone_display = f'📞 `{clean_phone}`'
        elif '+371' in phone and '***' in phone:
            phone_display = f'🔒 {phone} (CAPTCHA)'
        else:
            phone_display = f'📱 {phone}'
            
        print(f"🎯 Bot display: {phone_display}")
        
        # Simulate how it would appear in notification
        print("\\n📧 Example notification:")
        print("🆕 NEW LISTING!")
        print()
        print("🚗 Toyota Corolla, Hibrīds 2023")
        print("💰 €19,450")
        print(f"{phone_display}")
        print("🔗 [Skatīt sludinājumu](https://www.ss.lv/...)")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_phone_system()