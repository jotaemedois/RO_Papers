"""
Gera `studies_clean.jsonl` removendo o campo `sections` de `studies.jsonl`.
Mantém `study_id` e `full_text`.
"""

from __future__ import annotations

import json
from config import settings


def main() -> None:
    src = settings.studies_jsonl
    dst = settings.interim_dir / "studies_clean.jsonl"

    with src.open(encoding="utf-8") as fin, dst.open("w", encoding="utf-8") as fout:
        for line in fin:
            if not line.strip():
                continue
            rec = json.loads(line)
            cleaned = {
                "study_id": rec.get("study_id"),
                "full_text": rec.get("full_text", ""),
            }
            fout.write(json.dumps(cleaned, ensure_ascii=False))
            fout.write("\n")


if __name__ == "__main__":
    main()

