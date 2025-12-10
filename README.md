## Pipeline SLR Automatizado (BRIDGE)

Este projeto implementa um pipeline em Python para codificar 199 artigos (PDF) com um LLM seguindo o Codebook BRIDGE e regras de rigor científico.

### Organização de pastas
- `data/raw/` – PDFs originais (199 artigos).
- `data/interim/` – extrações de texto por artigo (`studies.jsonl`).
- `data/processed/` – saídas do LLM (`llm_outputs.jsonl`).
- `outputs/` – exportações finais (`SLR_coded.xlsx`).
- `prompts/` – `codebook.txt` (extraído do PDF) e `rigor_rules.txt`.
- `src/` – código-fonte (parse, LLM, compilação, CLI, utilitários).
- `.venv/` – ambiente virtual (opcional, já criado neste setup).

### Dependências principais
- PyMuPDF (`pymupdf`) para extração de PDF.
- pandas, pydantic.
- openai (API compatível do Perplexity).
- tqdm, typer.

### Configurações centrais
Arquivo `src/config.py` define caminhos e modelo do LLM:
- `raw_dir`, `interim_dir`, `processed_dir`, `outputs_dir`, `prompts_dir`.
- `codebook_txt`, `rigor_rules_txt`, `studies_jsonl`, `llm_outputs_jsonl`, `xlxs_output`.
- `model` (padrão: `sonar-reasoning-pro`; ajuste conforme modelos permitidos no Perplexity, e.g., `sonar-reasoning`, `sonar-pro`, `sonar`).
- `perplexity_base_url` (padrão: `https://api.perplexity.ai`).

Ajustes comuns:
- Colunas finais do template: editar `TEMPLATE_COLS` em `src/compile_outputs.py` para refletir exatamente `SLR_data_extraction_with_codebook.xlsx`.
- Se os PDFs estiverem noutro local, mude `raw_dir` em `config.py`.
- Se usar outro LLM: ajuste `model`/`perplexity_base_url` em `config.py` e `call_llm` em `src/llm_codec.py`.

### Ambiente Python
Um ambiente virtual já foi criado em `.venv/`.
- Ativar: `source .venv/bin/activate`
- PYTHONPATH para resolver imports locais: `PYTHONPATH=src:.`
- Dependências já instaladas: `pymupdf pandas pydantic openai google-generativeai tqdm typer` (google-generativeai pode ser removido se não usar Gemini).

### Preparação do Codebook
- O Codebook PDF (`BRIDGE_Codebook_Updated_15-10.pdf`) foi extraído para texto em `prompts/codebook.txt` via `src/extract_codebook.py`.
- Regras de rigor estão em `prompts/rigor_rules.txt`. Edite se quiser refinar instruções.

### Fluxo em 3 fases
Use o PYTHONPATH para os comandos abaixo: `PYTHONPATH=src:.`

1) **Fase 1 – Parsing PDFs**
   - Comando: `python src/parse_pdfs.py`
   - Lê todos os PDFs em `data/raw/` (suporta `.pdf` e `.PDF`), tenta identificar seções (abstract, methods, results, conclusion) e grava `data/interim/studies.jsonl`.

2) **Fase 2 – Codificação via LLM (Perplexity)**
   - Requer `PPLX_API_KEY` (ou `PERPLEXITY_API_KEY`) exportada no ambiente.
   - Modelo padrão em `config.py`: `llama-3.1-sonar-large-128k-online`; endpoint: `https://api.perplexity.ai`.
   - Comando: `python src/llm_codec.py`
   - Para cada estudo, monta prompt com Codebook + Regras de Rigor + texto do artigo (seções concatenadas) e salva a saída validada por pydantic em `data/processed/llm_outputs.jsonl`.
   - Rigor: não inferir; 99 = Not Reported; 98 = Unclear; sempre citar evidência literal.

3) **Fase 3 – Compilação**
   - Ajuste `TEMPLATE_COLS` em `src/compile_outputs.py` conforme o Excel de template.
   - Comando: `python src/compile_outputs.py`
   - Gera `outputs/SLR_coded.xlsx` com Study_ID, variáveis, códigos, rótulos e evidências.

### CLI opcional
`src/cli.py` expõe comandos via Typer:
- `python -m src.cli parse-pdfs`
- `python -m src.cli code`
- `python -m src.cli compile`

### Variáveis e chaves
- `PPLX_API_KEY` (ou `PERPLEXITY_API_KEY`) deve estar definida para a Fase 2.

### Possíveis ajustes
- Se o LLM tiver limite de tokens baixo, adapte `build_prompt` e implemente chunking (não dividir methods/results separadamente para evitar perda de contexto).
- Se o esquema de saída mudar, edite `models.py` (pydantic) e `prompt_builder.py`.
- Para outro provedor de LLM, ajuste `call_llm` e configuração no `config.py` (modelo, base_url, header/chave).

### Troubleshooting rápido
- Erro “No module named ...”: garantir `PYTHONPATH=src:.` ou ativar `.venv`.
- Erro de validação pydantic na Fase 2: revisar resposta do modelo e prompt; pode reexecutar o artigo após ajustar o prompt ou schema.
- Seções vazias: o parser preserva campos vazios; LLM deve retornar 99 (Not Reported) nesses casos.

