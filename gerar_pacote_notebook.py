# -*- coding: utf-8 -*-
"""
gerar_pacote_notebook.py — Empacota o notebook + 4 arquivos auxiliares
em um zip MENOR (~5 MB) para quando a banca quer rodar SOMENTE o
notebook, sem clonar o repo inteiro.

Conteudo do zip:
  notebook_h2o_agente_mvp.ipynb
  requirements_app.txt
  docs/agente/system_prompt.md
  docs/agente/tools_schema.json
  docs/demo/script_turnos.json
  dados_sinteticos/contratos.csv
  LEIA_ME_NOTEBOOK.txt

Saida: entregas/Predfy_Notebook_Standalone.zip

Diferencas para Predfy_Banca_Entrega.zip:
  - Sem PDFs nem screenshots — so o notebook executavel.
  - Tamanho ~5 MB (vs ~4.2 MB do completo, mas com codigo executavel).
  - Banca: extrair, abrir o .ipynb num kernel Python 3.10+, rodar.
"""
from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent
ENTREGAS_DIR = REPO_ROOT / "entregas"
ZIP_PATH = ENTREGAS_DIR / "Predfy_Notebook_Standalone.zip"

# Arquivos a incluir (caminho relativo no repo == caminho dentro do zip).
# A estrutura preserva pastas para que o notebook ache via relative paths.
ARQUIVOS = [
    "notebook_h2o_agente_mvp.ipynb",
    "requirements_app.txt",
    "gerar_demo_eaps.py",                 # Caminho B — gera demo_eaps_vai_atrasar.csv
    "docs/agente/system_prompt.md",
    "docs/agente/tools_schema.json",
    "docs/demo/script_turnos.json",
    "dados_sinteticos/contratos.csv",
]

LEIA_ME = """\
Predfy — Notebook Standalone (HyperCopa DISEC 2026)
====================================================

Este zip contem APENAS o necessario para rodar o notebook
notebook_h2o_agente_mvp.ipynb sem precisar clonar o repo
hypercopa-disec-mvp.

Conteudo
--------
- notebook_h2o_agente_mvp.ipynb  : o notebook em si.
- requirements_app.txt            : versoes pinadas das dependencias.
- gerar_demo_eaps.py              : gerador do CSV de demo (Caminho B).
- docs/agente/system_prompt.md    : prompt do agente OpenAI (Caminho A).
- docs/agente/tools_schema.json   : schema das 4 tools (Caminho A).
- docs/demo/script_turnos.json    : turnos pre-gravados (Caminho C, modo demo).
- dados_sinteticos/contratos.csv  : CSV do cenario canonico (Caminho C).

Como rodar (5 passos)
---------------------
1. Extraia o zip numa pasta vazia.
2. Crie um virtualenv e ative:
     Windows:  python -m venv .venv
               .\\.venv\\Scripts\\Activate.ps1
     Linux:    python3 -m venv .venv
               source .venv/bin/activate
3. Registre o kernel "Python (Predfy)" no Jupyter:
     pip install jupyter ipykernel
     python -m ipykernel install --user --name predfy --display-name "Python (Predfy)"
4. Abra o notebook (VS Code ou jupyter notebook) e selecione o kernel "Python (Predfy)".
5. Rode em ordem: a Secao 1 instala as dependencias (pandas, h2o, openai, etc.)
   com fallback automatico (uv -> pip -> lotes) caso a rede BB caia (erro 10054).

Para a banca
------------
- O Caminho C (Modo demonstracao offline) NAO precisa de chave OpenAI nem rede.
- O cenario canonico eh "EAP DICOI / vai atrasar?" e usa contratos.csv.
- Resultado eh deterministico (seed=42 em geradores, splits e AutoML).

Repositorio publico (caso queira a versao completa)
---------------------------------------------------
https://github.com/FranMarteen/hypercopa-disec-mvp

Equipe HyperCopa DISEC 2026
Time 1 — Modelos: Joao 23 (cap.) · Francisco · Rosali · Silvia
Time 2 — Agente : Bento 14 (cap.) · Felipe · Amelia · Vania · Rafael
"""


def main():
    ENTREGAS_DIR.mkdir(parents=True, exist_ok=True)

    faltando = [a for a in ARQUIVOS if not (REPO_ROOT / a).exists()]
    if faltando:
        print("ERRO: arquivos ausentes — abortando:", file=sys.stderr)
        for a in faltando:
            print(f"  - {a}", file=sys.stderr)
        sys.exit(1)

    print(f"Empacotando {ZIP_PATH}...")
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in ARQUIVOS:
            src = REPO_ROOT / rel
            zf.write(src, arcname=rel)
            print(f"  + {rel}  ({src.stat().st_size:,} bytes)")
        zf.writestr("LEIA_ME_NOTEBOOK.txt", LEIA_ME)
        print("  + LEIA_ME_NOTEBOOK.txt")

    size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    print(f"\nOK · {ZIP_PATH}  ({size_mb:.1f} MB)")
    print(f"     gerado em {datetime.now().strftime('%Y-%m-%d %H:%M')}")


if __name__ == "__main__":
    main()
