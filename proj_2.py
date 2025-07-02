from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
import json
import re
import json
def run_steps():
    with open("config.json", "r", encoding="utf-8") as file:
            config = json.load(file)
            max_workers_ = config.get("max_workers")
            # print(max_workers_)

    def generate_queries(cas, name, synonyms):
        synonyms = synonyms[:5]
        with open("config.json", "r", encoding="utf-8") as file:
            config = json.load(file)
            first_part_terms = config.get("first_part_terms", [])
        second_part_terms = list(filter(None, [name] + synonyms))
        return [f"({first}) AND ({second})" for first in first_part_terms for second in second_part_terms]

    def generate_links(queries):
        """Генерирует ссылки на Google Patents по заданным поисковым запросам."""
        base_url = "https://patents.google.com/?q="
        return [f"{base_url}{query.replace(' ', '+')}&oq={query.replace(' ', '+')}" for query in queries]

    def scrape_single_url(url):
        from playwright.sync_api import sync_playwright
        import re

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=60000)
                page.wait_for_selector("h4.metadata.style-scope.search-result-item", timeout=10000)

                blocks = page.locator("h4.metadata.style-scope.search-result-item").all_text_contents()

                patent_regex = re.compile(r'\b[A-Z]{2}[0-9]{6,}[A-Z0-9]*\b')
                result = []
                for block in blocks:
                    found = patent_regex.findall(block)
                    if found:
                        result.append(found[0])
                browser.close()
                return result
        except Exception as e:
            # print(f"[!] Ошибка при скрапинге {url!r}: {e}")
            return []


    from concurrent.futures import ThreadPoolExecutor

    def process_urls(url_list, row_number):
        patents = []
        with ThreadPoolExecutor(max_workers=max_workers_) as executor:
            results = list(executor.map(scrape_single_url, url_list))
            for res in results:
                patents.extend(res)
        return patents



    def get_valid_first_word(sentence):
        """
        Возвращает первое слово, если оно состоит только из цифр и заглавных латинских букв.
        Иначе возвращает None.
        """
        words = sentence.split()
        if not words:
            return None

        first_word = words[0]
        if re.fullmatch(r"[A-Z0-9]+", first_word):
            return first_word
        else:
            return None
        
    def get_valid_first_word_for_list(list):
        ans = []
        for sentence in list:
            ans.append(get_valid_first_word(sentence))
        return ans

    def remove_duplicates_and_none(items):
        """
        Убирает из списка все дубликаты и None.
        """
        return list({item for item in items if item is not None})

    # //////////////////////
    df = pd.read_csv("data/Synonyms.csv", sep=";", encoding="utf-8", on_bad_lines='skip')
    df["Synonyms"] = df["Synonyms"].apply(lambda x: x.split(",") if isinstance(x, str) else [])
    df["query"] = df.apply(lambda row: generate_queries(row["CAS"], row["Name"], row["Synonyms"]), axis=1)
    df["url"] = df["query"].apply(generate_links)

    tqdm.pandas(desc="Выбираем патенты:")
    df["patents"] = df.progress_apply(lambda row: process_urls(row["url"], row.name + 1), axis=1)
    # df.to_csv("data/Patents_do.csv", sep=";", encoding="utf-8", index=False)
    df['patents'] = df['patents'].apply(get_valid_first_word_for_list)
    df['patents'] = df['patents'].apply(remove_duplicates_and_none)
    df.to_csv("data/Patents.csv", sep=";", encoding="utf-8", index=False)

    print("\n✔ Выбор патентов завершён")

if __name__ == '__main__':
    run_steps()