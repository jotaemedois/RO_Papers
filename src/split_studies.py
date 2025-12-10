"""
Utilitário para dividir `studies.jsonl` em arquivos texto por estudo.
Cada arquivo terá o nome do `study_id` e conterá apenas `full_text`.
"""

from __future__ import annotations

from pathlib import Path
import json

from config import settings


def main() -> None:
    source = settings.studies_jsonl
    out_dir = settings.interim_dir / "by_study"
    out_dir.mkdir(parents=True, exist_ok=True)

    with source.open(encoding="utf-8") as fin:
        for line in fin:
            if not line.strip():
                continue
            rec = json.loads(line)
            study_id = rec.get("study_id")
            full_text = rec.get("full_text", "")
            if not study_id:
                continue
            outfile = out_dir / f"{study_id}.txt"
            outfile.write_text(full_text, encoding="utf-8")


if __name__ == "__main__":
    main()

