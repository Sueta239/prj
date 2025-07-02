import pandas as pd
import requests
import json
from bs4 import BeautifulSoup
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

def run_steps():
    with open("config.json", "r", encoding="utf-8") as file:
            config = json.load(file)
            max_workers_ = config.get("max_workers")
            # print(max_workers_)

    def get_chemical_info(cas_number):
        url = f"https://www.chembk.com/en/chem/{cas_number}"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            name = ''
            synonyms = ''

            table = soup.find('table', class_='table')
            if table:
                for row in table.find_all('tr'):
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        key = cols[0].get_text(strip=True)
                        value = cols[1]
                        if key == 'Name':
                            name = value.get_text(strip=True)
                        elif key == 'Synonyms':
                            synonyms_raw = value.decode_contents()
                            parts = BeautifulSoup(synonyms_raw, 'html.parser').stripped_strings
                            synonyms = ", ".join(parts)

            return cas_number, name, synonyms
        except Exception as e:
            # print(f"Ошибка для {cas_number}: {e}")
            return cas_number, None, None

    df = pd.read_csv("data/CAS.csv", sep=";", encoding="utf-8", on_bad_lines='skip')
    unique_cas = df['CAS'].dropna().unique()
    results = []
    with ThreadPoolExecutor(max_workers=max_workers_) as executor:
        futures = {executor.submit(get_chemical_info, cas): cas for cas in unique_cas}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Обработка CAS-номеров"):
            results.append(future.result())

    result_df = pd.DataFrame(results, columns=['CAS', 'Name', 'Synonyms'])

    df = df.drop(columns=['Name', 'Synonyms'], errors='ignore')
    df = df.merge(result_df, on='CAS', how='left')
    df = df[~((df['Name'].isna() | (df['Name'] == '')) & (df['Synonyms'].isna() | (df['Synonyms'] == '')))]
    df.to_csv("data/Synonyms.csv", sep=";", encoding="utf-8", index=False)
    print("✔ Файл Synonyms.csv успешно сохранен!")

if __name__ == '__main__':
    run_steps()