import pandas as pd
import ast
import torch
import json
from tqdm import tqdm
from sentence_transformers import SentenceTransformer, util
from itertools import chain

def run_steps():
    def string_to_list(s: str):
        return [item.strip() for item in s.split(",") if item.strip()]

    def string_to_dict(s: str):
        try:
            return ast.literal_eval(s)
        except (SyntaxError, ValueError):
            return {}

    def generate_synthesis_phrases(query):
        return [
            f"The present invention generally relates to {query} and methods of making {query}.",
            f"More specifically, the present invention relates to a method for producing {query}.",
            f"A process for synthesizing {query} is described.",
            f"The invention provides a method for the preparation of {query}.",
            f"This patent discloses a synthesis method for {query}."
        ]

    # print("Загрузка данных")
    dataset = pd.read_csv("data/Angl_Abstract.csv", sep=";", encoding="utf-8", on_bad_lines="skip", engine="python")
    dataset['Synonyms'] = dataset['Synonyms'].apply(string_to_list)
    dataset['querys'] = dataset.apply(lambda row: [row['Name']] + row['Synonyms'] if pd.notna(row['Name']) else row['Synonyms'], axis=1)
    dataset['abstracts'] = dataset['abstracts'].apply(string_to_dict)
    dataset['score'] = None

    # print("Загрузка модели")
    model = SentenceTransformer('AI-Growth-Lab/PatentSBERTa')

    # print("Подготовка эмбеддингов")

    all_abstracts = list(set(chain.from_iterable([list(d.values()) for d in dataset['abstracts']])))
    abstract_embeddings = dict(zip(
        all_abstracts,
        model.encode(all_abstracts, convert_to_tensor=True, show_progress_bar=True)
    ))

    query_embedding_cache = {}

    for query_list in tqdm(dataset["querys"], desc="Запросы"):
        for q in query_list:
            if q not in query_embedding_cache:
                phrases = generate_synthesis_phrases(q)
                embs = model.encode(phrases, convert_to_tensor=True)
                query_embedding_cache[q] = embs

    def calculate_synthesis_score(query, abstract):
        if not abstract:
            return [0.0] * 5 

        abstract_emb = abstract_embeddings.get(abstract)
        synthesis_embs = query_embedding_cache.get(query)

        if abstract_emb is None or synthesis_embs is None:
            return [0.0] * 5

        similarities = util.pytorch_cos_sim(abstract_emb, synthesis_embs)
        return similarities.squeeze().tolist()


    # print("Расчет скоров")
    all_scores = []

    for i in tqdm(range(len(dataset)), desc="Обработка записей"):
        res_dict = {}
        queries = dataset.loc[i, "querys"]
        patents = dataset.loc[i, "abstracts"]
        for patent_id, abstract in patents.items():
            inner_scores = {}
            for q in queries:
                score = calculate_synthesis_score(q, abstract)
                inner_scores[q] = score
            res_dict[patent_id] = inner_scores
        all_scores.append(res_dict)

    dataset["score"] = all_scores

    dataset["score"] = dataset["score"].apply(json.dumps)
    output_file = "data/Scores.csv"
    dataset.to_csv(output_file, sep=";", encoding="utf-8", index=False)
    print(f"\n✔ Готово! Данные сохранены в: {output_file}")

if __name__ == '__main__':
    run_steps()