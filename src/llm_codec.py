"""
Fase 2: chamada ao LLM para codificação com rigor científico.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Iterable, Optional, Set
import re

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


def yield_studies(path: Path) -> Iterable[StudyRecord]:
    with path.open(encoding="utf-8") as fin:
        for line in fin:
            yield StudyRecord.model_validate_json(line)


def call_llm(client: OpenAI, prompt: str, model_name: str) -> str:
    backoff = 1.0
    while True:
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Você é um assistente de codificação acadêmica. "
                            "Retorne APENAS JSON válido, sem texto fora do JSON. "
                            "Não inclua delimitadores como ``` ou tags <think>. "
                            "Responda diretamente com JSON no corpo."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            )
            raw = completion.choices[0].message.content or ""
            return sanitize_json(raw)
        except Exception as exc:  # noqa: BLE001
            if "429" in str(exc) or "quota" in str(exc).lower():
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
                continue
            raise


def sanitize_json(raw: str) -> str:
    """
    Remove tags <think>...</think> e blocos ```...``` e tenta extrair o primeiro JSON.
    """
    # remover blocos <think>...</think>
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL | re.IGNORECASE)
    # remover fences ```
    raw = raw.replace("```json", "```").replace("```", "\n")
    raw = raw.strip()
    # tentar extrair JSON bruto
    match = re.search(r"\{.*\}|\[.*\]", raw, flags=re.DOTALL)
    if match:
        return match.group(0).strip()
    return raw


def sanitize_codes(codes: list) -> list:
    """
    Sanitiza códigos: converte strings numéricas para int, inválidos -> 99 (Not Reported).
    """
    sanitized = []
    for item in codes:
        if not isinstance(item, dict):
            continue
        code_val = item.get("code")
        # tentar converter string numérica para int
        if isinstance(code_val, str):
            # tentar extrair número da string
            num_match = re.search(r"\d+", code_val)
            if num_match:
                code_val = int(num_match.group())
            else:
                # se não houver número, usar 99 (Not Reported)
                code_val = 99
        elif not isinstance(code_val, int):
            code_val = 99
        sanitized.append({**item, "code": code_val})
    return sanitized


def parse_response(raw: str, study_id: str) -> LLMResponse:
    """
    Tenta validar direto; fallback para formatos comuns retornados pelo modelo:
    - lista simples -> envolve em {study_id, codes}
    - dict com 'study_coding' -> envolve em {study_id, codes}
    - dict com uma lista em qualquer chave -> usa a primeira lista encontrada como codes.
    Sanitiza códigos antes de validar (converte strings para int, inválidos -> 99).
    """
    try:
        data = json.loads(raw)
        codes = None
        if isinstance(data, list):
            codes = sanitize_codes(data)
        elif isinstance(data, dict):
            if "study_coding" in data and isinstance(data["study_coding"], list):
                codes = sanitize_codes(data["study_coding"])
            elif "codes" in data and isinstance(data["codes"], list):
                codes = sanitize_codes(data["codes"])
            else:
                # procurar qualquer lista de dicts dentro do dict
                for v in data.values():
                    if isinstance(v, list) and v and isinstance(v[0], dict):
                        codes = sanitize_codes(v)
                        break
        if codes is None:
            raise ValueError("Não foi possível extrair lista de códigos da resposta")
        wrapped = {"study_id": study_id, "codes": codes}
        return LLMResponse.model_validate(wrapped)
    except (ValidationError, json.JSONDecodeError, ValueError) as e:
        # tentar validar direto como último recurso
        try:
            return LLMResponse.model_validate_json(raw)
        except ValidationError:
            raise RuntimeError(f"Falha ao parsear resposta para {study_id}: {e}") from e


def main() -> None:
    client = configure_client()
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    codebook_text, rigor_rules = load_prompt_assets()

    model_name = os.getenv("PPLX_MODEL") or settings.model

    # Filtros opcionais para rodar subset em dry-run ou validação
    ids_env = os.getenv("STUDY_IDS")  # ex: "SLR001,SLR005"
    ids_filter: Optional[Set[str]] = None
    if ids_env:
        ids_filter = {s.strip() for s in ids_env.split(",") if s.strip()}
    max_studies_env = os.getenv("MAX_STUDIES")  # ex: "5"
    max_studies = int(max_studies_env) if max_studies_env else None

    with settings.llm_outputs_jsonl.open("w", encoding="utf-8") as fout:
        processed = 0
        for study in tqdm(yield_studies(settings.studies_jsonl), desc="Codificando LLM"):
            if ids_filter and study.study_id not in ids_filter:
                continue
            if max_studies is not None and processed >= max_studies:
                break
            prompt = build_prompt(study, codebook_text, rigor_rules)
            raw = call_llm(client, prompt, model_name)
            try:
                parsed = parse_response(raw, study.study_id)
            except Exception as err:  # noqa: BLE001
                raise RuntimeError(f"Falha de validação para {study.study_id}: {err}") from err
            fout.write(parsed.model_dump_json(ensure_ascii=False))
            fout.write("\n")
            processed += 1


if __name__ == "__main__":
    main()

