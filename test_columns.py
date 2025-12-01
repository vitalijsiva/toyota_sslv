import requests
from bs4 import BeautifulSoup

r = requests.get('https://www.ss.lv/lv/transport/cars/toyota/sell/')
soup = BeautifulSoup(r.content, 'html.parser')
rows = soup.select('tr[id^="tr_"]')

# Find the Corolla
target_rows = [row for row in rows if 'Labs nenodzīts auto ar mazu' in row.get_text()]

if target_rows:
    row = target_rows[0]
    print("All columns in this row:")
    print("="*60)
    
    all_tds = row.select('td')
    for i, td in enumerate(all_tds):
        text = td.get_text(strip=True)
        classes = td.get('class', [])
        print(f"Column {i}: {classes} => '{text[:80]}'")
