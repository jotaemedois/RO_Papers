#!/usr/bin/env python3
"""
Script para processar estudos usando Google Gemini API diretamente.
Mantém as variáveis PPLX_API_KEY e PPLX_MODEL intactas para uso futuro.
"""

import os
import json
import time
from typing import Dict, Any, Optional
import google.generativeai as genai
from pathlib import Path

# Configuração - usa variáveis de ambiente para Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")  # padrão: gemini-1.5-pro (modelos disponíveis: gemini-pro, gemini-1.5-pro, gemini-1.5-flash)
STUDY_IDS = os.getenv("STUDY_IDS")  # IDs dos estudos a processar (separados por vírgula ou espaço)

# As variáveis PPLX são mantidas intactas (não usadas aqui)
# PPLX_API_KEY = os.getenv("PPLX_API_KEY")  # mantida para uso futuro
# PPLX_MODEL = os.getenv("PPLX_MODEL")  # mantida para uso futuro

def load_codebook() -> str:
    """Carrega o codebook do arquivo."""
    codebook_path = Path("prompts/codebook.txt")
    if codebook_path.exists():
        return codebook_path.read_text(encoding="utf-8")
    return ""

def load_studies(input_file: str) -> list:
    """Carrega estudos do arquivo JSONL."""
    studies = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                studies.append(json.loads(line))
    return studies

def filter_studies_by_ids(studies: list, study_ids_str: Optional[str]) -> list:
    """Filtra estudos baseado em STUDY_IDS."""
    if not study_ids_str:
        return studies
    
    # Parse STUDY_IDS - aceita vírgulas, espaços ou ambos
    study_ids_list = []
    for item in study_ids_str.replace(",", " ").split():
        study_id = item.strip()
        if study_id:
            study_ids_list.append(study_id)
    
    if not study_ids_list:
        return studies
    
    # Filtra estudos
    filtered = [s for s in studies if s.get("study_id") in study_ids_list]
    
    if len(filtered) < len(study_ids_list):
        found_ids = {s.get("study_id") for s in filtered}
        missing_ids = set(study_ids_list) - found_ids
        if missing_ids:
            print(f"AVISO: Os seguintes STUDY_IDS não foram encontrados: {', '.join(missing_ids)}")
    
    return filtered

def create_prompt(study: Dict[str, Any], codebook: str) -> str:
    """Cria o prompt para o LLM baseado no estudo e codebook."""
    study_id = study.get("study_id", "UNKNOWN")
    full_text = study.get("full_text", "")
    
    prompt = f"""Você é um assistente especializado em análise de literatura acadêmica.

Tarefa: Extrair e codificar informações de um estudo acadêmico de acordo com o codebook fornecido.

STUDY ID: {study_id}

CODEBOOK:
{codebook}

TEXTO DO ESTUDO:
{full_text[:50000]}  # Limita a 50k caracteres para evitar exceder limites

INSTRUÇÕES:
1. Analise o texto do estudo cuidadosamente
2. Extraia as informações solicitadas no codebook
3. Retorne APENAS um objeto JSON válido com a seguinte estrutura:
{{
    "study_id": "{study_id}",
    "codes": [
        {{
            "variable": "nome_da_variavel",
            "code": valor_ou_codigo,
            "label": "descrição_do_label",
            "evidence": "evidência_do_texto"
        }},
        ...
    ]
}}

IMPORTANTE:
- Use os códigos e valores especificados no codebook
- Sempre inclua evidência do texto para cada código
- Se a informação não estiver disponível, use 99="Not Reported"
- Retorne APENAS JSON, sem texto adicional antes ou depois
"""
    return prompt

def list_available_models():
    """Lista os modelos disponíveis na API."""
    if not GEMINI_API_KEY:
        print("ERRO: GEMINI_API_KEY não está definida para listar modelos.")
        return []
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        models = genai.list_models()
        available = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                available.append(model.name.replace('models/', ''))
        return available
    except Exception as e:
        print(f"Erro ao listar modelos: {e}")
        return []

