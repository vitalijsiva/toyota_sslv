import sys
sys.path.insert(0, '.')
from toyota import scrape_listings, filter_benzina_toyotas

print("Scraping all listings...")
listings = scrape_listings()
print(f"Total scraped: {len(listings)}")

print("\nFiltering...")
filtered = filter_benzina_toyotas(listings)
print(f"Filtered (will be sent): {len(filtered)}")

# Find what's NOT being sent
not_sent = [l for l in listings if l not in filtered]
print(f"\nNOT being sent: {len(not_sent)}")

print("\n" + "="*80)
print("LISTINGS NOT BEING SENT (first 20):")
print("="*80)

for i, item in enumerate(not_sent[:20], 1):
    title = item['title'][:80]
    link = item['link']
    text = (item['title'] + ' ' + item['description']).lower()
    
    # Check why it's excluded
    reasons = []
    if 'hybrid' in text or 'hibr' in text:
        reasons.append("HYBRID")
    if any(d in text for d in ['diesel', 'dīzeļ', 'd-4d', 'd4d']):
        reasons.append("DIESEL")
    if not any(r in reasons for r in ['HYBRID', 'DIESEL']):
        reasons.append("NO FUEL TYPE DETECTED")
    
    print(f"\n{i}. {title}")
    print(f"   Link: {link}")
    print(f"   Reason: {', '.join(reasons)}")
    print(f"   Defect: {item['is_defect']}")

print("\n" + "="*80)
print("SUMMARY BY REASON:")
print("="*80)

hybrid_count = sum(1 for l in not_sent if 'hybrid' in (l['title'] + ' ' + l['description']).lower() or 'hibr' in (l['title'] + ' ' + l['description']).lower())
diesel_count = sum(1 for l in not_sent if any(d in (l['title'] + ' ' + l['description']).lower() for d in ['diesel', 'dīzeļ', 'd-4d', 'd4d']))
unknown_count = len(not_sent) - hybrid_count - diesel_count

print(f"Hybrid excluded: {hybrid_count}")
print(f"Diesel excluded: {diesel_count}")
print(f"Unknown/No fuel type: {unknown_count}")
