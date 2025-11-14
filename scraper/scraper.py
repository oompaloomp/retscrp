import requests
import json
import datetime
import time

# Хедеры для имитации запроса из браузера
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_products_from_api(url, retailer_name, max_retries=3):
    """Универсальная функция для получения данных из API."""
    for attempt in range(max_retries):
        try:
            print(f"[{retailer_name}] Fetching from: {url}")
            response = requests.get(url, headers=HEADERS, timeout=20)
            print(f"[{retailer_name}] Status: {response.status_code}")
            response.raise_for_status() # Вызовет исключение для ошибок HTTP
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429: # Too Many Requests
                print(f"[{retailer_name}] Rate limited (429). Retrying in {5 * (attempt + 1)} seconds...")
                time.sleep(5 * (attempt + 1))
            else:
                print(f"[{retailer_name}] HTTP error {e} on attempt {attempt + 1}")
                break
        except requests.exceptions.RequestException as e:
            print(f"[{retailer_name}] Request error {e} on attempt {attempt + 1}")
            break
        except json.JSONDecodeError:
            print(f"[{retailer_name}] JSON Decode Error. Response: {response.text[:500]} on attempt {attempt + 1}")
            break
        except Exception as e:
            print(f"[{retailer_name}] Unexpected error: {e} on attempt {attempt + 1}")
            break
    return None

def scrape_pyaterochka():
    """Собирает широкий спектр товаров из Пятёрочки через их основной API каталога."""
    print("--- Scraping Пятёрочка (Main Catalog/Special Offers) ---")
    products = []
    # Этот endpoint обычно возвращает широкий каталог товаров, не только строго акционные.
    # Количество товаров на страницу можно увеличить для более быстрого сбора.
    base_url = "https://5ka.ru/api/v2/special_offers/"
    page = 1
    total_pages = 1 # Будет обновлено после первого запроса

    while page <= total_pages:
        url = f"{base_url}?page={page}&records_per_page=1000" # Запрашиваем 1000 записей за раз
        data = fetch_products_from_api(url, "Пятёрочка")
        
        if data:
            results = data.get('results', [])
            products.extend([
                {
                    'retailer': 'Пятёрочка',
                    'name': item.get('name', 'N/A'),
                    'price': float(item.get('current_price')) if item.get('current_price') is not None else None,
                    'old_price': float(item.get('old_price')) if item.get('old_price') is not None else None,
                    'discount_percent': item.get('promo', {}).get('value'),
                    'img_url': item.get('img_link'),
                    'category': item.get('group_name', 'Продукты'),
                    'unit_price': None # Дополнительное поле, если нужно
                } for item in results
            ])
            
            # Обновляем общее количество страниц из метаданных, если доступно
            if 'total_pages' in data and total_pages == 1: # Обновить только после первого запроса
                total_pages = data['total_pages']
                print(f"[{retailer_name}] Total pages: {total_pages}")

            print(f"[{retailer_name}] Scraped page {page}/{total_pages}. Total products collected: {len(products)}")
            page += 1
            time.sleep(1) # Небольшая задержка между страницами
        else:
            print(f"[{retailer_name}] No data received for page {page}.")
            break
    return products

def scrape_chizhik():
    """Собирает товары из Чижика, перебирая широкий список общих поисковых терминов."""
    print("\n--- Scraping Чижик (General Search Terms) ---")
    products = []
    # Расширенный список общих категорий/товаров для максимально широкого сбора
    # Используем более общие термины, которые, скорее всего, дадут много результатов.
    search_terms = [
        "молоко", "хлеб", "сыр", "масло", "курица", "говядина", "свинина", "рыба", 
        "овощи", "фрукты", "яйца", "крупы", "макароны", "сок", "вода", "чай", "кофе",
        "сладости", "печенье", "мороженое", "колбаса", "сосиски", "йогурт", "сметана",
        "творог", "кефир", "маргарин", "сахар", "соль", "мука", "рис", "гречка", 
        "картофель", "лук", "морковь", "яблоки", "бананы", "апельсины", "лимон",
        "шоколад", "конфеты", "чипсы", "сухарики", "пиво", "вино", "водка", "шампанское",
        "порошок", "мыло", "шампунь", "зубная паста", "щетка", "бумага", "салфетки",
        "корм для кошек", "корм для собак", "туалетная бумага", "жидкость для мытья посуды"
    ]
    
    city_id = "a309e4ce-2f36-4106-b1ca-53e0f48a6d95" # ID города Пермь

    for term in search_terms:
        print(f"[{retailer_name}] Searching for '{term}'...")
        url = f"https://app.chizhik.club/api/v1/catalog/unauthorized/products/?city_id={city_id}&term={term}"
        data = fetch_products_from_api(url, "Чижик")
        
        if data:
            results = data.get('products', [])
            products.extend([
                {
                    'retailer': 'Чижик',
                    'name': item.get('title', 'N/A'),
                    'price': float(item.get('price')) if item.get('price') is not None else None,
                    'old_price': float(item.get('old_price')) if item.get('old_price') is not None else None,
                    'discount_percent': round((1 - item['price'] / item['old_price']) * 100) if item.get('old_price') and item.get('price') else None,
                    'img_url': item.get('image', {}).get('src'),
                    'category': item.get('tags', [{}])[0].get('name', 'Продукты'),
                    'unit_price': None # Дополнительное поле
                } for item in results
            ])
            print(f"[{retailer_name}] Found {len(results)} items for '{term}'. Total products collected: {len(products)}")
        time.sleep(2) # Увеличенная задержка между запросами к Чижику, чтобы избежать блокировки
    return products

if __name__ == "__main__":
    all_products = []
    
    # Сбор данных
    pyaterochka_products = scrape_pyaterochka()
    chizhik_products = scrape_chizhik()

    all_products.extend(pyaterochka_products)
    all_products.extend(chizhik_products)
    
    # Удаляем дубликаты по названию и ритейлеру
    # Используем уникальный ключ из названия, ритейлера и цены для большей точности
    unique_products = {}
    for p in all_products:
        key = (p['name'].lower(), p['retailer'], p['price']) # lowercase для названия
        unique_products[key] = p
    
    output_data = {
        "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
        "products": list(unique_products.values())
    }
    
    # Убедимся, что директория docs существует
    import os
    os.makedirs('docs', exist_ok=True)

    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
        
    print(f"\nFinished. Total unique products found: {len(unique_products.values())}")
