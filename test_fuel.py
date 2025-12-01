import sys
sys.path.insert(0, '.')
from toyota import scrape_listings, filter_benzina_toyotas

print('Scraping listings (this will take a while as it fetches detail pages)...')
listings = scrape_listings()

# Find the Avensis listing
avensis = [l for l in listings if 'bjfxcd' in l['link']]
if avensis:
    print(f"\nAvensis listing found!")
    print(f"Title: {avensis[0]['title']}")
    print(f"Fuel type from detail page: {avensis[0].get('fuel_type', 'NOT FOUND')}")
else:
    print("\nAvensis listing NOT found in scraped data")

# Check if it passes filter
print("\nFiltering...")
filtered = filter_benzina_toyotas(listings)
avensis_filtered = [l for l in filtered if 'bjfxcd' in l['link']]
print(f"In filtered results: {'YES ✓' if avensis_filtered else 'NO ✗'}")

print(f"\nTotal scraped: {len(listings)}")
print(f"Total filtered: {len(filtered)}")
