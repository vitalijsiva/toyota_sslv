import requests
from bs4 import BeautifulSoup

# Fetch the page
r = requests.get('https://www.ss.lv/lv/transport/cars/toyota/sell/')
soup = BeautifulSoup(r.content, 'html.parser')
rows = soup.select('tr[id^="tr_"]')

# Find the specific Corolla
target_rows = [row for row in rows if 'Labs nenodzīts auto ar mazu' in row.get_text()]

if target_rows:
    row = target_rows[0]
    
    # Extract description as the bot does
    details_elements = row.select('td.msga2')
    description = ' '.join([el.get_text(strip=True) for el in details_elements])
    
    # Get title
    title_element = row.select_one('td.msg2 a.am, td.msga2 a.am')
    title = title_element.get_text(strip=True) if title_element else 'N/A'
    
    print(f"Title: {title}")
    print(f"\nDescription: {description}")
    
    # Test filter
    combined_text = (title + description).lower()
    petrol_keywords = ['benzīn', 'benz.', 'petrol', 'gas']
    
    print(f"\nCombined text (lowercase): {combined_text}")
    print(f"\nPetrol keywords: {petrol_keywords}")
    print(f"\nMatches found:")
    for kw in petrol_keywords:
        if kw in combined_text:
            print(f"  ✓ '{kw}' found in text")
    
    has_petrol = any(kw in combined_text for kw in petrol_keywords)
    print(f"\n==> Should pass filter: {has_petrol}")
else:
    print("Listing not found on first page!")
