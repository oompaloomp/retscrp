import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime

# Headers to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://5ka.ru/',
}

# Categories for Pyaterochka (from your original code, assuming IDs are correct)
PYATEROCHKA_CATEGORIES = {
    'Молоко, сыр, яйца': 43,
    'Мясо, птица, колбаса': 34,
    'Овощи, фрукты, грибы': 38,
    'Хлеб, выпечка': 44,
    # Add more categories if needed, e.g., 'Напитки': 35, etc. Check site for IDs
}

# Search terms for Chizhik (expanded for better coverage)
CHIZHIK_SEARCH_TERMS = [
    'молоко', 'хлеб', 'сыр', 'масло', 'курица', 'яйцо', 'кофе', 'чай', 'сахар', 'соль',
    'мука', 'макароны', 'вода', 'сок', 'колбаса', 'сосиски', 'овощи', 'фрукты', 'шоколад', 'печенье',
    # Added more: 'йогурт', 'творог', 'рыба', 'мясо', 'крупы', 'консервы'
    'йогурт', 'творог', 'рыба', 'мясо', 'крупы', 'консервы'
]

def scrape_pyaterochka():
    products = []
    base_url = "https://5ka.ru/api/v2/products/"
    for category_name, category_id in PYATEROCHKA_CATEGORIES.items():
        print(f"Scraping category: {category_name}...")
        page = 1
        while True:
            params = {
                'records_per_page': 100,
                'page': page,
                'categories': category_id
            }
            try:
                response = requests.get(base_url, params=params, headers=HEADERS)
                response.raise_for_status()  # Raise error for bad status
                data = response.json()
                if not data.get('results'):
                    break
                for item in data['results']:
                    products.append({
                        'name': item.get('name'),
                        'price': item.get('current_prices', {}).get('price_reg__min'),
                        'store': 'Пятёрочка',
                        'category': category_name
                    })
                page += 1
                time.sleep(1)  # Delay to avoid rate limiting
            except requests.exceptions.HTTPError as e:
                print(f"HTTP error in category '{category_name}': {e}")
                print(f"Response: {response.text[:500]}")  # Log partial response
                break
            except Exception as e:
                print(f"Unexpected error in category '{category_name}': {e}")
                break
    return products

def scrape_chizhik():
    products = []
    base_url = "https://chizhik.club/search"
    for term in CHIZHIK_SEARCH_TERMS:
        print(f"Searching for '{term}' in Чижик...")
        params = {'query': term}
        try:
            response = requests.get(base_url, params=params, headers=HEADERS)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            # Assuming product cards have class 'product-card' or similar; adjust based on site inspection
            product_cards = soup.find_all('div', class_='product-card')  # Check dev tools for exact class
            for card in product_cards:
                name = card.find('h3', class_='product-name').text.strip() if card.find('h3', class_='product-name') else 'N/A'
                price = card.find('span', class_='price').text.strip() if card.find('span', class_='price') else 'N/A'
                products.append({
                    'name': name,
                    'price': price,
                    'store': 'Чижик',
                    'category': term  # Use search term as proxy for category
                })
            time.sleep(1)
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error for term '{term}': {e}")
            print(f"Response: {response.text[:500]}")
        except Exception as e:
            print(f"Unexpected error for term '{term}': {e}")
    return products

if __name__ == "__main__":
    start_time = time.time()
    pyaterochka_products = scrape_pyaterochka()
    chizhik_products = scrape_chizhik()
    all_products = pyaterochka_products + chizhik_products
    
    # Remove duplicates by name (simple dedup)
    unique_products = {p['name']: p for p in all_products}.values()
    
    data = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "products": list(unique_products)
    }
    
    # Only write if there are products
    if data["products"]:
        with open('docs/data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Data saved to docs/data.json with {len(data['products'])} products.")
    else:
        print("No products found; not updating data.json.")
    
    print(f"Finished in {time.time() - start_time:.2f} seconds.")
    print(f"Total unique products found: {len(unique_products)}")
