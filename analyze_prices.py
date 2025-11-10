import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def analyze_divan_prices():
    """
    Обрабатывает данные из файла divan_prices.csv,
    вычисляет среднюю цену и строит гистограмму цен
    """
    # Читаем CSV файл
    filename = 'divan_prices.csv'
    
    try:
        # Читаем данные из CSV
        df = pd.read_csv(filename, encoding='utf-8')
        
        # Извлекаем цены (преобразуем в числовой формат)
        prices = pd.to_numeric(df['Цена'], errors='coerce')
        
        # Удаляем NaN значения (если есть некорректные данные)
        prices = prices.dropna()
        
        if len(prices) == 0:
            print("Ошибка: не найдено валидных цен в файле")
            return
        
        # Вычисляем среднюю цену
        mean_price = prices.mean()
        
        # Выводим статистику
        print("=" * 50)
        print("АНАЛИЗ ЦЕН НА ДИВАНЫ")
        print("=" * 50)
        print(f"Всего товаров: {len(prices)}")
        print(f"Средняя цена: {mean_price:.2f} руб.")
        print(f"Минимальная цена: {prices.min():.2f} руб.")
        print(f"Максимальная цена: {prices.max():.2f} руб.")
        print(f"Медианная цена: {prices.median():.2f} руб.")
        print(f"Стандартное отклонение: {prices.std():.2f} руб.")
        print("=" * 50)
        
        # Создаем гистограмму
        plt.figure(figsize=(12, 6))
        
        # Строим гистограмму
        n_bins = min(30, len(prices.unique()))  # Количество интервалов
        plt.hist(prices, bins=n_bins, edgecolor='black', alpha=0.7, color='steelblue')
        
        # Добавляем вертикальную линию для средней цены
        plt.axvline(mean_price, color='red', linestyle='--', linewidth=2, 
                   label=f'Средняя цена: {mean_price:.2f} руб.')
        
        # Настройка графика
        plt.title('Гистограмма цен на диваны', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Цена (руб.)', fontsize=12)
        plt.ylabel('Количество товаров', fontsize=12)
        plt.grid(True, alpha=0.3, axis='y')
        plt.legend(fontsize=10)
        
        # Форматируем ось X для лучшей читаемости
        plt.xticks(rotation=45, ha='right')
        
        # Улучшаем отображение
        plt.tight_layout()
        
        # Сохраняем график
        output_filename = 'divan_prices_histogram.png'
        plt.savefig(output_filename, dpi=300, bbox_inches='tight')
        print(f"\nГистограмма сохранена в файл: {output_filename}")
        
        # Показываем график
        plt.show()
        
    except FileNotFoundError:
        print(f"Ошибка: файл '{filename}' не найден")
        print("Убедитесь, что файл находится в той же директории, что и скрипт")
    except KeyError:
        print("Ошибка: в CSV файле отсутствует колонка 'Цена'")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_divan_prices()

