from pathlib import Path
import pandas as pd

REQUIRED_COLUMNS = {"numero_processo"}
OPTIONAL_COLUMNS = {"cliente", "pasta", "observacao"}

def read_processes(file_path: str):
    path = Path(file_path)
    if path.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(path)
    elif path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError("Arquivo inválido. Envie .xlsx, .xls ou .csv")

    df.columns = [str(c).strip().lower() for c in df.columns]
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError("A planilha precisa conter a coluna obrigatória: numero_processo")

    records = []
    for _, row in df.iterrows():
        numero = str(row.get("numero_processo", "")).strip()
        if numero and numero.lower() != "nan":
            records.append({
                "numero_processo": numero,
                "cliente": clean(row.get("cliente", "")),
                "pasta": clean(row.get("pasta", "")),
                "observacao": clean(row.get("observacao", "")),
            })
    return records

def clean(value):
    text = str(value).strip()
    return "" if text.lower() == "nan" else text
