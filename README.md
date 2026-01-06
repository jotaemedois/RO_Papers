# RO Papers - Processing Pipeline

This repository contains the pipeline for processing and analyzing academic studies.

## Prerequisites

- Python 3.13+
- Virtual environment (`.venv`)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### 1. PDF Parsing

Extracts and processes study PDFs:

```bash
source .venv/bin/activate
export PYTHONPATH=src:.
python src/parse_pdfs.py
```

### 2. Analysis with Perplexity

Processes studies using the Perplexity API:

```bash
source .venv/bin/activate
export PYTHONPATH=src:.
export PPLX_API_KEY="api_key"
export PPLX_MODEL="sonar-reasoning-pro"
export STUDY_IDS="XXX,YYY,etc"  # Optional: process only specific studies
python src/llm_codec.py
```

**Note:** If `STUDY_IDS` is not defined, all studies will be processed.

### 3. Analysis with Gemini

Processes studies using the Google Gemini API:

```bash
source .venv/bin/activate
pip install google-generativeai
export GEMINI_API_KEY='api_key'
export GEMINI_MODEL='gemini-2.5-pro'
export STUDY_IDS='XXX,YYY,etc'  # Optional: process only specific studies
python process_studies_gemini.py
```

**Note:** If `STUDY_IDS` is not defined, all studies will be processed.

### 4. Compile Outputs

Compiles LLM outputs (JSONL) to Excel (XLSX):

```bash
source .venv/bin/activate
export LLM_OUTPUTS_FILE='data/processed/XXX.jsonl'  # Optional: specify input file
python src/compile_outputs.py
```

**Alternatives to specify the input file:**
- Use command line argument: `python src/compile_outputs.py -i data/processed/XXX.jsonl`
- Use environment variable: `export LLM_OUTPUTS_FILE='data/processed/XXX.jsonl'`
- Default (if not specified): `data/processed/llm_outputs.jsonl`

## Directory Structure

```
RO_Papers/
├── data/
│   ├── raw/              # Original PDFs
│   ├── interim/          # Intermediate processed data
│   └── processed/        # LLM outputs (JSONL)
├── outputs/              # Final results (Excel)
├── prompts/              # Codebook and rigor rules
└── src/                  # Source code
```

## Environment Variables

### Perplexity
- `PPLX_API_KEY`: Perplexity API key
- `PPLX_MODEL`: Model to use (e.g., `sonar-reasoning-pro`)

### Gemini
- `GEMINI_API_KEY`: Google Gemini API key
- `GEMINI_MODEL`: Model to use (e.g., `gemini-2.5-pro`, `gemini-2.5-flash`)

### Filters
- `STUDY_IDS`: IDs of studies to process (comma or space separated)
- `LLM_OUTPUTS_FILE`: Path to input JSONL file for compilation
