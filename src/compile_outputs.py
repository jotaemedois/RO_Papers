"""
Compila outputs do LLM (JSONL) para Excel (XLSX).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from config import settings
from models import LLMResponse


def load_llm_outputs() -> list[LLMResponse]:
    """Carrega outputs do LLM do arquivo JSONL."""
    outputs = []
    if not settings.llm_outputs_jsonl.exists():
        # Tenta encontrar arquivos JSONL alternativos
        jsonl_files = list(settings.processed_dir.glob("*.jsonl"))
        if jsonl_files:
            print(f"Arquivo {settings.llm_outputs_jsonl} não encontrado.")
            print(f"Arquivos JSONL encontrados em {settings.processed_dir}:")
            for f in jsonl_files:
                print(f"  - {f.name}")
            raise FileNotFoundError(
                f"Arquivo não encontrado: {settings.llm_outputs_jsonl}\n"
                f"Execute primeiro: python src/llm_codec.py"
            )
        else:
            raise FileNotFoundError(
                f"Arquivo não encontrado: {settings.llm_outputs_jsonl}\n"
                f"Execute primeiro: python src/llm_codec.py"
            )
    
    with settings.llm_outputs_jsonl.open(encoding="utf-8") as fin:
        for line in fin:
            if line.strip():
                outputs.append(LLMResponse.model_validate_json(line))
    
    return outputs


def compile_to_dataframe(outputs: list[LLMResponse]) -> pd.DataFrame:
    """Converte outputs do LLM para DataFrame."""
    rows = []
    for output in outputs:
        for code in output.codes:
            rows.append({
                "study_id": output.study_id,
                "variable": code.variable,
                "code": code.code,
                "label": code.label,
                "evidence": code.evidence,
            })
    return pd.DataFrame(rows)


def main() -> None:
    """Função principal."""
    print(f"Carregando outputs de {settings.llm_outputs_jsonl}...")
    outputs = load_llm_outputs()
    print(f"Encontrados {len(outputs)} estudos processados")
    
    print("Compilando para DataFrame...")
    df = compile_to_dataframe(outputs)
    print(f"Total de códigos: {len(df)}")
    
    print(f"Salvando em {settings.xlxs_output}...")
    settings.outputs_dir.mkdir(parents=True, exist_ok=True)
    df.to_excel(settings.xlxs_output, index=False, engine="openpyxl")
    print("✓ Compilação concluída!")


if __name__ == "__main__":
    main()

