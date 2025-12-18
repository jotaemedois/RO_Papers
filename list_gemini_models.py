#!/usr/bin/env python3
"""
Script auxiliar para listar modelos Gemini disponíveis.
"""

import os
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("ERRO: GEMINI_API_KEY não está definida!")
    print("Configure com: export GEMINI_API_KEY='sua_chave_aqui'")
    exit(1)

try:
    genai.configure(api_key=GEMINI_API_KEY)
    models = genai.list_models()
    
    print("Modelos Gemini disponíveis para generateContent:\n")
    available = []
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            model_name = model.name.replace('models/', '')
            available.append(model_name)
            print(f"  ✓ {model_name}")
    
    if not available:
        print("  Nenhum modelo encontrado com suporte a generateContent")
    else:
        print(f"\nTotal: {len(available)} modelo(s) disponível(is)")
        print("\nModelos recomendados:")
        print("  - gemini-1.5-pro (mais capaz, melhor para tarefas complexas)")
        print("  - gemini-1.5-flash (mais rápido, bom para tarefas simples)")
        print("  - gemini-pro (versão anterior, ainda disponível)")

except Exception as e:
    print(f"ERRO ao listar modelos: {e}")
    print("\nVerifique se:")
    print("  1. Sua API key está correta")
    print("  2. Você tem acesso à API do Gemini")
    print("  3. Sua conexão com a internet está funcionando")


