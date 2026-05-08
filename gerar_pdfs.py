# -*- coding: utf-8 -*-
"""
gerar_pdfs.py — Gera PDFs do pacote de entrega Predfy à banca HyperCopa DISEC 2026.

Pipeline:
  1. Para cada Markdown em docs/*.md (e README.md):
       - Extrai blocos ```mermaid``` e converte para <div class="mermaid">.
       - Compila o Markdown em HTML.
       - Aplica o template assets/pdf_template.html (CSS BB + Mermaid CDN).
       - Renderiza com Playwright (Chromium) → docs/pdf/<nome>.pdf.
  2. Renderiza cada bloco Mermaid como PDF standalone via `mmdc` →
     docs/pdf/diagramas/NN_<titulo>.pdf.
  3. Renderiza docs/PREDFY_OVERVIEW.html → docs/pdf/PREDFY_OVERVIEW.pdf via Playwright.

Pré-requisitos:
  - Python 3.10+
  - pip install markdown playwright
  - playwright install chromium  (já feito por capturar_screenshots.py)
  - npm i -g @mermaid-js/mermaid-cli

Uso:
  python gerar_pdfs.py
"""

from __future__ import annotations

import asyncio
import re
import shutil
import subprocess
import sys
from pathlib import Path

import markdown
from playwright.async_api import async_playwright


REPO_ROOT = Path(__file__).resolve().parent
DOCS_DIR = REPO_ROOT / "docs"
PDF_DIR = DOCS_DIR / "pdf"
DIAGRAMAS_DIR = PDF_DIR / "diagramas"
TEMPLATE_PATH = REPO_ROOT / "assets" / "pdf_template.html"

# Lista ordenada dos arquivos Markdown que viram PDF.
# (file_path_relativa_ao_repo, titulo_no_header_pdf, subtitulo_no_header_pdf)
MD_DOCS = [
    ("README.md",
     "README · Predfy",
     "Visão geral do repositório e quickstart"),
    ("docs/COMO_AVALIAR.md",
     "Como Avaliar · Roteiro para a banca",
     "Caminho C (Modo Demonstração offline) — sem chave OpenAI, sem rede"),
    ("docs/MVP_CANVAS.md",
     "MVP Canvas · Predfy",
     "HyperCopa DISEC 2026 · Banco do Brasil"),
    ("docs/RELATORIO_SOLUCAO.md",
     "Relatório da Solução · Predfy",
     "Documento técnico estendido — banca avaliadora"),
    ("docs/ENTREGA_TIME1_MODELOS.md",
     "Entrega Time 1 · Modelos Analíticos",
     "Capitão João 23 · Francisco · Rosali · Silvia"),
    ("docs/ENTREGA_TIME2_AGENTE.md",
     "Entrega Time 2 · Agente IA + RPA",
     "Capitão Bento 14 · Felipe · Amélia · Vânia · Rafael"),
    ("docs/FLUXOGRAMA.md",
     "Fluxograma · Predfy",
     "Caminhos A, B e C — diagramas Mermaid"),
    ("docs/DIAGRAMAS.md",
     "Diagramas · Predfy",
     "5 visões — jornada, privacidade, sequência, tecnologias, produção"),
    ("docs/COPILOT_STUDIO_GUIA.md",
     "Guia Copilot Studio · Predfy",
     "Publicar o Agente Predfy no Microsoft Copilot do Teams"),
    ("docs/ACESSO.md",
     "Acesso e Instalação · Predfy",
     "Pré-requisitos e quickstart detalhado"),
]


# -----------------------------------------------------------------------------#
# Mermaid extraction
# -----------------------------------------------------------------------------#

MERMAID_BLOCK_RE = re.compile(
    r"```mermaid\s*\n(.*?)\n```", re.DOTALL
)


