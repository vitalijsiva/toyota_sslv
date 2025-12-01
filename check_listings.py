import sys
sys.path.insert(0, '.')
from toyota import scrape_listings, filter_benzina_toyotas
import json

listings = scrape_listings()
filtered = filter_benzina_toyotas(listings)

# Check for specific listings
rav4 = [l for l in filtered if 'bhphed' in l['link']]
corolla_verso = [l for l in filtered if 'cefpig' in l['link']]

print('RAV-4 (bhphed):', 'FOUND ✓' if rav4 else 'NOT FOUND ✗')
print('Corolla Verso (cefpig):', 'FOUND ✓' if corolla_verso else 'NOT FOUND ✗')

print('\nSearching in all scraped listings...')
all_rav4 = [l for l in listings if 'bhphed' in l['link']]
all_corolla = [l for l in listings if 'cefpig' in l['link']]

print('RAV-4 in scraped:', 'YES ✓' if all_rav4 else 'NO ✗')
print('Corolla Verso in scraped:', 'YES ✓' if all_corolla else 'NO ✗')

if all_rav4:
    print('\nRAV-4 details:')
    print(json.dumps(all_rav4[0], ensure_ascii=False, indent=2))
    
if all_corolla:
    print('\nCorolla Verso details:')
    print(json.dumps(all_corolla[0], ensure_ascii=False, indent=2))
