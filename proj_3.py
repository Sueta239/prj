import pandas as pd
import ast
import sys
import time
import random
import concurrent.futures
from tqdm import tqdm
from google_patent_scraper import scraper_class
from deep_translator import GoogleTranslator
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.error
import http.client
import json

def run_steps():
    with open("config.json", "r", encoding="utf-8") as file:
            config = json.load(file)
            max_workers_ = config.get("max_workers")
            # print(max_workers_)

    def safe_eval(x):
        """Безопасное преобразование строки в список"""
        try:
            return ast.literal_eval(x) if isinstance(x, str) and x.startswith("[") else []
        except (SyntaxError, ValueError):
            return []

    def get_patent_abstracts(patent_list, max_retries=5):
        """
        Получает аннотации для списка патентов с обработкой ошибок.
        """
        if not patent_list or not isinstance(patent_list, list):
            return {patent: "Ошибка получения аннотации" for patent in patent_list}

        scraper = scraper_class(return_abstract=True)

        for patent in patent_list:
            if patent:
                scraper.add_patents(patent)

        if not scraper.list_of_patents:
            return {patent: "Аннотация не найдена (пустой список)" for patent in patent_list}

        for attempt in range(max_retries):
            try:
                scraper.scrape_all_patents()
                return {
                    patent: scraper.parsed_patents.get(patent, {}).get("abstract_text", "Аннотация не найдена")
                    for patent in patent_list
                }
            except (urllib.error.HTTPError, urllib.error.URLError, http.client.IncompleteRead) as e:
                # print(f" Ошибка загрузки аннотаций (попытка {attempt+1}/{max_retries}): {e}")
                time.sleep(random.uniform(1, 3))  # Ожидание перед повтором
            except Exception as e:
                # print(f" Критическая ошибка получения аннотаций: {e}")
                return {patent: "Ошибка получения аннотации" for patent in patent_list}

        return {patent: "Ошибка после всех попыток" for patent in patent_list}

    def process_patents_dataframe(df, column_name="patents", max_workers=max_workers_):
        """
        Применяет get_patent_abstracts к каждому списку патентов с многопоточной обработкой.
        """
        def process_row(index_patents):
            index, patents = index_patents
            print(f"🔍 Обработка строки {index + 1} из {len(df)}...")
            if not isinstance(patents, list) or not patents:
                return {}
            return get_patent_abstracts(patents)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers_) as executor:
            try:
                results = list(tqdm(
                    executor.map(process_row, zip(df.index, df[column_name])),
                    total=len(df),
                    desc="Обработка патентов"
                ))
            except Exception as e:
                # print(f" Ошибка в многопоточном обработчике патентов: {e}")
                results = [{}] * len(df)  # Возвращаем пустые данные, чтобы продолжить работу

        df["abstracts"] = results
        return df

    def translate_text(text):
        """Перевод текста с обработкой ошибок"""
        try:
            if not text or text == "Аннотация не найдена":
                return text
            translated = GoogleTranslator(source="auto", target="en").translate(text)
            return translated if translated else text
        except Exception as e:
            # print(f" Ошибка перевода: {e}")
            return text

    def translate_abstracts(abstract_dict):
        """Перевод всех аннотаций с обработкой ошибок"""
        try:
            with ThreadPoolExecutor(max_workers=max_workers_) as executor:
                future_to_key = {executor.submit(translate_text, text): key for key, text in abstract_dict.items()}
                translated_dict = {}
                for future in as_completed(future_to_key):
                    key = future_to_key[future]
                    translated_dict[key] = future.result()
            return translated_dict
        except Exception as e:
            # print(f" Ошибка при переводе аннотаций: {e}")
            return abstract_dict


    # ////////////////////
    try:
        df = pd.read_csv("data/Patents.csv", sep=";", encoding="utf-8", on_bad_lines="skip")
        df["patents"] = df["patents"].apply(safe_eval)
        process_patents_dataframe(df)

        # output_file = "data/Abstract.csv"
        # df.to_csv(output_file, sep=";", encoding="utf-8", index=False)
        # print(f"\n✔ Обработка завершена! Данные сохранены в '{output_file}'.")

        tqdm.pandas(desc="Перевод аннотаций")
        df["abstracts"] = df["abstracts"].progress_apply(translate_abstracts)

        output_file = "data/Angl_Abstract.csv"
        df.to_csv(output_file, sep=";", encoding="utf-8", index=False)
        print(f"\n✔ Аннотации получены и переведены! Данные сохранены в '{output_file}'.")

    except Exception as e:
        print(f"\n Критическая ошибка обработки файла: {e}")
    # ////////////////////

if __name__ == '__main__':
    run_steps()