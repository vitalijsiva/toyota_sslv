#!/usr/bin/env python3

# Test to show what phone numbers look like in actual messages
sample_listings = [
    {
        'title': 'Toyota Corolla, Hibrīds 2023',
        'price': '€25,000',
        'phone': 'Pieejams sarakstē',
        'link': 'https://www.ss.lv/msg/lv/transport/cars/toyota/corolla/acnoi.html',
        'description': '1.8L Hybrid, automātisks',
        'car_make': 'Toyota',
        'car_model': 'Corolla', 
        'car_year': '2023',
        'condition_pct': ''
    },
    {
        'title': 'Toyota Land Cruiser 2020',
        'price': '€45,000', 
        'phone': '+371 27123456',
        'link': 'https://www.ss.lv/msg/lv/transport/cars/toyota/land-cruiser/xyz123.html',
        'description': '3.0D V6, pilnpiedziņa',
        'car_make': 'Toyota',
        'car_model': 'Land Cruiser',
        'car_year': '2020', 
        'condition_pct': ''
    },
    {
        'title': 'Toyota Hilux pēc avārijas',
        'price': '€8,000',
        'phone': 'Skatīt sludinājumā', 
        'link': 'https://www.ss.lv/msg/lv/transport/cars/toyota/hilux/crash123.html',
        'description': 'Bojāts priekšā, remontējams',
        'car_make': 'Toyota',
        'car_model': 'Hilux',
        'car_year': '2018',
        'condition_pct': '75%'
    }
]

def show_message_format():
    """Show how phone numbers appear in actual bot messages"""
    
    print("=== TOYOTA BOT MESSAGE EXAMPLES ===\n")
    
    for i, listing in enumerate(sample_listings, 1):
        title = listing['title']
        price = listing['price'] 
        phone = listing['phone']
        link = listing['link']
        
        # Format phone display (same logic as bot)
        if phone == 'N/A':
            phone_display = '❓ Nav norādīts'
        elif phone in ['Pieejams sarakstē', 'Noklikšķiniet, lai redzētu', 'Skatīt sludinājumā']:
            phone_display = f'📱 {phone}'
        else:
            phone_display = f'📞 {phone}'
        
        # Show message as bot would send it
        print(f"{i}. *{title}*")
        print(f"💰 Cena: `{price}`")
        print(f"{phone_display}")
        print(f"🔗 [Skatīt sludinājumu]({link})")
        print()
    
    print("=== PHONE DISPLAY EXPLANATION ===")
    print("📞 +371 XXXXXXXX  = Actual phone number found")
    print("📱 Pieejams sarakstē = Phone available through SS.lv messaging")
    print("📱 Skatīt sludinājumā = Check the full listing for phone")  
    print("❓ Nav norādīts = No phone information found")

if __name__ == "__main__":
    show_message_format()