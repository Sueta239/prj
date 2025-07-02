import pandas as pd
import re
import sys
import csv

def run_steps():
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "data/Test.csv"

    try:
        df = pd.read_csv(file_path, sep=";", quoting=csv.QUOTE_MINIMAL, on_bad_lines='skip')
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        sys.exit(1)

    required_columns = ["Наименование продукции"]
    if not all(col in df.columns for col in required_columns):
        print(f"Ошибка: в файле отсутствуют нужные столбцы: {required_columns}")
        sys.exit(1)

    df = df[["Наименование продукции"]]
    df["CAS"] = None
    df["Synonyms"] = None
    df["Name"] = None

    def split_name_cas(cell_value):
        """
        Разделяет название продукции и CAS-номер, если они находятся в одной строке.
        """
        if not isinstance(cell_value, str) or not cell_value.strip():
            return cell_value, None

        match = re.search(r'(.+?)[,\s]*CAS[:\s]*([\d\-]+)|(.+?)\s*\(CAS\s*([\d\-]+)\)', cell_value, re.IGNORECASE)
        
        if match:
            name = match.group(1) or match.group(3)
            cas_number = match.group(2) or match.group(4)
            return name.strip("() ,"), cas_number.strip()

        return cell_value, None

    df[['Наименование продукции', 'CAS']] = df['Наименование продукции'].apply(split_name_cas).apply(pd.Series)
    df_with_cas = df[df["CAS"].notna()]
    df_with_cas.to_csv("data/CAS.csv", index=False, sep=";")
    print(f"✔ Файл CAS.csv сохранен ({len(df_with_cas)} строк).")


if __name__ == '__main__':
    run_steps()