def extrair_mermaid_blocks(md_text: str):
    """Devolve lista de (codigo_mermaid, titulo_aproximado).

    O título é inferido pelo último heading `##` antes do bloco
    ou, na falta dele, pelo primeiro nó do diagrama.
    """
    blocos = []
    pos = 0
    for m in MERMAID_BLOCK_RE.finditer(md_text):
        antes = md_text[pos:m.start()]
        # último ## ou ### antes do bloco
        headings = re.findall(r"^(?:##|###)\s+(.+)$", antes, re.MULTILINE)
        titulo = headings[-1].strip() if headings else ""
        if not titulo:
            titulo = "diagrama"
        blocos.append((m.group(1).strip(), titulo))
        pos = m.end()
    return blocos


def slugify(text: str) -> str:
    """Normaliza um título para nome de arquivo."""
    out = text.lower()
    out = re.sub(r"[áàâã]", "a", out)
    out = re.sub(r"[éèê]", "e", out)
    out = re.sub(r"[íì]", "i", out)
    out = re.sub(r"[óòôõ]", "o", out)
    out = re.sub(r"[úù]", "u", out)
    out = re.sub(r"ç", "c", out)
    out = re.sub(r"[^a-z0-9]+", "_", out)
    out = out.strip("_")
    return out[:50] or "diagrama"


def renderizar_mermaid_para_svg(code: str, mmdc_path: str = "mmdc") -> str:
    """Chama mmdc para converter codigo Mermaid em SVG inline.
    Retorna o conteudo SVG (string) ou um <pre> de fallback em caso de falha.
    """
    import tempfile, os
    tmpdir = Path(tempfile.mkdtemp(prefix="mermaid_svg_"))
    try:
        mmd = tmpdir / "diagram.mmd"
        svg = tmpdir / "diagram.svg"
        cfg = tmpdir / "config.json"
        mmd.write_text(code, encoding="utf-8")
        cfg.write_text(MMDC_CONFIG_JSON, encoding="utf-8")
        cmd = [
            mmdc_path,
            "-i", str(mmd),
            "-o", str(svg),
            "-c", str(cfg),
            "-b", "white",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode != 0 or not svg.exists():
            print(f"    [mermaid->svg] FALHA: {result.stderr[:200]}")
            return f"<pre><code>{code}</code></pre>"
        svg_text = svg.read_text(encoding="utf-8")
        # Remove declaracao XML (problema dentro de HTML inline)
        svg_text = re.sub(r"<\?xml[^>]*\?>", "", svg_text).strip()
        return f'<div class="mermaid-rendered">{svg_text}</div>'
    finally:
        try:
            for f in tmpdir.iterdir():
                f.unlink(missing_ok=True)
            tmpdir.rmdir()
        except Exception:
            pass


def md_para_html_com_mermaid(md_text: str) -> str:
    """Converte Markdown em HTML, pre-renderizando blocos Mermaid em SVG via mmdc."""
    placeholder_blocks = []

    def replace_mermaid(match):
        idx = len(placeholder_blocks)
        placeholder_blocks.append(match.group(1).strip())
        return f"\n\n@@MERMAID_PLACEHOLDER_{idx}@@\n\n"

    text = MERMAID_BLOCK_RE.sub(replace_mermaid, md_text)

    html = markdown.markdown(
        text,
        extensions=[
            "fenced_code",
            "tables",
            "toc",
            "sane_lists",
            "attr_list",
        ],
        output_format="html5",
    )

    for i, code in enumerate(placeholder_blocks):
        svg_html = renderizar_mermaid_para_svg(code)
        # markdown lib costuma envelopar o placeholder em <p> — remover
        html = re.sub(
            rf"<p>\s*@@MERMAID_PLACEHOLDER_{i}@@\s*</p>",
            svg_html,
            html,
        )
        html = html.replace(f"@@MERMAID_PLACEHOLDER_{i}@@", svg_html)

    return html


def aplicar_template(template: str, *, title: str, header: str, sub: str, content: str) -> str:
    return (template
            .replace("__TITLE__", title)
            .replace("__HEADER_TITLE__", header)
            .replace("__HEADER_SUB__", sub)
            .replace("__CONTENT__", content))


# -----------------------------------------------------------------------------#
# Mermaid → standalone PDFs via mmdc
# -----------------------------------------------------------------------------#

MMDC_CONFIG_JSON = """{
  "theme": "default",
  "themeVariables": {
    "primaryColor": "#FAE128",
    "primaryTextColor": "#1F1F1F",
    "primaryBorderColor": "#003DA5",
    "lineColor": "#003DA5",
    "secondaryColor": "#003DA5",
    "tertiaryColor": "#F7F8FA",
    "fontFamily": "IBM Plex Sans, Segoe UI, Arial, sans-serif"
  },
  "flowchart": { "htmlLabels": true, "curve": "basis" }
}
"""


def renderizar_mermaid_standalone(blocos, mmdc_path: str = "mmdc"):
    """Para cada bloco mermaid, gera um PDF standalone em docs/pdf/diagramas/.
    Limpa PDFs antigos antes (para que renumeração não deixe órfãos)."""
    DIAGRAMAS_DIR.mkdir(parents=True, exist_ok=True)
    for stale in DIAGRAMAS_DIR.glob("*.pdf"):
        stale.unlink(missing_ok=True)
    for stale in DIAGRAMAS_DIR.glob("*.mmd"):
        stale.unlink(missing_ok=True)

    config_file = DIAGRAMAS_DIR / "_mermaid_config.json"
    config_file.write_text(MMDC_CONFIG_JSON, encoding="utf-8")

    contador = 1
    nomes_gerados = []
    for code, titulo in blocos:
        nome = f"{contador:02d}_{slugify(titulo)}"
        contador += 1
        mmd_file = DIAGRAMAS_DIR / f"{nome}.mmd"
        pdf_file = DIAGRAMAS_DIR / f"{nome}.pdf"

        mmd_file.write_text(code, encoding="utf-8")

        cmd = [
            mmdc_path,
            "-i", str(mmd_file),
            "-o", str(pdf_file),
            "-c", str(config_file),
            "--pdfFit",
            "-b", "white",
        ]
        print(f"  [mmdc] {nome}.pdf")
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, shell=True)
            nomes_gerados.append(pdf_file.name)
        except subprocess.CalledProcessError as e:
            print(f"    ERRO: {e.stderr}")
        finally:
            mmd_file.unlink(missing_ok=True)

    config_file.unlink(missing_ok=True)
    return nomes_gerados


