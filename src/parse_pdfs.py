"""
Fase 1: extração de texto dos PDFs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import fitz  # PyMuPDF
from tqdm import tqdm

from config import settings
from models import Sections, StudyRecord

SECTION_PATTERNS = {
    "abstract": r"\babstract\b|\bsummary\b",
    "methods": r"\bmethod(s|ology)?\b|\bmaterials and methods\b",
    "results": r"\bresults?\b|\bfindings?\b",
    "conclusion": r"\bconclusion(s)?\b|\bdiscussion\b|\bimplications\b",
}


def split_sections(text: str) -> Sections:
    boundaries: list[tuple[int, str]] = []
    for name, pat in SECTION_PATTERNS.items():
        for match in re.finditer(pat, text, flags=re.IGNORECASE):
            boundaries.append((match.start(), name))
    boundaries.sort(key=lambda x: x[0])

    sections: dict[str, str] = {k: "" for k in SECTION_PATTERNS}
    for idx, (pos, name) in enumerate(boundaries):
        end = boundaries[idx + 1][0] if idx + 1 < len(boundaries) else len(text)
        sections[name] += text[pos:end].strip()
    return Sections(**sections)


def extract_pdf(pdf_path: Path) -> StudyRecord:
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text("text") for page in doc)
    text = re.sub(r"[ \t]+", " ", text)
    sections = split_sections(text)
    return StudyRecord(study_id=pdf_path.stem, full_text=text, sections=sections)


def main() -> None:
    settings.interim_dir.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(settings.raw_dir.glob("*.pdf")) + sorted(settings.raw_dir.glob("*.PDF"))
    if not pdfs:
        raise SystemExit(f"Nenhum PDF encontrado em {settings.raw_dir}")

    with settings.studies_jsonl.open("w", encoding="utf-8") as fout:
        for pdf in tqdm(pdfs, desc="Extraindo PDFs"):
            record = extract_pdf(pdf)
            fout.write(record.model_dump_json(ensure_ascii=False))
            fout.write("\n")


if __name__ == "__main__":
    main()

