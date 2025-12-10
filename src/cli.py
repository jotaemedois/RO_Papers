"""
CLI mínima para orquestrar as três fases.
"""

from __future__ import annotations

import typer

from compile_outputs import main as compile_main
from llm_codec import main as llm_main
from parse_pdfs import main as parse_main

app = typer.Typer(help="Pipeline SLR automatizado.")


@app.command()
def parse_pdfs():
    """Fase 1: extrair texto dos PDFs para JSONL."""
    parse_main()


@app.command()
def code():
    """Fase 2: chamar LLM para codificação."""
    llm_main()


@app.command()
def compile():
    """Fase 3: consolidar em XLSX."""
    compile_main()


if __name__ == "__main__":
    app()

