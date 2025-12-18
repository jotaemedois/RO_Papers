"""
Configurações centrais do pipeline.
"""

from pathlib import Path
from pydantic import BaseModel


class Settings(BaseModel):
    raw_dir: Path = Path("data/raw")
    interim_dir: Path = Path("data/interim")
    processed_dir: Path = Path("data/processed")
    outputs_dir: Path = Path("outputs")
    prompts_dir: Path = Path("prompts")
    codebook_txt: Path = Path("prompts/codebook.txt")
    rigor_rules_txt: Path = Path("prompts/rigor_rules.txt")
    studies_jsonl: Path = Path("data/interim/studies.jsonl")
    llm_outputs_jsonl: Path = Path("data/processed/llm_outputs.jsonl")
    xlxs_output: Path = Path("outputs/SLR_coded.xlsx")
    model: str = "llama-3.1-sonar-large-128k-online"
    perplexity_base_url: str = "https://api.perplexity.ai"


settings = Settings()

