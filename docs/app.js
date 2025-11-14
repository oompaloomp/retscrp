document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const sortSelect = document.getElementById('sort-select');
    const resultsContainer = document.getElementById('results-container');
    const filtersContainer = document.getElementById('filters-container');
    const lastUpdatedSpan = document.getElementById('last-updated');

    let allProducts = [];

    // --- Инициализация ---
    async function init() {
        try {
            const response = await fetch('data.json');
            const data = await response.json();
            
            allProducts = data.products || [];
            lastUpdatedSpan.textContent = new Date(data.last_updated).toLocaleString();
            
            populateFilters();
            addEventListeners();
            applyFiltersAndSort();
        } catch (error) {
            resultsContainer.innerHTML = '<p>Не удалось загрузить данные. Файл data.json пуст или поврежден.</p>';
            console.error(error);
        }
    }

    // --- Рендеринг ---
    function renderProducts(products) {
        resultsContainer.innerHTML = '';
        if (products.length === 0) {
            resultsContainer.innerHTML = '<p>Товары не найдены.</p>';
            return;
        }

        products.forEach(product => {
            const card = document.createElement('div');
            card.className = 'product-card';

            const oldPriceHTML = product.old_price ? `<span class="old-price">${product.old_price} ₽</span>` : '';
            const discountHTML = product.discount_percent ? `<span class="discount">-${product.discount_percent}%</span>` : '';

            card.innerHTML = `
                <img src="${product.img_url}" alt="${product.name}" onerror="this.style.display='none'">
                <h3>${product.name}</h3>
                <p class="price">${product.price} ₽ ${oldPriceHTML}</p>
                <p>${discountHTML}</p>
                <p class="retailer">${product.retailer}</p>
            `;
            resultsContainer.appendChild(card);
        });
    }

    // --- Фильтры и сортировка ---
    function applyFiltersAndSort() {
        const searchTerm = searchInput.value.toLowerCase();
        const sortBy = sortSelect.value;
        
        const activeCategories = Array.from(filtersContainer.querySelectorAll('input:checked'))
                                      .map(input => input.value);

        let filtered = [...allProducts];

        // Поиск по названию
        if (searchTerm) {
            filtered = filtered.filter(p => p.name.toLowerCase().includes(searchTerm));
        }
        
        // Фильтр по категориям
        if (activeCategories.length > 0) {
            filtered = filtered.filter(p => activeCategories.includes(p.category));
        }

        // Сортировка
        switch (sortBy) {
            case 'price_asc':
                filtered.sort((a, b) => (a.price || Infinity) - (b.price || Infinity));
                break;
            case 'price_desc':
                filtered.sort((a, b) => (b.price || 0) - (a.price || 0));
                break;
            case 'discount_desc':
                filtered.sort((a, b) => (b.discount_percent || 0) - (a.discount_percent || 0));
                break;
        }

        renderProducts(filtered);
    }
    
    // --- Вспомогательные функции ---
    function populateFilters() {
        const categories = [...new Set(allProducts.map(p => p.category))].sort();
        filtersContainer.innerHTML = '';
        categories.forEach(category => {
            const label = document.createElement('label');
            label.className = 'filter-item';
            label.innerHTML = `<input type="checkbox" value="${category}"> ${category}`;
            label.querySelector('input').addEventListener('change', applyFiltersAndSort);
            filtersContainer.appendChild(label);
        });
    }

    function addEventListeners() {
        searchInput.addEventListener('input', applyFiltersAndSort);
        sortSelect.addEventListener('change', applyFiltersAndSort);
    }
    
    init();
});