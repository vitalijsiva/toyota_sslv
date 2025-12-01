import sys
sys.path.insert(0, '.')
from toyota import scrape_listings, filter_benzina_toyotas

print('Scraping listings...')
listings = scrape_listings()

# Find elmcp listing
avensis = [l for l in listings if 'elmcp' in l['link']]

if avensis:
    print('\n✓ Found in scraped data:')
    print(f"  ID: {avensis[0]['id']}")
    print(f"  Title: {avensis[0]['title']}")
    print(f"  Fuel type: {avensis[0].get('fuel_type', 'N/A')}")
    print(f"  Link: {avensis[0]['link']}")
else:
    print('\n✗ NOT found in scraped data')

# Check if filtered
filtered = filter_benzina_toyotas(listings)
avensis_filtered = [l for l in filtered if 'elmcp' in l['link']]

print(f"\nIn filtered results: {'YES ✓' if avensis_filtered else 'NO ✗'}")
print(f"\nTotal scraped: {len(listings)}")
print(f"Total filtered: {len(filtered)}")
