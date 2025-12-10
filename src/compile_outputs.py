"""
Fase 3: consolidação das saídas do LLM em CSV e XLSX.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

from config import settings


# Ajuste a lista de colunas conforme o template real.
TEMPLATE_COLS = ["Study_ID", "Variable", "Code", "Label", "Evidence"]


def main() -> None:
    settings.outputs_dir.mkdir(parents=True, exist_ok=True)
    
    if not settings.llm_outputs_jsonl.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {settings.llm_outputs_jsonl}. "
            "Execute a Fase 2 primeiro (llm_codec.py)."
        )
    
    rows = []
    with settings.llm_outputs_jsonl.open(encoding="utf-8") as fin:
        for line in fin:
            rec = json.loads(line)
            study_id = rec["study_id"]
            for code in rec["codes"]:
                rows.append(
                    {
                        "Study_ID": study_id,
                        "Variable": code["variable"],
                        "Code": code["code"],
                        "Label": code["label"],
                        "Evidence": code["evidence"],
                    }
                )
    
    if not rows:
        raise ValueError("Nenhum dado encontrado no arquivo JSONL.")
    
    df = pd.DataFrame(rows, columns=TEMPLATE_COLS)
    
    # Gerar CSV
    csv_output = settings.outputs_dir / "SLR_coded.csv"
    df.to_csv(csv_output, index=False, encoding="utf-8")
    print(f"CSV gerado: {csv_output} ({len(rows)} linhas)")
    
    # Gerar XLSX (requer openpyxl)
    try:
        df.to_excel(settings.xlxs_output, index=False, engine="openpyxl")
        print(f"XLSX gerado: {settings.xlxs_output} ({len(rows)} linhas)")
    except ImportError:
        print("Aviso: openpyxl não instalado. Instale com: pip install openpyxl")
        print("Apenas CSV foi gerado.")
    except Exception as e:
        print(f"Erro ao gerar XLSX: {e}")
        print("Apenas CSV foi gerado.")


if __name__ == "__main__":
    main()