def call_gemini_api(prompt: str, max_retries: int = 3) -> Optional[str]:
    """Chama a API do Gemini."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY não está definida. Configure a variável de ambiente.")
    
    # Configura o cliente Gemini
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Verifica se o modelo existe antes de tentar usar
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
    except Exception as e:
        print(f"ERRO: Modelo '{GEMINI_MODEL}' não encontrado ou inválido.")
        print(f"Erro: {e}")
        print("\nModelos disponíveis:")
        available = list_available_models()
        if available:
            for m in available:
                print(f"  - {m}")
        else:
            print("  Não foi possível listar modelos. Verifique sua API key.")
        raise
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                }
            )
            return response.text
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"Erro na tentativa {attempt + 1}/{max_retries}: {e}")
                print(f"Aguardando {wait_time} segundos antes de tentar novamente...")
                time.sleep(wait_time)
            else:
                raise
    
    return None

def extract_json_from_response(response_text: str) -> Optional[Dict]:
    """Extrai JSON da resposta do LLM."""
    # Tenta encontrar JSON na resposta
    response_text = response_text.strip()
    
    # Remove markdown code blocks se presentes
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1]) if lines[-1].startswith("```") else "\n".join(lines[1:])
    
    # Tenta parsear como JSON
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Tenta encontrar JSON dentro do texto
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        if start_idx >= 0 and end_idx > start_idx:
            try:
                return json.loads(response_text[start_idx:end_idx])
            except json.JSONDecodeError:
                pass
    
    return None

def process_study(study: Dict[str, Any], codebook: str) -> Optional[Dict]:
    """Processa um único estudo."""
    study_id = study.get("study_id", "UNKNOWN")
    print(f"Processando {study_id}...")
    
    prompt = create_prompt(study, codebook)
    response = call_gemini_api(prompt)
    
    if not response:
        print(f"Erro: Não foi possível obter resposta para {study_id}")
        return None
    
    result = extract_json_from_response(response)
    if not result:
        print(f"Erro: Não foi possível extrair JSON da resposta para {study_id}")
        print(f"Resposta recebida: {response[:500]}...")
        return None
    
    return result

def main():
    """Função principal."""
    # Verifica se a API key está configurada
    if not GEMINI_API_KEY:
        print("ERRO: GEMINI_API_KEY não está definida!")
        print("Configure com: export GEMINI_API_KEY='sua_chave_aqui'")
        return
    
    print(f"Usando modelo: {GEMINI_MODEL}")
    print(f"PPLX_API_KEY mantida: {'Sim' if os.getenv('PPLX_API_KEY') else 'Não (opcional)'}")
    print(f"PPLX_MODEL mantida: {os.getenv('PPLX_MODEL', 'Não definida (opcional)')}")
    if STUDY_IDS:
        print(f"STUDY_IDS filtrado: {STUDY_IDS}")
    else:
        print("STUDY_IDS: Não definido (processando todos os estudos)")
    
    # Verifica se o modelo está disponível
    print("\nVerificando modelo disponível...")
    available_models = list_available_models()
    if available_models:
        if GEMINI_MODEL not in available_models:
            print(f"AVISO: Modelo '{GEMINI_MODEL}' pode não estar disponível.")
            print(f"Modelos disponíveis: {', '.join(available_models[:5])}")
            if len(available_models) > 5:
                print(f"... e mais {len(available_models) - 5} modelos")
        else:
            print(f"✓ Modelo '{GEMINI_MODEL}' está disponível")
    print("-" * 50)
    
    # Carrega codebook
    codebook = load_codebook()
    if not codebook:
        print("AVISO: Codebook não encontrado. Continuando sem ele...")
    
    # Configuração de arquivos
    input_file = "data/interim/studies.jsonl"
    output_file = "data/processed/llm_outputs_gemini.jsonl"
    
    # Cria diretório de saída se não existir
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Carrega estudos
    print(f"Carregando estudos de {input_file}...")
    all_studies = load_studies(input_file)
    print(f"Encontrados {len(all_studies)} estudos no arquivo")
    
    # Filtra estudos se STUDY_IDS estiver definido
    studies = filter_studies_by_ids(all_studies, STUDY_IDS)
    print(f"Estudos a processar: {len(studies)}")
    
    # Processa cada estudo
    results = []
    for i, study in enumerate(studies, 1):
        print(f"\n[{i}/{len(studies)}] ", end="")
        result = process_study(study, codebook)
        if result:
            results.append(result)
            # Salva incrementalmente
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
        
        # Pequena pausa entre requisições para evitar rate limiting
        if i < len(studies):
            time.sleep(1)
    
    print(f"\n{'='*50}")
    print(f"Processamento concluído!")
    print(f"Resultados salvos em: {output_file}")
    print(f"Estudos processados com sucesso: {len(results)}/{len(studies)}")

if __name__ == "__main__":
    main()

