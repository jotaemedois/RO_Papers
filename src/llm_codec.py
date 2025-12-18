"""
Fase 2: chamada ao LLM para codificação com rigor científico.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Iterable

from openai import OpenAI
from pydantic import ValidationError
from tqdm import tqdm

from config import settings
from models import LLMResponse, StudyRecord
from prompt_builder import build_prompt, load_prompt_assets


def configure_client() -> OpenAI:
    api_key = os.getenv("PPLX_API_KEY") or os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise RuntimeError("Defina PPLX_API_KEY (ou PERPLEXITY_API_KEY) no ambiente.")
    return OpenAI(api_key=api_key, base_url=settings.perplexity_base_url)


def yield_studies(path: Path, study_ids_filter: list[str] | None = None) -> Iterable[StudyRecord]:
    with path.open(encoding="utf-8") as fin:
        for line in fin:
            study = StudyRecord.model_validate_json(line)
            if study_ids_filter is None or study.study_id in study_ids_filter:
                yield study


def extract_json_from_response(response_text: str) -> str:
    """Extrai JSON da resposta, removendo tags e markdown."""
    if not response_text:
        return ""
    
    response_text = response_text.strip()
    
    # Remove tags de reasoning do Perplexity
    import re
    response_text = re.sub(r'<[^>]*reasoning[^>]*>.*?</[^>]*>', '', response_text, flags=re.DOTALL | re.IGNORECASE)
    response_text = re.sub(r'<[^>]*think[^>]*>.*?</[^>]*>', '', response_text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove markdown code blocks de forma mais robusta
    # Remove ```json ou ``` do início (com ou sem quebra de linha)
    response_text = re.sub(r'^```(?:json)?\s*\n?', '', response_text, flags=re.MULTILINE)
    # Remove ``` do final (com ou sem quebra de linha)
    response_text = re.sub(r'\n?```\s*$', '', response_text, flags=re.MULTILINE)
    # Remove qualquer ``` que possa ter sobrado no meio ou nas bordas
    response_text = response_text.replace('```json', '').replace('```', '').strip()
    
    # Extrai JSON - pode ser objeto {} ou array []
    # Procura primeiro { ou [ e último } ou ]
    start_obj = response_text.find("{")
    start_arr = response_text.find("[")
    
    if start_obj >= 0 and (start_arr < 0 or start_obj < start_arr):
        # É um objeto JSON
        end_idx = response_text.rfind("}") + 1
        if end_idx > start_obj:
            json_text = response_text[start_obj:end_idx]
            try:
                json.loads(json_text)
                return json_text
            except json.JSONDecodeError:
                pass
    elif start_arr >= 0:
        # É um array JSON - precisa converter para objeto com study_id e codes
        end_idx = response_text.rfind("]") + 1
        if end_idx > start_arr:
            json_text = response_text[start_arr:end_idx]
            try:
                parsed = json.loads(json_text)
                # Se for array, precisa converter para o formato esperado
                # O modelo espera: {"study_id": "...", "codes": [...]}
                if isinstance(parsed, list):
                    # Retorna o array como está - será convertido no main()
                    return json_text
            except json.JSONDecodeError:
                pass
    
    return response_text.strip()


def call_llm(client: OpenAI, prompt: str) -> str:
    # Usa PPLX_MODEL se definido, senão usa o padrão do settings
    model_name = os.getenv("PPLX_MODEL") or settings.model
    backoff = 1.0
    while True:
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            raw_response = completion.choices[0].message.content or ""
            # Limpa a resposta para extrair apenas JSON
            return extract_json_from_response(raw_response)
        except Exception as exc:  # noqa: BLE001
            if "429" in str(exc) or "quota" in str(exc).lower():
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
                continue
            raise


def main() -> None:
    client = configure_client()
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    codebook_text, rigor_rules = load_prompt_assets()
    
    # Filtra estudos se STUDY_IDS estiver definido
    study_ids_filter = None
    study_ids_env = os.getenv("STUDY_IDS")
    if study_ids_env:
        study_ids_filter = [s.strip() for s in study_ids_env.replace(",", " ").split() if s.strip()]
        print(f"Filtrando estudos: {', '.join(study_ids_filter)}")

    with settings.llm_outputs_jsonl.open("w", encoding="utf-8") as fout:
        for study in tqdm(yield_studies(settings.studies_jsonl, study_ids_filter), desc="Codificando LLM"):
            prompt = build_prompt(study, codebook_text, rigor_rules)
            raw = call_llm(client, prompt)
            try:
                # Tenta parsear como JSON primeiro
                parsed_json = json.loads(raw)
                # Se for array, converte para o formato esperado
                if isinstance(parsed_json, list):
                    parsed_json = {"study_id": study.study_id, "codes": parsed_json}
                # Valida com Pydantic
                parsed = LLMResponse.model_validate(parsed_json)
            except (ValidationError, json.JSONDecodeError) as err:
                raise RuntimeError(f"Falha de validação para {study.study_id}: {err}") from err
            fout.write(parsed.model_dump_json(ensure_ascii=False))
            fout.write("\n")


if __name__ == "__main__":
    main()
