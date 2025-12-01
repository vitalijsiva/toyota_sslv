import sys
sys.path.insert(0, '.')
from toyota import scrape_listings, filter_benzina_toyotas
from datetime import datetime

print("Scraping all listings...")
listings = scrape_listings()
print(f"Total scraped: {len(listings)}")

print("\nFiltering...")
filtered = filter_benzina_toyotas(listings)
print(f"Filtered (will be sent): {len(filtered)}")

# Find what's NOT being sent
not_sent = [l for l in listings if l not in filtered]
print(f"\nNOT being sent: {len(not_sent)}")

# Write to file
filename = f"not_sent_listings_{datetime.now().strftime('%Y-%m-%d')}.txt"
with open(filename, 'w', encoding='utf-8') as f:
    f.write(f"NOT SENT LISTINGS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Total NOT being sent: {len(not_sent)}\n")
    f.write("="*80 + "\n\n")
    
    for i, item in enumerate(not_sent, 1):
        text = (item['title'] + ' ' + item['description']).lower()
        
        # Determine reason
        reasons = []
        if 'hybrid' in text or 'hibr' in text:
            reasons.append("HYBRID")
        if any(d in text for d in ['diesel', 'dīzeļ', 'd-4d', 'd4d']):
            reasons.append("DIESEL")
        if not reasons:
            reasons.append("NO FUEL TYPE DETECTED")
        
        f.write(f"{i}. {item['title']}\n")
        f.write(f"   Price: {item['price']}\n")
        f.write(f"   Link: {item['link']}\n")
        f.write(f"   Reason: {', '.join(reasons)}\n")
        f.write(f"   Defect: {item['is_defect']}\n")
        f.write("-"*80 + "\n\n")
    
    # Summary
    hybrid_count = sum(1 for l in not_sent if 'hybrid' in (l['title'] + ' ' + l['description']).lower() or 'hibr' in (l['title'] + ' ' + l['description']).lower())
    diesel_count = sum(1 for l in not_sent if any(d in (l['title'] + ' ' + l['description']).lower() for d in ['diesel', 'dīzeļ', 'd-4d', 'd4d']))
    unknown_count = len(not_sent) - hybrid_count - diesel_count
    
    f.write("\n" + "="*80 + "\n")
    f.write("SUMMARY\n")
    f.write("="*80 + "\n")
    f.write(f"Hybrid excluded: {hybrid_count}\n")
    f.write(f"Diesel excluded: {diesel_count}\n")
    f.write(f"Unknown/No fuel type: {unknown_count}\n")
    f.write(f"TOTAL NOT SENT: {len(not_sent)}\n")

print(f"\n✅ Saved to: {filename}")
print(f"\nSummary:")
print(f"  Hybrids: {hybrid_count}")
print(f"  Diesels: {diesel_count}")
print(f"  Unknown: {unknown_count}")
print(f"  TOTAL: {len(not_sent)}")
