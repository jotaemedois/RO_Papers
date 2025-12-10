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


def is_table_block(text: str) -> bool:
    """Heurística simples para identificar blocos que parecem tabela."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return False
    # Se muitas linhas contêm separadores típicos de tabela, considerar como tabela.
    sep_lines = 0
    for ln in lines:
        if "|" in ln or "\t" in ln:
            sep_lines += 1
            continue
        # Padrão de múltiplos espaços sugerindo colunas alinhadas.
        if re.search(r"\S+\s{2,}\S+.*\s{2,}\S+", ln):
            sep_lines += 1
    return sep_lines >= max(2, int(0.6 * len(lines)))


def clean_text(raw: str) -> str:
    """Remove quebras artificiais e normaliza espaçamento, preservando parágrafos."""
    text = raw.replace("\r", "")
    # Desfazer hifenização simples
    text = re.sub(r"-\n", "", text)
    # Colapsar quebras múltiplas para duplas (parágrafos)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Colapsar espaços
    text = re.sub(r"[ \t]+", " ", text)
    # Transformar quebras simples em espaço (mantém duplas como parágrafo)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    # Espaços extras
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


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
    blocks_text: list[str] = []
    for page in doc:
        for block in page.get_text("blocks"):
            block_text = block[4]
            if not block_text or not block_text.strip():
                continue
            if is_table_block(block_text):
                continue
            blocks_text.append(block_text.strip())
    raw_text = "\n\n".join(blocks_text)
    text = clean_text(raw_text)
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

