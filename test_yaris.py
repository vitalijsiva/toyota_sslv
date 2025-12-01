import sys
sys.path.insert(0, '.')
from toyota import scrape_listings, filter_benzina_toyotas

print('Scraping listings...')
listings = scrape_listings()

# Find cbpndi listing
yaris = [l for l in listings if 'cbpndi' in l['link']]

if yaris:
    print('\n✓ Found in scraped data:')
    print(f"  ID: {yaris[0]['id']}")
    print(f"  Title: {yaris[0]['title']}")
    print(f"  Fuel type: {yaris[0].get('fuel_type', 'N/A')}")
    print(f"  Link: {yaris[0]['link']}")
else:
    print('\n✗ NOT found in scraped data')

# Check if filtered
filtered = filter_benzina_toyotas(listings)
yaris_filtered = [l for l in filtered if 'cbpndi' in l['link']]

print(f"\nIn filtered results: {'YES ✓' if yaris_filtered else 'NO ✗'}")
print(f"\nTotal scraped: {len(listings)}")
print(f"Total filtered: {len(filtered)}")
