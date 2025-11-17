import json
import time
import datetime
import requests
from bs4 import BeautifulSoup

DATA_FILE = "docs/data.json"
LOG_FILE = "scraper.log"

# ---------------------------
# ЛОГГЕР
# ---------------------------
def log(msg: str):
    timestamp = datetime.datetime.utcnow().isoformat()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {msg}\n")
    print(msg)


# ---------------------------
# ЗАГОЛОВКИ ДЛЯ ОБХОДА 403
# ---------------------------
HEADERS_5KA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://5ka.ru/",
    "Origin": "https://5ka.ru",
}

# Чижик без API — парсим HTML через их сайт
HEADERS_CHIZHIK = {
    "User-Agent": "Mozilla/5.0",
}


# ---------------------------
# ОБНОВЛЕНИЕ JSON
# ---------------------------
def save_data(products: list):
    data = {
        "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
        "products": products,
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ======================================================
#                 ПЯТЁРОЧКА
# ======================================================
def scrape_5ka():
    log("--- Scraping Пятёрочка ---")

    categories = {
        "Молоко, сыр, яйца": 43,
        "Мясо и колбасы": 34,
        "Овощи, фрукты": 38,
        "Хлеб": 44,
    }

    products = []

    session = requests.Session()

    for title, cid in categories.items():
        log(f"Пятёрочка: категория '{title}'...")

        url = (
            "https://5ka.ru/api/v2/products/"
            f"?records_per_page=100&page=1&categories={cid}"
        )

        try:
            r = session.get(url, headers=HEADERS_5KA, timeout=10)
            if r.status_code == 403:
                log(f"❌ 403 Forbidden — Пятёрочка блокирует доступ")
                continue

            r.raise_for_status()

            data = r.json()

            if "results" in data:
                for item in data["results"]:
                    products.append({
                        "title": item.get("name", ""),
                        "price": item.get("current_prices", {}).get("price_reg__min", ""),
                        "store": "Пятёрочка",
                    })

        except Exception as e:
            log(f"Ошибка категории '{title}': {e}")

    return products


# ======================================================
#                     ЧИЖИК
# ======================================================
def scrape_chizhik():
    log("--- Scraping Чижик ---")

    search_terms = [
        "молоко", "хлеб", "сыр", "масло", "курица", "яйцо",
        "кофе", "чай", "сахар", "соль", "мука", "макароны",
        "вода", "сок", "колбаса", "сосиски", "овощи", "фрукты"
    ]

    products = []
    session = requests.Session()

    for term in search_terms:
        log(f"Чижик: поиск '{term}'...")

        try:
            url = f"https://chizhik.club/catalogsearch/result/?q={term}"
            r = session.get(url, headers=HEADERS_CHIZHIK, timeout=10)

            if r.status_code != 200:
                log(f"Ошибка {r.status_code} при поиске '{term}'")
                continue

            soup = BeautifulSoup(r.text, "html.parser")

            items = soup.select(".product-item")

            for item in items:
                name = item.select_one(".product-item__name")
                price = item.select_one(".price__main-value")

                if not name:
                    continue

                products.append({
                    "title": name.text.strip(),
                    "price": price.text.strip() if price else "",
                    "store": "Чижик",
                })

        except Exception as e:
            log(f"Чижик ошибка '{term}': {e}")

    return products


# ======================================================
#                 МЕРЖ ТОВАРОВ
# ======================================================
def merge_products(list_a, list_b):
    combined = {}

    for item in list_a + list_b:
        key = item["title"].lower()
        if key not in combined:
            combined[key] = item

    return list(combined.values())


# ======================================================
#                    MAIN
# ======================================================
def main():
    start = time.time()
    log("=== START SCRAPER ===")

    p1 = scrape_5ka()
    p2 = scrape_chizhik()

    merged = merge_products(p1, p2)

    log(f"Всего товаров: {len(merged)}")

    save_data(merged)

    log(f"Готово за {round(time.time() - start, 2)} сек")
    log("=== END ===")


if __name__ == "__main__":
    main()