# -----------------------------------------------------------------------------#
# Markdown → PDF via Playwright
# -----------------------------------------------------------------------------#

async def renderizar_md_para_pdf(page, md_path: Path, pdf_path: Path,
                                 *, title: str, header: str, sub: str,
                                 template: str):
    md_text = md_path.read_text(encoding="utf-8")
    content_html = md_para_html_com_mermaid(md_text)
    html_full = aplicar_template(template,
                                 title=title, header=header, sub=sub,
                                 content=content_html)

    # Salvar HTML temporário para que o navegador resolva URLs do CDN
    tmp_html = pdf_path.with_suffix(".tmp.html")
    tmp_html.write_text(html_full, encoding="utf-8")

    await page.goto(tmp_html.as_uri(), wait_until="networkidle")
    # Aguardar Mermaid renderizar (ele substitui os <div class="mermaid">)
    try:
        await page.wait_for_function(
            """() => {
                const ds = document.querySelectorAll('div.mermaid');
                if (ds.length === 0) return true;
                return Array.from(ds).every(d =>
                    d.querySelector('svg') || d.dataset.processed === 'true');
            }""",
            timeout=20000,
        )
    except Exception:
        # Sem mermaid ou demora — segue
        pass

    # Pequena espera adicional para garantir layout estável
    await page.wait_for_timeout(500)

    await page.pdf(
        path=str(pdf_path),
        format="A4",
        margin={"top": "22mm", "bottom": "24mm", "left": "18mm", "right": "18mm"},
        print_background=True,
        prefer_css_page_size=True,
    )

    tmp_html.unlink(missing_ok=True)


async def renderizar_html_para_pdf(page, html_path: Path, pdf_path: Path):
    await page.goto(html_path.as_uri(), wait_until="networkidle")
    await page.wait_for_timeout(500)
    await page.pdf(
        path=str(pdf_path),
        format="A4",
        margin={"top": "16mm", "bottom": "16mm", "left": "12mm", "right": "12mm"},
        print_background=True,
    )


