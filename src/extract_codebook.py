"""
Utilitário para extrair o Codebook em texto plano a partir do PDF.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

from config import settings


def extract_codebook(pdf_path: Path, out_path: Path) -> None:
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text("text") for page in doc)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")


def main() -> None:
    pdf_path = Path("BRIDGE_Codebook_Updated_15-10.pdf")
    extract_codebook(pdf_path, settings.codebook_txt)


if __name__ == "__main__":
    main()

