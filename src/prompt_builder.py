"""
Construção de prompt com Codebook e Script de Rigor.
"""

from __future__ import annotations

from pathlib import Path

from config import settings
from models import StudyRecord


def build_prompt(study: StudyRecord, codebook_text: str, rigor_rules: str) -> str:
    # Usar o texto completo (full_text) para evitar perda de evidências em seções não detectadas.
    body = study.full_text
    return f"""
You are an academic coding assistant. Follow the Codebook and Rigor Script exactly.
- Do NOT infer; quote literal evidence for every code.
- Use code 99 (Not Reported) if absent; 98 (Unclear) if ambiguous or contradictory.
- CRITICAL: The 'code' field MUST be an INTEGER (number), not a string. Use the numeric code from the Codebook.
- Respond only with JSON matching the schema: list of objects with fields
  [variable (string), code (int - MUST be a number), label (string), evidence (string literal from article)].
- Maintain semantic equivalences defined in the Codebook (e.g., "confidence in parliament" -> Trust).

CODEBOOK:
{codebook_text}

RIGOR RULES:
{rigor_rules}

ARTICLE TEXT:
{body}
""".strip()


def load_prompt_assets() -> tuple[str, str]:
    codebook_text = Path(settings.codebook_txt).read_text(encoding="utf-8")
    rigor_rules = Path(settings.rigor_rules_txt).read_text(encoding="utf-8")
    return codebook_text, rigor_rules

