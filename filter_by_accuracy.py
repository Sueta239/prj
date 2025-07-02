import pandas as pd
import json
import sys

def run_steps():
    threshold = float(sys.argv[1]) if len(sys.argv) > 1 else 0.40
    df = pd.read_csv("data/Best_score.csv", sep=";", encoding="utf-8")
    df["best_score"] = pd.to_numeric(df["best_score"], errors="coerce")
    filtered_df = df[df["best_score"] >= threshold]


    filtered_df.to_csv("data/Filtered_score.csv", sep=";", encoding="utf-8", index=False)
    print(f"\n✔ Отфильтровано по порогу {threshold:.2f} — осталось {len(filtered_df)} записей.")

    final = filtered_df[["Наименование продукции", "top_5_patents"]]
    final.to_csv("data/Final.csv", sep=";", encoding="utf-8", index=False)
    
if __name__ == '__main__':
    run_steps()