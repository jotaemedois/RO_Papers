"""
Compila outputs do LLM (JSONL) para Excel (XLSX).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from config import settings
from models import LLMResponse


def load_llm_outputs(input_file: Path | None = None) -> list[LLMResponse]:
    """Carrega outputs do LLM do arquivo JSONL."""
    # Determina qual arquivo usar: argumento > variável de ambiente > padrão
    if input_file is None:
        env_file = os.getenv("LLM_OUTPUTS_FILE")
        if env_file:
            input_file = Path(env_file)
        else:
            input_file = settings.llm_outputs_jsonl
    
    # Garante que é um Path
    if isinstance(input_file, str):
        input_file = Path(input_file)
    
    # Resolve caminho relativo se necessário
    if not input_file.is_absolute():
        input_file = Path.cwd() / input_file
    
    outputs = []
    if not input_file.exists():
        # Tenta encontrar arquivos JSONL alternativos
        jsonl_files = list(settings.processed_dir.glob("*.jsonl"))
        if jsonl_files:
            print(f"Arquivo {input_file} não encontrado.")
            print(f"Arquivos JSONL encontrados em {settings.processed_dir}:")
            for f in jsonl_files:
                print(f"  - {f.name}")
            raise FileNotFoundError(
                f"Arquivo não encontrado: {input_file}\n"
                f"Execute primeiro: python src/llm_codec.py"
            )
        else:
            raise FileNotFoundError(
                f"Arquivo não encontrado: {input_file}\n"
                f"Execute primeiro: python src/llm_codec.py"
            )
    
    with input_file.open(encoding="utf-8") as fin:
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
    parser = argparse.ArgumentParser(
        description="Compila outputs do LLM (JSONL) para Excel (XLSX)."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        default=None,
        help="Caminho para o arquivo JSONL de entrada (ou use variável de ambiente LLM_OUTPUTS_FILE). "
             f"Padrão: {settings.llm_outputs_jsonl}",
    )
    args = parser.parse_args()
    
    # Determina arquivo de entrada
    input_file = None
    if args.input:
        input_file = Path(args.input)
    else:
        env_file = os.getenv("LLM_OUTPUTS_FILE")
        if env_file:
            input_file = Path(env_file)
        else:
            input_file = settings.llm_outputs_jsonl
    
    print(f"Carregando outputs de {input_file}...")
    outputs = load_llm_outputs(input_file)
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

