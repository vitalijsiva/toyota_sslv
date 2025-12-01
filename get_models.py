import requests
from bs4 import BeautifulSoup

# Fetch main Toyota page
r = requests.get('https://www.ss.lv/lv/transport/cars/toyota/')
soup = BeautifulSoup(r.content, 'html.parser')

# Find all model links
model_links = []
for a in soup.select('a'):
    href = a.get('href', '')
    if '/toyota/' in href and href.endswith('/'):
        # Extract model name
        parts = [p for p in href.split('/') if p]
        if 'toyota' in parts:
            idx = parts.index('toyota')
            if idx + 1 < len(parts):
                model = parts[idx + 1]
                full_url = f'https://www.ss.lv/lv/transport/cars/toyota/{model}/sell/'
                if full_url not in model_links:
                    model_links.append(full_url)

model_links.sort()
print("All Toyota model URLs:")
print("=" * 60)
for url in model_links:
    print(url)
    
print(f"\nTotal models: {len(model_links)}")
