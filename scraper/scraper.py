import asyncio
import json
import time
from datetime import datetime
from pyaterochka_api import PyaterochkaAPI  # New library for 5ka
import requests
from bs4 import BeautifulSoup

# Headers for Chizhik (keep for HTML requests)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://5ka.ru/',  # Can reuse for consistency
}

CHIZHIK_SEARCH_TERMS = [
    'молоко', 'хлеб', 'сыр', 'масло', 'курица', 'яйцо', 'кофе', 'чай', 'сахар', 'соль',
    'мука', 'макароны', 'вода', 'сок', 'колбаса', 'сосиски', 'овощи', 'фрукты', 'шоколад', 'печенье',
    'йогурт', 'творог', 'рыба', 'мясо', 'крупы', 'консервы'
]

async def scrape_pyaterochka():
    products = []
    try:
        async with PyaterochkaAPI() as api:
            # Get store info for sap_code (required for catalog)
            store_info = await api.delivery_panel_store()
            sap_code = store_info.get('selectedStore', {}).get('sapCode')
            if not sap_code:
                print("Error: No sap_code from store info.")
                return products

            # Get catalog tree (categories)
            categories_data = await api.Catalog.tree(sap_code_store_id=sap_code)
            for category in categories_data:
                category_id = category.get('id')
                category_name = category.get('name')
                if not category_id:
                    continue

                # Get products list for category
                products_data = await api.Catalog.products_list(category_id=category_id, sap_code_store_id=sap_code)
                for item in products_data.get('products', []):
                    products.append({
                        'name': item.get('name'),
                        'price': item.get('current_price') or item.get('price_reg__min'),
                        'store': 'Пятёрочка',
                        'category': category_name
                    })
                await asyncio.sleep(1)  # Async delay

    except Exception as e:
        print(f"Error in Pyaterochka scrape: {e}")
    return products

def scrape_chizhik():  # Keep sync for simplicity, or make async if needed
    products = []
    base_url = "https://chizhik.club/search"
    for term in CHIZHIK_SEARCH_TERMS:
        print(f"Searching for '{term}' in Чижик...")
        params = {'query': term}
        try:
            response = requests.get(base_url, params=params, headers=HEADERS)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            product_cards = soup.find_all('div', class_='product-card')  # Adjust class if needed
            for card in product_cards:
                name = card.find('h3', class_='product-name').text.strip() if card.find('h3', class_='product-name') else 'N/A'
                price = card.find('span', class_='price').text.strip() if card.find('span', class_='price') else 'N/A'
                if name != 'N/A' and price != 'N/A':
                    products.append({
                        'name': name,
                        'price': price,
                        'store': 'Чижик',
                        'category': term
                    })
            time.sleep(1)
        except Exception as e:
            print(f"Error for term '{term}': {e}")
    return products

async def main():
    start_time = time.time()
    pyaterochka_products = await scrape_pyaterochka()
    chizhik_products = scrape_chizhik()  # Sync call
    all_products = pyaterochka_products + chizhik_products
    
    unique_products = {p['name']: p for p in all_products}.values()
    
    data = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "products": list(unique_products)
    }
    
    if data["products"]:
        with open('docs/data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Data saved with {len(data['products'])} products.")
    else:
        print("No products; not updating.")
    
    print(f"Finished in {time.time() - start_time:.2f} s.")
    print(f"Unique products: {len(unique_products)}")

if __name__ == "__main__":
    asyncio.run(main())
