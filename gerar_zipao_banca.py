# -*- coding: utf-8 -*-
"""
gerar_zipao_banca.py — Empacota a entrega final Predfy num único .zip
para o capitão submeter à banca HyperCopa DISEC 2026.

Conteúdo do zipão:
  00_LEIA_PRIMEIRO.pdf         (cópia do COMO_AVALIAR.pdf)
  01_README.pdf
  02_MVP_CANVAS.pdf            (inclui §8 — Contexto legal Lei 13.303/16)
  03_RELATORIO_SOLUCAO.pdf
  04_ENTREGA_TIME1_MODELOS.pdf
  05_ENTREGA_TIME2_AGENTE.pdf
  06_FLUXOGRAMA.pdf
  07_DIAGRAMAS.pdf
  08_ACESSO.pdf
  09_COPILOT_STUDIO_GUIA.pdf
  10_PREDFY_OVERVIEW.pdf
  diagramas_individuais/...    (PDFs Mermaid standalone)
  screenshots/...              (PNGs do app + INDEX.md)
  relatorio_exemplo/...        (último HTML+JSON gerado, se existir)
  LEIA_ME_PACOTE.txt           (orientações para a banca)

Pré-requisitos:
  - python gerar_pdfs.py já rodou (docs/pdf/ populado)

Saída:
  entregas/Predfy_Banca_Entrega.zip
"""

from __future__ import annotations

import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
PDF_DIR = REPO_ROOT / "docs" / "pdf"
DIAGRAMAS_DIR = PDF_DIR / "diagramas"
SCREENSHOTS_DIR = REPO_ROOT / "docs" / "screenshots"
RELATORIOS_DIR = REPO_ROOT / "relatorios"
ENTREGAS_DIR = REPO_ROOT / "entregas"
ZIP_PATH = ENTREGAS_DIR / "Predfy_Banca_Entrega.zip"

# Mapeamento <nome_no_zip>: <arquivo_origem>
DOCS_NA_RAIZ = [
    ("00_LEIA_PRIMEIRO.pdf", "COMO_AVALIAR.pdf"),
    ("01_README.pdf", "README.pdf"),
    ("02_MVP_CANVAS.pdf", "MVP_CANVAS.pdf"),
    ("03_RELATORIO_SOLUCAO.pdf", "RELATORIO_SOLUCAO.pdf"),
    ("04_ENTREGA_TIME1_MODELOS.pdf", "ENTREGA_TIME1_MODELOS.pdf"),
    ("05_ENTREGA_TIME2_AGENTE.pdf", "ENTREGA_TIME2_AGENTE.pdf"),
    ("06_FLUXOGRAMA.pdf", "FLUXOGRAMA.pdf"),
    ("07_DIAGRAMAS.pdf", "DIAGRAMAS.pdf"),
    ("08_ACESSO.pdf", "ACESSO.pdf"),
    ("09_COPILOT_STUDIO_GUIA.pdf", "COPILOT_STUDIO_GUIA.pdf"),
    ("10_PREDFY_OVERVIEW.pdf", "PREDFY_OVERVIEW.pdf"),
]

