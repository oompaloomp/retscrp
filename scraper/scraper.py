import requests
from bs4 import BeautifulSoup
import json
import datetime

# Хедеры для имитации запроса из браузера
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

SEARCH_TERM = "скумбрия"
all_products = []

def scrape_pyaterochka():
    print("Scraping Пятёрочка...")
    url = f"https://5ka.ru/api/v2/special_offers/?records_per_page=20&search={SEARCH_TERM}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json().get('results', [])
        
        for item in data:
            all_products.append({
                'retailer': 'Пятёрочка',
                'name': item.get('name', 'N/A'),
                'price': item.get('current_price'),
                'old_price': item.get('old_price'),
                'discount_percent': item.get('promo', {}).get('value'),
                'img_url': item.get('img_link'),
                'category': 'Продукты' # Категорию можно уточнить, если API её отдает
            })
    except Exception as e:
        print(f"Error scraping Пятёрочка: {e}")

def scrape_chizhik():
    print("Scraping Чижик...")
    # ID города Пермь. Для других городов нужно будет найти соответствующий ID.
    url = f"https://app.chizhik.club/api/v1/catalog/unauthorized/products/?city_id=a309e4ce-2f36-4106-b1ca-53e0f48a6d95&term={SEARCH_TERM}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json().get('products', [])
        
        for item in data:
            all_products.append({
                'retailer': 'Чижик',
                'name': item.get('title', 'N/A'),
                'price': item.get('price'),
                'old_price': item.get('old_price'),
                'discount_percent': round((1 - item['price'] / item['old_price']) * 100) if item.get('old_price') and item['price'] else None,
                'img_url': item.get('image', {}).get('src'),
                'category': 'Продукты'
            })
    except Exception as e:
        print(f"Error scraping Чижик: {e}")

if __name__ == "__main__":
    scrape_pyaterochka()
    scrape_chizhik()
    
    # Добавляем метаданные
    output_data = {
        "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
        "products": all_products
    }
    
    # Сохраняем результат в файл /docs/data.json
    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
        
    print(f"\nFinished. Total products found: {len(all_products)}")