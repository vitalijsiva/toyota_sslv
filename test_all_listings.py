"""
Test script to find and display all active Toyota listings
"""
import sys
sys.path.insert(0, '.')
from toyota import scrape_listings, filter_benzina_toyotas

print('Scraping all Toyota listings (this may take a while as it fetches detail pages)...\n')

# Scrape all listings
all_listings = scrape_listings()
print(f'Total listings scraped: {len(all_listings)}')

# Filter for petrol/hybrid
filtered_listings = filter_benzina_toyotas(all_listings)
print(f'Filtered listings (petrol/hybrid): {len(filtered_listings)}\n')

# Save all listings to file
with open('all_active_listings.txt', 'w', encoding='utf-8') as f:
    f.write(f'All Active Toyota Listings - Total: {len(all_listings)}\n')
    f.write('=' * 80 + '\n\n')
    
    for item in all_listings:
        f.write(f"ID: {item['id']}\n")
        f.write(f"Title: {item['title']}\n")
        f.write(f"Price: {item['price']}\n")
        f.write(f"Fuel: {item.get('fuel_type', 'N/A')}\n")
        f.write(f"Link: {item['link']}\n")
        f.write(f"Defect: {item['is_defect']}\n")
        f.write('-' * 80 + '\n')

print('✓ All listings saved to: all_active_listings.txt')

# Save filtered listings to file
with open('filtered_active_listings.txt', 'w', encoding='utf-8') as f:
    f.write(f'Filtered Toyota Listings (Petrol/Hybrid) - Total: {len(filtered_listings)}\n')
    f.write('=' * 80 + '\n\n')
    
    for item in filtered_listings:
        f.write(f"ID: {item['id']}\n")
        f.write(f"Title: {item['title']}\n")
        f.write(f"Price: {item['price']}\n")
        f.write(f"Fuel: {item.get('fuel_type', 'N/A')}\n")
        f.write(f"Link: {item['link']}\n")
        f.write(f"Defect: {item['is_defect']}\n")
        f.write('-' * 80 + '\n')

print('✓ Filtered listings saved to: filtered_active_listings.txt')

# Display summary by fuel type
print('\n' + '=' * 80)
print('FUEL TYPE SUMMARY:')
print('=' * 80)

fuel_types = {}
for item in all_listings:
    fuel = item.get('fuel_type', 'Unknown')
    if fuel:
        fuel_types[fuel] = fuel_types.get(fuel, 0) + 1
    else:
        fuel_types['Unknown'] = fuel_types.get('Unknown', 0) + 1

for fuel, count in sorted(fuel_types.items(), key=lambda x: x[1], reverse=True):
    print(f"{fuel}: {count}")

print('\n✓ Done!')
