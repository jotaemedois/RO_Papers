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


def yield_studies(path: Path) -> Iterable[StudyRecord]:
    with path.open(encoding="utf-8") as fin:
        for line in fin:
            yield StudyRecord.model_validate_json(line)


def call_llm(client: OpenAI, prompt: str) -> str:
    backoff = 1.0
    while True:
        try:
            completion = client.chat.completions.create(
                model=settings.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            return completion.choices[0].message.content or ""
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

    with settings.llm_outputs_jsonl.open("w", encoding="utf-8") as fout:
        for study in tqdm(yield_studies(settings.studies_jsonl), desc="Codificando LLM"):
            prompt = build_prompt(study, codebook_text, rigor_rules)
            raw = call_llm(client, prompt)
            try:
                parsed = LLMResponse.model_validate_json(raw)
            except ValidationError as err:
                raise RuntimeError(f"Falha de validação para {study.study_id}: {err}") from err
            fout.write(parsed.model_dump_json(ensure_ascii=False))
            fout.write("\n")


if __name__ == "__main__":
    main()

