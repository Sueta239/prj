import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

import pandas as pd
import json

def run_steps():
    df = pd.read_csv("data/Filtered_score.csv", sep=";", encoding="utf-8")

    # Преобразуем строковые поля обратно в словари/списки
    for col in ["score", "new_score", "top_1_score", "top_5_patents"]:
        df[col] = df[col].apply(json.loads)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Гистограмма
    axes[0, 0].hist(df['best_score'], bins=50, color='blue', edgecolor='black')
    axes[0, 0].set_title('Распределение best_score')
    axes[0, 0].set_xlabel('Значение best_score')
    axes[0, 0].set_ylabel('Частота')
    axes[0, 0].grid(True)

    # График плотности
    sns.kdeplot(df['best_score'], fill=True, color='blue', ax=axes[0, 1])
    axes[0, 1].set_title('График плотности best_score')
    axes[0, 1].set_xlabel('Значение best_score')
    axes[0, 1].set_ylabel('Плотность')
    axes[0, 1].grid(True)

    # Точечный график
    axes[1, 0].scatter(range(len(df['best_score'])), df['best_score'], alpha=0.5)
    axes[1, 0].set_title('Точечный график best_score')
    axes[1, 0].set_xlabel('Индекс строки')
    axes[1, 0].set_ylabel('Значение best_score')
    axes[1, 0].grid(True)

    # CDF
    x = np.sort(df['best_score'])
    y = np.arange(1, len(x) + 1) / len(x)
    axes[1, 1].plot(x, y, marker='.', linestyle='none')
    axes[1, 1].set_title('CDF для best_score')
    axes[1, 1].set_xlabel('Значение best_score')
    axes[1, 1].set_ylabel('Доля данных')
    axes[1, 1].grid(True)

    fig.canvas.manager.set_window_title("Статистика")
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    run_steps()