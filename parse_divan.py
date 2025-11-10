from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import csv
import time
import re

def parse_divan_prices():
    """
    Парсит цены на диваны с сайта divan.ru и сохраняет в CSV файл
    """
    # Настройка Chrome опций
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Запуск в фоновом режиме (без GUI)
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Инициализация драйвера
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        url = 'https://www.divan.ru/category/divany'
        print(f"Открываю страницу: {url}")
        driver.get(url)
        
        # Ждем загрузки страницы
        time.sleep(3)
        
        # Прокручиваем страницу для загрузки всех товаров
        print("Прокручиваю страницу для загрузки товаров...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_pause_time = 2
        
        # Прокручиваем несколько раз для загрузки большего количества товаров
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # Ждем загрузки контента
        time.sleep(2)
        
        # Находим все карточки товаров
        # Пробуем разные селекторы для карточек товаров
        products = []
        
        # Селектор для карточек товаров (может варьироваться в зависимости от структуры сайта)
        product_cards = driver.find_elements(By.CSS_SELECTOR, '[data-testid="product-card"], .product-card, .catalog-item, [class*="product"], [class*="item"]')
        
        if not product_cards:
            # Альтернативный поиск по классам
            product_cards = driver.find_elements(By.CSS_SELECTOR, 'div[class*="ProductCard"], div[class*="product-card"], article, [data-product-id]')
        
        print(f"Найдено карточек товаров: {len(product_cards)}")
        
        # Если карточек не найдено, пробуем найти по другому селектору
        if len(product_cards) == 0:
            # Ищем все элементы с ценами
            price_elements = driver.find_elements(By.CSS_SELECTOR, '[class*="price"], [class*="Price"], span[class*="rub"]')
            print(f"Найдено элементов с ценами: {len(price_elements)}")
            
            # Пробуем найти товары через родительские элементы
            product_cards = driver.find_elements(By.CSS_SELECTOR, 'div[class*="catalog"], div[class*="grid"], div[class*="list"] > div')
        
        # Извлекаем данные из каждой карточки
        for idx, card in enumerate(product_cards[:50]):  # Ограничиваем до 50 товаров для примера
            try:
                # Ищем название товара
                name = "Не указано"
                name_selectors = [
                    'h2', 'h3', '[class*="title"]', '[class*="name"]', 
                    'a[class*="title"]', 'span[class*="title"]', 
                    '[data-testid="product-title"]'
                ]
                
                for selector in name_selectors:
                    try:
                        name_elem = card.find_element(By.CSS_SELECTOR, selector)
                        name = name_elem.text.strip()
                        if name:
                            break
                    except:
                        continue
                
                # Ищем цену со скидкой (только текущую цену, не зачеркнутую)
                price = "Не указано"
                
                try:
                    # Сначала ищем специфичные элементы с ценами
                    price_elements = card.find_elements(By.CSS_SELECTOR, 
                        '*[class*="price"]:not([class*="old"]):not([class*="strike"]), '
                        '*[class*="Price"]:not([class*="old"]):not([class*="strike"]), '
                        '*[class*="cost"]:not([class*="old"]):not([class*="strike"]), '
                        'span[class*="rub"], div[class*="rub"]')
                    
                    # Если не нашли специфичные, ищем более широко
                    if not price_elements:
                        price_elements = card.find_elements(By.CSS_SELECTOR, 
                            'span, div, p')
                    
                    # Ограничиваем количество проверяемых элементов (первые 20)
                    price_elements = price_elements[:20]
                    
                    # Сортируем элементы по их позиции на странице (сверху вниз)
                    try:
                        price_elements.sort(key=lambda e: e.location['y'])
                    except:
                        pass
                    
                    for elem in price_elements:
                        try:
                            text = elem.text.strip()
                            if not text:
                                continue
                            
                            # Пропускаем элементы с процентами скидки
                            if '%' in text or 'скидк' in text.lower() or 'скидка' in text.lower():
                                continue
                            
                            # Проверяем, зачеркнут ли элемент через computed style
                            try:
                                is_strikethrough = driver.execute_script(
                                    "return window.getComputedStyle(arguments[0]).textDecorationLine.includes('line-through');", 
                                    elem
                                )
                                if is_strikethrough:
                                    continue
                            except:
                                pass
                            
                            # Проверяем inline style и классы
                            style = elem.get_attribute('style') or ''
                            class_attr = elem.get_attribute('class') or ''
                            if 'line-through' in style or 'strikethrough' in class_attr.lower():
                                continue
                            
                            # Ищем цену в формате "28 990" или "28990" (от 4 до 7 цифр)
                            # Ищем последовательность цифр с возможными пробелами
                            price_patterns = [
                                r'(\d{1,3}(?:\s+\d{3})+)\s*[Рр]',  # "28 990 Р"
                                r'(\d{4,7})\s*[Рр]',  # "28990 Р"
                                r'(\d{1,3}(?:\s+\d{3})+)',  # "28 990"
                                r'(\d{4,7})',  # "28990"
                            ]
                            
                            for pattern in price_patterns:
                                price_match = re.search(pattern, text.replace('\u00A0', ' '))
                                if price_match:
                                    price_text = price_match.group(1).replace(' ', '').replace('\u00A0', '')
                                    
                                    if price_text.isdigit():
                                        price_int = int(price_text)
                                        # Проверяем разумный диапазон цен (от 1000 до 10000000)
                                        if 1000 <= price_int <= 10000000:
                                            price = price_text
                                            break
                            
                            if price != "Не указано":
                                break
                                
                        except Exception as e:
                            continue
                
                except Exception as e:
                    pass
                
                # Если нашли цену, добавляем в список (название необязательно)
                if price != "Не указано":
                    products.append({
                        'Цена': price
                    })
                    name_display = name if name != "Не указано" else "Без названия"
                    print(f"Товар {len(products)}: {name_display[:50]}... - {price} руб.")
                
            except Exception as e:
                print(f"Ошибка при обработке карточки {idx}: {e}")
                continue
        
        # Если не нашли товары через карточки, пробуем другой подход
        if len(products) == 0:
            print("Пробую альтернативный метод парсинга...")
            # Ищем все ссылки на товары
            product_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/product/"], a[href*="/divan"]')
            
            for link in product_links[:30]:
                try:
                    name = link.text.strip()
                    if name and len(name) > 5:  # Фильтруем слишком короткие тексты
                        # Ищем цену рядом со ссылкой
                        parent = link.find_element(By.XPATH, './ancestor::*[contains(@class, "product") or contains(@class, "item")][1]')
                        price_elem = parent.find_elements(By.CSS_SELECTOR, '[class*="price"], span[class*="rub"]')
                        
                        price = "Не указано"
                        if price_elem:
                            price_text = price_elem[0].text.strip()
                            price_clean = ''.join(filter(str.isdigit, price_text.replace(' ', '')))
                            if price_clean:
                                price = price_clean
                        
                        if price != "Не указано":
                            products.append({
                                'Название': name,
                                'Цена': price
                            })
                except:
                    continue
        
        # Сохраняем данные в CSV
        if products:
            filename = 'divan_prices.csv'
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Цена']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for product in products:
                    writer.writerow(product)
            
            print(f"\nДанные успешно сохранены в файл {filename}")
            print(f"Всего найдено товаров: {len(products)}")
        else:
            print("Не удалось найти товары. Возможно, изменилась структура сайта.")
            print("Попробуйте запустить скрипт без headless режима для отладки.")
            
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()
        print("Браузер закрыт.")

if __name__ == "__main__":
    parse_divan_prices()