# -----------------------------------------------------------------------------#
# Main
# -----------------------------------------------------------------------------#

async def main():
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    DIAGRAMAS_DIR.mkdir(parents=True, exist_ok=True)
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Coletar blocos mermaid de FLUXOGRAMA + DIAGRAMAS
    print("[1/3] Renderizando diagramas Mermaid standalone via mmdc...")
    blocos_total = []
    for arquivo in ["docs/FLUXOGRAMA.md", "docs/DIAGRAMAS.md"]:
        path = REPO_ROOT / arquivo
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        blocos = extrair_mermaid_blocks(text)
        prefix = "fluxograma" if "FLUXOGRAMA" in arquivo else "diagrama"
        for code, titulo in blocos:
            blocos_total.append((code, f"{prefix}_{titulo}"))
    nomes = renderizar_mermaid_standalone(blocos_total)
    print(f"  -> {len(nomes)} PDFs em docs/pdf/diagramas/")

    print("\n[2/3] Renderizando .md → .pdf via Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={"width": 1200, "height": 1600})
        page = await context.new_page()

        for rel_path, header_title, header_sub in MD_DOCS:
            src = REPO_ROOT / rel_path
            if not src.exists():
                print(f"  [WARN] ausente: {rel_path}")
                continue
            nome_pdf = Path(rel_path).stem + ".pdf"
            dst = PDF_DIR / nome_pdf
            print(f"  [pw] {rel_path} -> docs/pdf/{nome_pdf}")
            try:
                await renderizar_md_para_pdf(
                    page, src, dst,
                    title=header_title,
                    header=header_title,
                    sub=header_sub,
                    template=template,
                )
            except Exception as e:
                print(f"    ERRO: {e}")

        # PREDFY_OVERVIEW.html (já tem CSS próprio)
        html_in = DOCS_DIR / "PREDFY_OVERVIEW.html"
        if html_in.exists():
            html_pdf = PDF_DIR / "PREDFY_OVERVIEW.pdf"
            print(f"  [pw] PREDFY_OVERVIEW.html -> docs/pdf/PREDFY_OVERVIEW.pdf")
            await renderizar_html_para_pdf(page, html_in, html_pdf)

        await browser.close()

    print("\n[3/3] Gerando docs/pdf/INDEX.md (sumário do pacote)...")
    gerar_index_md()

    print("\nOK · PDFs gerados em docs/pdf/")
    print("    Use gerar_zipao_banca.py para empacotar tudo em entregas/Predfy_Banca_Entrega.zip")


def gerar_index_md():
    """Cria um INDEX.md em docs/pdf/ explicando o que tem em cada PDF."""
    pdfs = sorted(p.name for p in PDF_DIR.glob("*.pdf"))
    diagramas = sorted(p.name for p in DIAGRAMAS_DIR.glob("*.pdf"))

    linhas = [
        "# Pacote PDF · Predfy — HyperCopa DISEC 2026",
        "",
        "Conteúdo desta pasta gerado por `gerar_pdfs.py` a partir dos `.md` de `docs/`.",
        "",
        "## Documentos principais",
        "",
    ]
    for nome in pdfs:
        linhas.append(f"- `{nome}`")
    linhas += ["", "## Diagramas standalone (`diagramas/`)", ""]
    for nome in diagramas:
        linhas.append(f"- `diagramas/{nome}`")
    linhas += [
        "",
        "---",
        "",
        "*Pacote pronto para anexar à entrega oficial à banca · 07/05/2026*",
    ]
    (PDF_DIR / "INDEX.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if not TEMPLATE_PATH.exists():
        print(f"Template HTML ausente: {TEMPLATE_PATH}", file=sys.stderr)
        sys.exit(1)
    if not shutil.which("mmdc") and not shutil.which("mmdc.cmd"):
        print("Aviso: 'mmdc' não encontrado no PATH. Instale com:", file=sys.stderr)
        print("  npm i -g @mermaid-js/mermaid-cli", file=sys.stderr)
    asyncio.run(main())
