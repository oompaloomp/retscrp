import requests
import json
import datetime
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def scrape_pyaterochka():
    """Обходит основные категории Пятёрочки и собирает товары с первых страниц."""
    print("--- Scraping Пятёрочка (by categories) ---")
    products = []
    # Список ID основных категорий (их можно найти, анализируя запросы сайта)
    categories = {
        "Молоко, сыр, яйца": 43,
        "Мясо, птица, колбаса": 34,
        "Овощи, фрукты, грибы": 38,
        "Хлеб, выпечка": 44
    }

    for cat_name, cat_id in categories.items():
        print(f"Scraping category: {cat_name}...")
        url = f"https://5ka.ru/api/v2/products/?records_per_page=100&page=1&categories={cat_id}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            response.raise_for_status()
            data = response.json().get('results', [])
            
            for item in data:
                products.append({
                    'retailer': 'Пятёрочка',
                    'name': item.get('name', 'N/A'),
                    'price': item.get('current_price'),
                    'old_price': item.get('old_price'),
                    'discount_percent': item.get('promo', {}).get('value'),
                    'img_url': item.get('img_link'),
                    'category': cat_name
                })
            time.sleep(2) # Задержка, чтобы не забанили
        except Exception as e:
            print(f"Error in category '{cat_name}': {e}")
    return products

def scrape_chizhik():
    """Собирает товары из Чижика по нескольким популярным поисковым запросам, так как у него нет API категорий."""
    print("\n--- Scraping Чижик (expanding search) ---")
    products = []
    # Максимально расширяем список поисковых запросов для покрытия основных товаров
    search_terms = [
        "молоко", "хлеб", "сыр", "масло", "курица", "яйцо", "кофе", "чай",
        "сахар", "соль", "мука", "макароны", "вода", "сок", "колбаса", "сосиски",
        "овощи", "фрукты", "шоколад", "печенье"
    ]
    
    for term in search_terms:
        print(f"Searching for '{term}' in Чижик...")
        url = f"https://app.chizhik.club/api/v1/catalog/unauthorized/products/?city_id=a309e4ce-2f36-4106-b1ca-53e0f48a6d95&term={term}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            data = response.json().get('products', [])
            
            for item in data:
                products.append({
                    'retailer': 'Чижик',
                    'name': item.get('title', 'N/A'),
                    'price': item.get('price'),
                    'old_price': item.get('old_price'),
                    'discount_percent': round((1 - item['price'] / item['old_price']) * 100) if item.get('old_price') and item.get('price') else None,
                    'img_url': item.get('image', {}).get('src'),
                    'category': item.get('tags', [{}])[0].get('name', 'Продукты')
                })
            time.sleep(2) # Обязательная задержка!
        except Exception as e:
            print(f"An unexpected error occurred with Чижик for term '{term}': {e}")
    return products

if __name__ == "__main__":
    start_time = time.time()
    all_products = []
    all_products.extend(scrape_pyaterochka())
    all_products.extend(scrape_chizhik())
    
    # Удаляем дубликаты, оставляя только уникальные товары
    unique_products = list({ (p['name'], p['retailer']): p for p in all_products }.values())
    
    output_data = {
        "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
        "products": unique_products
    }
    
    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    
    end_time = time.time()
    print(f"\nFinished in {end_time - start_time:.2f} seconds.")
    print(f"Total unique products found: {len(unique_products)}")
