import pandas as pd
import torch
import ast
import json
from tqdm.auto import tqdm

def run_steps():
    # Enable tqdm support for pandas
    tqdm.pandas()

    def convert_to_dict(data_str):
        if isinstance(data_str, str):
            data_str = data_str.replace("tensor(", "torch.tensor(")
            return eval(data_str)
        return data_str

    def func(data):
        merged_tensors = {}

        for key, values in data.items():
            tensors = []
            for v in values.values():
                if isinstance(v, torch.Tensor):
                    tensors.append(v)
                elif isinstance(v, list):
                    tensors.append(torch.tensor(v))
                elif isinstance(v, float):
                    tensors.append(torch.tensor([v]))
                else:
                    raise ValueError(f"Неожданный тип: {type(v)} = {v}")
            merged_tensors[key] = torch.cat(tensors, dim=0)

        list_dict = {key: value.cpu().flatten().tolist() for key, value in merged_tensors.items()}
        return list_dict

    def sort_dict(zxc):
        for key in zxc:
            zxc[key].sort()
        return zxc

    def top1(zxc):
        for key in zxc:
            zxc[key] = zxc[key][-1]
        return zxc

    def get_top_5(data):
        """
        Функция принимает словарь и возвращает 5 наибольших значений с указанием патентов.
        :param data: Словарь, где ключи — патенты, а значения — числа.
        :return: Словарь с 5 наибольшими значениями.
        """
        return dict(sorted(data.items(), key=lambda item: item[1], reverse=True)[:5])

    def get_top_1(data):
        if not data:
            return None
        return list(sorted(data.items(), key=lambda item: item[1], reverse=True)[:1])[0][1]

    # Load dataset
    dataset = pd.read_csv("data/Scores.csv", sep=";", encoding="utf-8")
    # Parse JSON-encoded score column

    dataset['score'] = dataset['score'].apply(json.loads)
    # Convert string representations to actual dicts

    dataset['score'] = dataset['score'].apply(convert_to_dict)
    # Apply processing functions with progress bars

    dataset['new_score'] = dataset['score'].progress_apply(func)
    dataset['new_score'] = dataset['new_score'].apply(sort_dict)
    dataset['top_1_score'] = dataset['new_score'].progress_apply(top1)
    dataset['top_5_patents'] = dataset['top_1_score'].progress_apply(get_top_5)
    dataset['best_score'] = dataset['top_5_patents'].progress_apply(get_top_1)

    # Serialize columns back to JSON strings

    dataset['score'] = dataset['score'].apply(json.dumps)
    dataset['new_score'] = dataset['new_score'].apply(json.dumps)
    dataset['top_1_score'] = dataset['top_1_score'].apply(json.dumps)
    dataset['top_5_patents'] = dataset['top_5_patents'].apply(json.dumps)

    # Save to CSV
    output_file = "data/Best_score.csv"
    dataset.to_csv(output_file, sep=";", encoding="utf-8", index=False)

    print(f"\n✔ Обработка завершена! Данные сохранены в '{output_file}'.")

if __name__ == '__main__':
    run_steps()