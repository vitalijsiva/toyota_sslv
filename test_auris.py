import sys
sys.path.insert(0, '.')
from toyota import scrape_listings, filter_benzina_toyotas

print('Scraping listings...')
listings = scrape_listings()

# Find kjobd listing
auris = [l for l in listings if 'kjobd' in l['link']]

if auris:
    print('\n✓ Found in scraped data:')
    print(f"  ID: {auris[0]['id']}")
    print(f"  Title: {auris[0]['title']}")
    print(f"  Fuel type: {auris[0].get('fuel_type', 'N/A')}")
    print(f"  Link: {auris[0]['link']}")
else:
    print('\n✗ NOT found in scraped data')

# Check if filtered
filtered = filter_benzina_toyotas(listings)
auris_filtered = [l for l in filtered if 'kjobd' in l['link']]

print(f"\nIn filtered results: {'YES ✓' if auris_filtered else 'NO ✗'}")
print(f"\nTotal scraped: {len(listings)}")
print(f"Total filtered: {len(filtered)}")
