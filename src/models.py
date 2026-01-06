"""
Modelos pydantic para entradas e saídas do pipeline.
"""

from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field


class Sections(BaseModel):
    abstract: str = ""
    methods: str = ""
    results: str = ""
    conclusion: str = ""


class StudyRecord(BaseModel):
    study_id: str
    full_text: str
    sections: Sections


class VariableCode(BaseModel):
    variable: str
    code: int | str | None = None  # Aceita int, str ou None para flexibilidade
    label: str | None = None  # Aceita None caso o LLM não retorne label
    evidence: str | None = Field(
        default=None,
        description="Trecho literal do artigo que justifica o código aplicado.",
    )


class LLMResponse(BaseModel):
    study_id: str
    codes: List[VariableCode]

