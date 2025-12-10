"""
Fase 3: consolidação das saídas do LLM em XLSX.
"""

from __future__ import annotations

import json

import pandas as pd

from config import settings


# Ajuste a lista de colunas conforme o template real.
TEMPLATE_COLS = ["Study_ID", "Variable", "Code", "Label", "Evidence"]


def main() -> None:
    settings.outputs_dir.mkdir(parents=True, exist_ok=True)
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
    df = pd.DataFrame(rows, columns=TEMPLATE_COLS)
    df.to_excel(settings.xlxs_output, index=False)


if __name__ == "__main__":
    main()

