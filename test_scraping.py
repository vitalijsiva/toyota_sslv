"""
Test script to verify Toyota scraping and filtering works correctly
WITHOUT using Telegram bot
"""
import sys
sys.path.insert(0, '.')
from toyota import scrape_listings, filter_benzina_toyotas

print('=' * 80)
print('TOYOTA LISTINGS TEST')
print('=' * 80)

print('\n1. Scraping all listings (this will take 1-2 minutes)...')
all_listings = scrape_listings()
print(f'   ✓ Scraped {len(all_listings)} total listings')

print('\n2. Filtering for petrol-only Toyotas...')
filtered = filter_benzina_toyotas(all_listings)
print(f'   ✓ Filtered to {len(filtered)} petrol listings')

print('\n3. Breakdown by category:')
hilux = [l for l in filtered if '/hilux/' in l['link'].lower()]
land_cruiser = [l for l in filtered if '/land-cruiser/' in l['link'].lower()]
defects = [l for l in filtered if l['is_defect']]
regular = [l for l in filtered if not l['is_defect'] and '/hilux/' not in l['link'].lower() and '/land-cruiser/' not in l['link'].lower()]

print(f'   - Hilux (all fuels): {len(hilux)}')
print(f'   - Land Cruiser (all fuels): {len(land_cruiser)}')
print(f'   - Defect/Crash (petrol only): {len(defects)}')
print(f'   - Regular Toyotas (petrol only): {len(regular)}')

print('\n4. Testing specific listings:')

# Test Yaris
yaris = [l for l in filtered if 'cbpndi' in l['link']]
print(f'   - Yaris (cbpndi): {"✓ FOUND" if yaris else "✗ NOT FOUND"}')

# Test Auris
auris = [l for l in filtered if 'kjobd' in l['link']]
print(f'   - Auris (kjobd): {"✓ FOUND" if auris else "✗ NOT FOUND"}')

# Test diesel Avensis (should NOT be in results)
diesel_avensis = [l for l in filtered if 'elmcp' in l['link']]
print(f'   - Diesel Avensis (elmcp): {"✗ FOUND (ERROR!)" if diesel_avensis else "✓ NOT FOUND (correct)"}')

print('\n5. Sample listings:')
for i, item in enumerate(filtered[:5], 1):
    print(f'\n   {i}. {item["title"][:60]}...')
    print(f'      Fuel: {item.get("fuel_type", "N/A")}')
    print(f'      Price: {item["price"]}')
    print(f'      Link: {item["link"]}')

print('\n' + '=' * 80)
print('TEST COMPLETE!')
print('=' * 80)