LEIA_ME_PACOTE = """\
Predfy — HyperCopa DISEC 2026 · Pacote de Entrega à Banca
Equipe: Times 1 e 2 da ECOA / CESUP-Contratacoes · Banco do Brasil
Data: 07/05/2026

Este zip contem TODOS os artefatos da entrega oficial. A banca pode ler
sem precisar clonar o repo, embora o repo publico continue disponivel em:
  https://github.com/FranMarteen/hypercopa-disec-mvp

Como abrir
==========
1. Extraia o zip numa pasta.
2. Comece pelo arquivo "00_LEIA_PRIMEIRO.pdf" (COMO_AVALIAR) — eh o roteiro
   guiado dos 7 passos da jornada Predfy, incluindo o Caminho C
   (Modo Demonstracao offline), recomendado para a avaliacao.
3. Os outros PDFs cobrem:
     01 — README do projeto.
     02 — MVP Canvas com glossario Lei 13.303/16 (§8).
     03 — Relatorio tecnico estendido (arquitetura, privacidade, ROI).
     04 — Entrega comparativa Time 1 (modelos analiticos).
     05 — Entrega comparativa Time 2 (agente IA + RPA).
     06 — Fluxograma da jornada (3 caminhos A/B/C, em Mermaid renderizado).
     07 — 5 diagramas (visao geral, privacidade, sequencia, tecnologias, producao).
     08 — Doc de acesso/instalacao.
     09 — Guia para publicar o agente no Microsoft Copilot Studio.
     10 — PREDFY_OVERVIEW (1-pager visual).
4. As pastas auxiliares contem:
     diagramas_individuais/  — cada fluxograma Mermaid como PDF standalone
                               (otimo para imprimir ou anexar em apresentacao).
     screenshots/            — capturas reais do app rodando
                               (paleta BB, modo demo ativo, agente, H2O, etc.).
     relatorio_exemplo/      — HTML + JSON do ultimo treino feito pela equipe
                               (caso a banca queira inspecionar a saida).

Para reproduzir
===============
A entrega eh totalmente reproduzivel (seed=42 em todos os pontos de
aleatoriedade). Para testar na propria maquina:

  git clone https://github.com/FranMarteen/hypercopa-disec-mvp.git
  cd hypercopa-disec-mvp
  python -m venv .venv
  .venv\\Scripts\\activate          # Windows
  pip install -r requirements_app.txt
  streamlit run app_agente_bb.py
  -> ative "Modo demonstracao da banca" na sidebar

Referencia legal
================
A solucao opera sob a Lei 13.303/16 (Lei das Estatais), que rege as
contratacoes do BB e demais empresas estatais — nao se aplica a Lei
14.133/21 (Nova Lei de Licitacoes), que rege a administracao publica
direta. O glossario completo (EAP, EAP Padrao, Etapa, Licitacao
Eletronica, DISEC, CESUP-Contratacoes, etc.) esta no §8 do MVP Canvas.

Equipe
======
Time 1 — Modelos Analiticos:
  Capitao Joao 23 · Francisco · Rosali · Silvia
Time 2 — Agente IA + RPA:
  Capitao Bento 14 · Felipe · Amelia · Vania · Rafael

Em caso de duvidas, contate qualquer dos capitaes pelo canal HyperCopa.
"""


def main():
    if not PDF_DIR.exists():
        print(f"ERRO: {PDF_DIR} nao existe. Rode 'python gerar_pdfs.py' primeiro.",
              file=sys.stderr)
        sys.exit(1)

    ENTREGAS_DIR.mkdir(parents=True, exist_ok=True)

    # Verificar se cada PDF da raiz existe; avisar mas seguir mesmo assim.
    faltando = [src for _, src in DOCS_NA_RAIZ if not (PDF_DIR / src).exists()]
    if faltando:
        print("AVISO: PDFs ausentes (sera ignorado no zip):")
        for f in faltando:
            print(f"  - {f}")

    print(f"Empacotando {ZIP_PATH}...")
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1) PDFs principais
        for nome_zip, fonte in DOCS_NA_RAIZ:
            src = PDF_DIR / fonte
            if src.exists():
                zf.write(src, arcname=nome_zip)
                print(f"  + {nome_zip}")

        # 2) Diagramas individuais
        if DIAGRAMAS_DIR.exists():
            for pdf in sorted(DIAGRAMAS_DIR.glob("*.pdf")):
                arc = f"diagramas_individuais/{pdf.name}"
                zf.write(pdf, arcname=arc)
                print(f"  + {arc}")

        # 3) Screenshots
        if SCREENSHOTS_DIR.exists():
            for f in sorted(SCREENSHOTS_DIR.iterdir()):
                if f.is_file() and f.suffix.lower() in (".png", ".md"):
                    arc = f"screenshots/{f.name}"
                    zf.write(f, arcname=arc)
                    print(f"  + {arc}")

        # 4) Relatorio exemplo (mais recente em relatorios/)
        if RELATORIOS_DIR.exists():
            html_files = sorted(RELATORIOS_DIR.glob("*.html"),
                                key=lambda p: p.stat().st_mtime, reverse=True)
            json_files = sorted(RELATORIOS_DIR.glob("*.json"),
                                key=lambda p: p.stat().st_mtime, reverse=True)
            if html_files:
                zf.write(html_files[0], arcname=f"relatorio_exemplo/{html_files[0].name}")
                print(f"  + relatorio_exemplo/{html_files[0].name}")
            if json_files:
                zf.write(json_files[0], arcname=f"relatorio_exemplo/{json_files[0].name}")
                print(f"  + relatorio_exemplo/{json_files[0].name}")

        # 5) LEIA_ME_PACOTE.txt
        zf.writestr("LEIA_ME_PACOTE.txt", LEIA_ME_PACOTE)
        print("  + LEIA_ME_PACOTE.txt")

    size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    print(f"\nOK · {ZIP_PATH}  ({size_mb:.1f} MB)")
    print(f"     gerado em {datetime.now().strftime('%Y-%m-%d %H:%M')}")


if __name__ == "__main__":
    main()
