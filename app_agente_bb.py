"""
Agente Preparador BB + Modelo Analitico — app Streamlit standalone.

Identidade visual Banco do Brasil (paleta amarelo/azul, tipografia humanista).
Jornada unica:
    1. usuario sobe CSVs recebidos da area
    2. conversa com o agente (OpenAI function calling)
    3. agente entrega CSV final pronto para H2O AutoML
    4. usuario clica em "Treinar modelo" e ve o relatorio analitico final

Execucao:
    streamlit run app_agente_bb.py
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# ----------------------------------------------------------------------------
# Identidade visual BB
# ----------------------------------------------------------------------------
BB_AMARELO = "#FAE128"
BB_AZUL = "#003DA5"
BB_AZUL_ESCURO = "#002D72"
BB_CINZA = "#5C6670"
BB_FUNDO = "#FFFFFF"
BB_FUNDO_SUAVE = "#F7F8FA"
BB_TEXTO = "#1F1F1F"

# Fonte web fallback (humanista, semelhante a BB Texto). Se voce tiver os
# arquivos oficiais (BB Texto, BB Titulos), troque a regra @font-face abaixo.
FONT_FAMILY = "'IBM Plex Sans', 'Segoe UI', sans-serif"

st.set_page_config(
    page_title="Agente Preparador BB",
    page_icon="🟡",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

/* Forca tema light com fundo branco em toda a pagina */
html, body, .stApp, [data-testid="stAppViewContainer"], .main, .block-container {{
    background-color: {BB_FUNDO} !important;
    color: {BB_TEXTO} !important;
}}
html, body, [class*="css"], p, span, div, label, li {{
    font-family: {FONT_FAMILY} !important;
}}
p, span, div, label, li {{
    color: {BB_TEXTO};
}}

/* CRITICO — preserva a fonte de icones Material do Streamlit. Sem isso a regra
   acima vira icones em texto literal: 'arrow_right', 'upload', 'close' etc. */
[data-testid="stIconMaterial"],
.material-symbols-outlined,
.material-symbols-rounded,
.material-icons,
[class*="material-symbols"],
[class*="material-icons"] {{
    font-family: "Material Symbols Outlined", "Material Symbols Rounded",
                 "Material Icons" !important;
    font-feature-settings: normal !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    word-wrap: normal !important;
    white-space: nowrap !important;
    direction: ltr !important;
    -webkit-font-feature-settings: 'liga' !important;
    font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}}

/* Header BB */
.bb-header {{
    background: linear-gradient(180deg, {BB_AZUL} 0%, {BB_AZUL_ESCURO} 100%);
    color: white;
    padding: 1.2rem 1.6rem;
    border-radius: 6px;
    border-top: 6px solid {BB_AMARELO};
    margin-bottom: 1.2rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
}}
.bb-header h1 {{
    color: white !important;
    margin: 0;
    font-size: 1.7rem;
    font-weight: 700;
    letter-spacing: -0.01em;
}}
.bb-header .bb-sub {{
    color: {BB_AMARELO};
    font-size: 0.95rem;
    margin-top: 0.25rem;
    font-weight: 500;
}}
.bb-header .bb-tag {{
    display: inline-block;
    background: {BB_AMARELO};
    color: {BB_AZUL_ESCURO};
    padding: 0.15rem 0.7rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    margin-top: 0.5rem;
}}

/* Botao primario BB (amarelo com texto azul) */
.stButton > button[kind="primary"], .stDownloadButton > button {{
    background: {BB_AMARELO} !important;
    color: {BB_AZUL_ESCURO} !important;
    border: 1px solid {BB_AMARELO} !important;
    font-weight: 700 !important;
    border-radius: 4px !important;
}}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button:hover {{
    background: #FFD700 !important;
    border-color: #FFD700 !important;
    color: {BB_AZUL_ESCURO} !important;
}}

/* Botao secundario (outline azul) */
.stButton > button:not([kind="primary"]) {{
    border: 1.5px solid {BB_AZUL} !important;
    color: {BB_AZUL} !important;
    background: white !important;
    font-weight: 600 !important;
    border-radius: 4px !important;
}}
.stButton > button:not([kind="primary"]):hover {{
    background: {BB_FUNDO_SUAVE} !important;
    color: {BB_AZUL_ESCURO} !important;
    border-color: {BB_AZUL_ESCURO} !important;
}}

/* Chat */
.stChatMessage {{
    background: {BB_FUNDO_SUAVE} !important;
    border: 1px solid #E5E7EB;
    border-left: 3px solid {BB_AMARELO};
    border-radius: 4px;
    padding: 0.8rem 1rem !important;
    color: {BB_TEXTO} !important;
}}
.stChatMessage [data-testid="stMarkdownContainer"] p {{
    color: {BB_TEXTO} !important;
}}

/* Caixa de chat input */
[data-testid="stChatInput"] textarea {{
    background: white !important;
    color: {BB_TEXTO} !important;
    border: 1.5px solid {BB_CINZA}55 !important;
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: {BB_FUNDO_SUAVE} !important;
    border-right: 2px solid {BB_AMARELO};
    padding-top: 0.5rem !important;
}}
section[data-testid="stSidebar"] > div {{
    padding-top: 0.5rem !important;
}}
section[data-testid="stSidebar"] * {{
    color: {BB_TEXTO};
}}
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{
    color: {BB_AZUL_ESCURO} !important;
    font-weight: 700;
    margin-top: 1rem !important;
    margin-bottom: 0.5rem !important;
}}
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
section[data-testid="stSidebar"] small {{
    color: {BB_CINZA} !important;
}}

/* Esconde a navegacao automatica de paginas no topo da sidebar
   (nao usamos multipage, era leftover do pages_legacy/) */
[data-testid="stSidebarNav"], [data-testid="stSidebarNavItems"] {{
    display: none !important;
}}
section[data-testid="stSidebar"] [data-testid="stSidebarNavSeparator"] {{
    display: none !important;
}}

/* Separadores mais discretos */
section[data-testid="stSidebar"] hr {{
    margin: 0.8rem 0 !important;
    border-color: {BB_AMARELO}66 !important;
}}

/* Expander BB-stylado */
section[data-testid="stSidebar"] [data-testid="stExpander"] {{
    border: 1px solid {BB_AZUL}33 !important;
    border-radius: 4px;
    background: white;
}}
section[data-testid="stSidebar"] [data-testid="stExpander"] summary {{
    color: {BB_AZUL} !important;
    font-weight: 600;
}}

/* File uploader */
[data-testid="stFileUploader"] section {{
    background: white !important;
    border: 2px dashed {BB_AZUL}66 !important;
    border-radius: 6px !important;
    padding: 0.8rem !important;
    min-height: 100px;
}}
[data-testid="stFileUploader"] section:hover {{
    border-color: {BB_AZUL} !important;
    background: {BB_FUNDO_SUAVE} !important;
}}
[data-testid="stFileUploader"] section button {{
    background: {BB_AZUL} !important;
    color: white !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
}}
[data-testid="stFileUploader"] section button:hover {{
    background: {BB_AZUL_ESCURO} !important;
}}
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploaderDropzoneInstructions"] {{
    color: {BB_CINZA} !important;
}}
[data-testid="stFileUploaderDropzoneInstructions"] span:first-child {{
    color: {BB_TEXTO} !important;
    font-weight: 500;
}}

/* Cards de metricas */
[data-testid="stMetricValue"] {{
    color: {BB_AZUL} !important;
    font-weight: 700;
}}
[data-testid="stMetricLabel"] {{
    color: {BB_CINZA} !important;
    font-weight: 600;
}}

/* Cabecalho de secao */
h1, h2, h3, h4 {{
    color: {BB_AZUL_ESCURO} !important;
}}
h2 {{
    border-bottom: 2px solid {BB_AMARELO};
    padding-bottom: 0.3rem;
    margin-top: 1.5rem;
}}

/* Inputs */
.stTextInput input, .stTextArea textarea {{
    background: white !important;
    color: {BB_TEXTO} !important;
    border: 1.5px solid {BB_CINZA}55 !important;
    border-radius: 4px !important;
}}
.stSelectbox > div > div {{
    background: white !important;
    color: {BB_TEXTO} !important;
    border-radius: 4px !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
    border-color: {BB_AZUL} !important;
    box-shadow: 0 0 0 1px {BB_AZUL}33 !important;
}}

/* Radio (escolha de caminho) */
[data-testid="stRadio"] label {{
    color: {BB_TEXTO} !important;
    font-weight: 500;
}}
[data-testid="stRadio"] [data-baseweb="radio"] {{
    color: {BB_TEXTO} !important;
}}

/* Slider */
[data-testid="stSlider"] [data-baseweb="slider"] div {{
    color: {BB_AZUL} !important;
}}

/* Caixas de info/success/warning/error */
.stAlert {{
    background: {BB_FUNDO_SUAVE} !important;
    border-left: 4px solid {BB_AZUL} !important;
    color: {BB_TEXTO} !important;
}}
.stAlert [data-testid="stMarkdownContainer"] p,
.stAlert [data-testid="stMarkdownContainer"] li {{
    color: {BB_TEXTO} !important;
}}

/* DataFrame */
[data-testid="stDataFrame"] {{
    border: 1px solid #E5E7EB !important;
    border-radius: 4px;
}}

/* Codigo (st.code) */
.stCodeBlock pre, [data-testid="stCodeBlock"] pre {{
    background: {BB_FUNDO_SUAVE} !important;
    color: {BB_TEXTO} !important;
    border: 1px solid #E5E7EB !important;
}}
.stCodeBlock code, [data-testid="stCodeBlock"] code {{
    color: {BB_TEXTO} !important;
}}

/* Hide streamlit branding */
#MainMenu, footer, header[data-testid="stHeader"] {{
    visibility: hidden;
    height: 0 !important;
}}
.stDeployButton {{ display: none !important; }}

/* === MODO RADIO ESTILIZADO COMO ABAS GRANDES === */
/* Identifica o radio horizontal do modo via container */
div[data-testid="stRadio"] > label {{
    display: none !important;  /* esconde o label "Modo" */
}}
/* Radios horizontais — caixinhas estilo aba */
.modo-tabs [data-testid="stRadio"] [role="radiogroup"] {{
    gap: 0 !important;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}}
.modo-tabs [data-testid="stRadio"] [role="radiogroup"] > label {{
    flex: 1;
    background: white;
    border: 2px solid {BB_AZUL}33;
    padding: 1rem 1.5rem !important;
    margin: 0 !important;
    cursor: pointer;
    transition: all 0.15s ease;
    text-align: center;
    font-weight: 500;
    color: {BB_TEXTO};
    border-right: none;
}}
.modo-tabs [data-testid="stRadio"] [role="radiogroup"] > label:last-child {{
    border-right: 2px solid {BB_AZUL}33;
    border-radius: 0 8px 8px 0;
}}
.modo-tabs [data-testid="stRadio"] [role="radiogroup"] > label:first-child {{
    border-radius: 8px 0 0 8px;
}}
.modo-tabs [data-testid="stRadio"] [role="radiogroup"] > label:hover {{
    background: {BB_FUNDO_SUAVE};
    border-color: {BB_AZUL};
}}
/* Item selecionado: amarelo BB com texto azul escuro */
.modo-tabs [data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) {{
    background: {BB_AMARELO} !important;
    border-color: {BB_AZUL_ESCURO} !important;
    color: {BB_AZUL_ESCURO} !important;
    font-weight: 700;
    box-shadow: 0 2px 6px rgba(0,61,165,0.2);
}}
/* Esconde a bolinha do radio dentro das abas */
.modo-tabs [data-testid="stRadio"] [role="radiogroup"] > label > div:first-child {{
    display: none !important;
}}

/* === CARD GENERICO === */
.bb-card {{
    background: white;
    border: 1px solid #E5E7EB;
    border-left: 4px solid {BB_AMARELO};
    border-radius: 6px;
    padding: 1rem 1.2rem;
    margin: 0.6rem 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}}
.bb-card-titulo {{
    color: {BB_AZUL_ESCURO};
    font-weight: 700;
    margin-bottom: 0.4rem;
    font-size: 1.05rem;
}}

/* === SEMAFORO BIG === */
.semaforo-box {{
    padding: 1.2rem;
    border-radius: 12px;
    color: white;
    text-align: center;
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    margin: 0.6rem 0;
}}

/* Remove a translucidez agressiva durante reruns — mantem so um spinner discreto */
.stApp [data-stale="true"] {{
    opacity: 1 !important;
    filter: none !important;
}}
[data-testid="stStatusWidget"] {{
    background: {BB_AMARELO} !important;
    color: {BB_AZUL_ESCURO} !important;
    border-radius: 4px;
    padding: 0.3rem 0.6rem !important;
    font-weight: 600;
}}
.stSpinner > div {{
    border-top-color: {BB_AZUL} !important;
    border-right-color: {BB_AMARELO} !important;
}}

/* Mensagem de carregamento suave dentro do app */
.stSpinner {{
    background: rgba(255, 255, 255, 0.85);
    padding: 1rem 1.5rem;
    border-left: 4px solid {BB_AMARELO};
    border-radius: 4px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
PROMPT_PATH = ROOT / "docs" / "agente" / "system_prompt.md"
TOOLS_PATH = ROOT / "docs" / "agente" / "tools_schema.json"
OUTPUT_DIR = ROOT / "dados_treino"
REPORT_DIR = ROOT / "relatorios"
MODELS_DIR = ROOT / "models"
OUTPUT_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)


def _slugify(s: str) -> str:
    import re as _re
    s = _re.sub(r"[^\w]+", "_", str(s).lower()).strip("_")
    return s or "modelo"

load_dotenv(ROOT / ".env")

MODELOS = {
    "Padrao (gpt-5.2)": "gpt-5.2",
    "Avancado (gpt-5.2-pro)": "gpt-5.2-pro",
    "Economico (gpt-5.2-mini)": "gpt-5.2-mini",
}
MAX_TURNS = 15
MAX_TOOL_ITERS = 8

# Bloco demo do Caminho B (Copilot Teams) — usado pelo botao "Demo Caminho B"
# da sidebar e pelo botao "Pre-preencher" dentro do textarea.
BLOCO_DEMO_COPILOT = """\
PERGUNTA: Estamos estimando o prazo corretamente? Esta EAP vai atrasar?
TARGET: vai_atrasar
TASK: classification
FEATURES_MANTER: modalidade,tipo_servico,unidade_demandante,valor_estimado,num_etapas,num_participantes,tem_intercorrencia,urgencia,complexidade,status,dt_abertura_ano,dt_abertura_mes,etapas_duracao_media,etapas_interrompidas
FILTRO: nenhum
JOINS: nenhum
TRATAMENTO_NULOS: usar como esta (H2O lida com NaN nativamente)
PASSO_A_PASSO_PANDAS: |
  eaps = dfs['demo_eaps_vai_atrasar.csv']
  cols = ['modalidade','tipo_servico','unidade_demandante','valor_estimado',
          'num_etapas','num_participantes','tem_intercorrencia','urgencia',
          'complexidade','status','dt_abertura_ano','dt_abertura_mes',
          'etapas_duracao_media','etapas_interrompidas','vai_atrasar']
  resultado = eaps[cols].copy()
"""

# ----------------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------------
ss = st.session_state
ss.setdefault("uploaded_dfs", {})
ss.setdefault("agent_dfs", {})
ss.setdefault("messages", [])
ss.setdefault("turn_count", 0)
ss.setdefault("final_csv_path", None)
ss.setdefault("final_meta", {})
ss.setdefault("modelo_label", list(MODELOS.keys())[0])
ss.setdefault("h2o_iniciado", False)
ss.setdefault("h2o_resultado", None)
ss.setdefault("caminho", "A")  # "A" = OpenAI direto / "B" = Copilot Teams / "C" = Modo demo
ss.setdefault("bloco_copilot", "")
ss.setdefault("training_log", "")

# Modo demonstracao (banca avaliadora — sem chave OpenAI, sem rede externa)
ss.setdefault("modo_demo", False)
ss.setdefault("demo_carregado", False)
ss.setdefault("demo_turn_idx", 0)
ss.setdefault("demo_script", None)
ss.setdefault("demo_finalizado", False)


# ----------------------------------------------------------------------------
# Tool handlers do agente
# ----------------------------------------------------------------------------
def _find_df(nome: str):
    if nome in ss.uploaded_dfs:
        return ss.uploaded_dfs[nome]
    if nome in ss.agent_dfs:
        return ss.agent_dfs[nome]
    return None


def tool_ler_schema(nome_arquivo: str) -> dict:
    df = _find_df(nome_arquivo)
    if df is None:
        return {"erro": f"arquivo '{nome_arquivo}' nao encontrado"}
    return {
        "nome": nome_arquivo,
        "linhas": int(len(df)),
        "colunas": {c: str(df[c].dtype) for c in df.columns},
    }


def _safe_str(val) -> str:
    """Converte qualquer valor pra string, lidando com bytes em latin-1."""
    if isinstance(val, bytes):
        try:
            return val.decode("utf-8")
        except UnicodeDecodeError:
            return val.decode("latin-1", errors="replace")
    if pd.isna(val):
        return ""
    return str(val)


def tool_ler_amostra(nome_arquivo: str, n: int = 5) -> dict:
    df = _find_df(nome_arquivo)
    if df is None:
        return {"erro": f"arquivo '{nome_arquivo}' nao encontrado"}
    n = max(1, min(int(n), 20))
    try:
        amostra_df = df.head(n).map(_safe_str)
    except AttributeError:
        # pandas < 2.1.0
        amostra_df = df.head(n).applymap(_safe_str)
    return {"nome": nome_arquivo, "amostra": amostra_df.to_dict(orient="records")}


def tool_executar_pandas(codigo: str) -> dict:
    dfs = {**ss.uploaded_dfs, **ss.agent_dfs}
    safe_builtins = {
        "len": len, "range": range, "list": list, "dict": dict, "set": set,
        "tuple": tuple, "str": str, "int": int, "float": float, "bool": bool,
        "print": print, "min": min, "max": max, "sum": sum, "abs": abs,
        "round": round, "sorted": sorted, "enumerate": enumerate, "zip": zip,
        "any": any, "all": all, "isinstance": isinstance, "type": type,
    }
    safe_globals = {"__builtins__": safe_builtins, "pd": pd, "np": np, "dfs": dfs}
    local_vars: dict = {}
    stdout_buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout_buf):
            exec(codigo, safe_globals, local_vars)
    except Exception as e:
        return {
            "ok": False,
            "erro": f"{type(e).__name__}: {e}",
            "stdout": stdout_buf.getvalue()[:2000],
        }
    resultado = local_vars.get("resultado")
    saida: dict = {"ok": True, "stdout": stdout_buf.getvalue()[:2000]}
    if isinstance(resultado, pd.DataFrame):
        df_id = f"df_{uuid.uuid4().hex[:8]}"
        ss.agent_dfs[df_id] = resultado
        saida.update({
            "df_id": df_id,
            "shape": list(resultado.shape),
            "colunas": list(resultado.columns),
        })
    elif isinstance(resultado, pd.Series):
        saida["resultado_serie"] = resultado.head(50).astype(str).to_dict()
    elif resultado is not None:
        saida["resultado_repr"] = str(resultado)[:2000]
    return saida


def tool_salvar_csv_final(
    df_id: str, nome_sugerido: str, pergunta: str = "",
    target: str = "", task: str = "",
) -> dict:
    df = ss.agent_dfs.get(df_id)
    if df is None:
        return {"erro": f"df_id '{df_id}' nao encontrado"}
    nome = nome_sugerido.strip().replace(" ", "_").replace("/", "_").replace("\\", "_")
    if not nome.endswith(".csv"):
        nome += ".csv"
    path = OUTPUT_DIR / nome
    df.to_csv(path, index=False)
    meta = {"pergunta": pergunta, "target": target, "task": task}
    path.with_suffix(".meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    ss.final_csv_path = path
    ss.final_meta = meta
    return {
        "arquivo": nome,
        "linhas": int(len(df)),
        "colunas": int(len(df.columns)),
    }


TOOL_HANDLERS = {
    "ler_schema": tool_ler_schema,
    "ler_amostra": tool_ler_amostra,
    "executar_pandas": tool_executar_pandas,
    "salvar_csv_final": tool_salvar_csv_final,
}


@st.cache_data
def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


@st.cache_data
def load_tools() -> list:
    return json.loads(TOOLS_PATH.read_text(encoding="utf-8"))["tools"]


# ----------------------------------------------------------------------------
# Modo demonstracao — pre-carregamento do cenario e player de turnos
# ----------------------------------------------------------------------------
DEMO_SCRIPT_PATH = ROOT / "docs" / "demo" / "script_turnos.json"
DEMO_CSV_PATH = ROOT / "dados_sinteticos" / "contratos.csv"


@st.cache_data
def load_demo_script() -> dict:
    """Carrega o script de turnos pre-gravado da banca."""
    return json.loads(DEMO_SCRIPT_PATH.read_text(encoding="utf-8"))


def carregar_csv_demo() -> bool:
    """Carrega o CSV demo na memoria do app sob nome amigavel.
    Retorna True se carregou com sucesso (ou ja estava carregado)."""
    script = load_demo_script()
    nome_amigavel = script["cenario"]["csv_nome_amigavel"]
    if nome_amigavel in ss.uploaded_dfs:
        return True
    if not DEMO_CSV_PATH.exists():
        return False
    df = pd.read_csv(DEMO_CSV_PATH)
    df.columns = [str(c).strip().lstrip("﻿") for c in df.columns]
    ss.uploaded_dfs[nome_amigavel] = df
    return True


def reset_demo() -> None:
    """Reinicia o player de turnos do modo demo."""
    ss.demo_turn_idx = 0
    ss.demo_finalizado = False
    ss.messages = []
    ss.turn_count = 0
    ss.final_csv_path = None
    ss.final_meta = {}
    ss.h2o_iniciado = False
    ss.h2o_resultado = None
    ss.agent_dfs = {}


def avancar_turno_demo() -> None:
    """Consome o proximo turno do script e atualiza ss.messages.
    Executa as tools de verdade quando o turno tem `tool_calls`."""
    if ss.demo_script is None:
        ss.demo_script = load_demo_script()
    turnos = ss.demo_script["turnos"]
    if ss.demo_turn_idx >= len(turnos):
        ss.demo_finalizado = True
        return

    turno = turnos[ss.demo_turn_idx]
    role = turno["role"]
    content = turno.get("content", "")
    tool_calls = turno.get("tool_calls", []) or []

    if role == "user":
        ss.messages.append({"role": "user", "content": content})
        ss.turn_count += 1
    elif role == "assistant":
        if tool_calls:
            # Adiciona a mensagem do assistente com tool_calls (formato OpenAI)
            assistant_msg: dict = {"role": "assistant", "content": content}
            assistant_msg["tool_calls"] = []
            for i, tc in enumerate(tool_calls):
                tc_id = f"demo_tc_{ss.demo_turn_idx}_{i}"
                assistant_msg["tool_calls"].append({
                    "id": tc_id,
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc.get("arguments", {}),
                                                ensure_ascii=False),
                    },
                })
            ss.messages.append(assistant_msg)

            # Executa cada tool de verdade
            for i, tc in enumerate(tool_calls):
                tc_id = f"demo_tc_{ss.demo_turn_idx}_{i}"
                nome = tc["name"]
                args = tc.get("arguments", {}) or {}
                handler = TOOL_HANDLERS.get(nome)
                if handler is None:
                    res = {"erro": f"tool '{nome}' nao existe"}
                else:
                    # Para salvar_csv_final no demo, fornecemos df_id automatico
                    # se nao foi passado: pega o ultimo dataframe gerado.
                    if nome == "salvar_csv_final" and "df_id" not in args:
                        ultimo_id = (sorted(ss.agent_dfs.keys())[-1]
                                     if ss.agent_dfs else None)
                        if ultimo_id:
                            args = {**args, "df_id": ultimo_id,
                                    "nome_sugerido": "demo_contratos_final"}
                    try:
                        res = handler(**args)
                    except Exception as e:
                        res = {"erro": f"{type(e).__name__}: {e}"}
                ss.messages.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "name": nome,
                    "content": json.dumps(res, ensure_ascii=False, default=str)[:6000],
                })
        else:
            ss.messages.append({"role": "assistant", "content": content})

    ss.demo_turn_idx += 1
    if ss.demo_turn_idx >= len(turnos):
        ss.demo_finalizado = True


def render_stepper(etapa_atual: int) -> str:
    """Renderiza HTML do stepper visual de 7 etapas (0..6).
    `etapa_atual` é o índice da etapa em destaque (0..6)."""
    etapas = [
        ("0", "Dados"),
        ("1", "Preparar"),
        ("2", "Treinar"),
        ("3", "Avaliar"),
        ("4", "Documentos"),
        ("5", "Interpretar"),
        ("6", "Evento real"),
    ]
    blocos = []
    for i, (n, label) in enumerate(etapas):
        if i < etapa_atual:
            cor_bg = BB_AZUL
            cor_fg = "#FFFFFF"
            simbolo = "✓"
        elif i == etapa_atual:
            cor_bg = BB_AMARELO
            cor_fg = BB_AZUL_ESCURO
            simbolo = n
        else:
            cor_bg = "#E5E7EA"
            cor_fg = BB_CINZA
            simbolo = n
        blocos.append(
            f"<div style='display:flex;flex-direction:column;align-items:center;flex:1;min-width:0;'>"
            f"<div style='width:36px;height:36px;border-radius:50%;background:{cor_bg};"
            f"color:{cor_fg};display:flex;align-items:center;justify-content:center;"
            f"font-weight:700;font-size:0.9rem;'>{simbolo}</div>"
            f"<div style='font-size:0.72rem;color:{cor_fg if i==etapa_atual else BB_CINZA};"
            f"margin-top:4px;text-align:center;font-weight:{'700' if i==etapa_atual else '500'};'>"
            f"{label}</div></div>"
        )
        if i < len(etapas) - 1:
            blocos.append(
                f"<div style='flex:0 0 18px;height:2px;background:"
                f"{BB_AZUL if i < etapa_atual else '#E5E7EA'};"
                f"margin-top:16px;'></div>"
            )
    return (
        "<div style='display:flex;align-items:flex-start;justify-content:space-between;"
        "padding:0.6rem 0.8rem;background:#F7F8FA;border-radius:6px;"
        "margin:0 0 1rem 0;border-left:4px solid " + BB_AMARELO + ";'>"
        + "".join(blocos) + "</div>"
    )


def etapa_atual_da_jornada() -> int:
    """Inferir em que etapa o usuario esta com base no estado da sessao."""
    if ss.h2o_resultado is not None:
        return 3  # ja treinou — pode ir para Avaliar/Documentos/Interpretar
    if ss.final_csv_path is not None:
        return 2  # CSV final pronto — pode treinar
    if ss.uploaded_dfs:
        return 1  # tem dados, agente preparando
    return 0  # sem dados ainda


# ----------------------------------------------------------------------------
# Header BB
# ----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="bb-header">
        <h1>Agente Preparador + Modelo Analitico</h1>
        <div class="bb-sub">DISEC · Banco do Brasil · Licitacao Eletronica</div>
        <span class="bb-tag">HyperCopa DISEC 2026</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Banner do modo demonstracao (so aparece quando ativo)
if ss.modo_demo:
    st.markdown(
        f"""
        <div style='background:{BB_AMARELO};border-left:6px solid {BB_AZUL_ESCURO};
        padding:0.8rem 1rem;border-radius:4px;margin-bottom:1rem;
        color:{BB_AZUL_ESCURO};font-size:0.92rem;'>
        <b>🎓 Modo demonstração da banca</b> — sem chave OpenAI, sem chamadas
        externas. Cenário pré-curado: <b>EAP DICOI / "vai atrasar?"</b>.
        Resultado idêntico em qualquer máquina (seed=42). Veja
        <code>docs/COMO_AVALIAR.md</code> para o roteiro completo.
        </div>
        """,
        unsafe_allow_html=True,
    )

# Stepper visual da jornada (7 etapas)
st.markdown(render_stepper(etapa_atual_da_jornada()), unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Sidebar — uploads + configuracao
# ----------------------------------------------------------------------------
with st.sidebar:
    # Toggle do modo demonstracao — antes de qualquer outra config
    novo_modo_demo = st.toggle(
        "🎓 Modo demonstração da banca",
        value=ss.modo_demo,
        help="Roda a jornada inteira sem chave OpenAI e sem chamadas externas. "
             "Carrega CSV pré-curado (contratos DICOI), executa o agente com "
             "respostas pré-gravadas, e gera predições com seed fixo. "
             "Resultado idêntico em qualquer máquina.",
    )
    if novo_modo_demo != ss.modo_demo:
        ss.modo_demo = novo_modo_demo
        if ss.modo_demo:
            ss.caminho = "C"
            reset_demo()
            carregar_csv_demo()
            ss.demo_carregado = True
        st.rerun()

    if ss.modo_demo:
        st.success(
            "Modo demo ativo. CSV carregado: "
            "**contratos_dicoi.csv** (1.959 linhas)"
        )
        if st.button("🔄 Reiniciar demo do início", use_container_width=True):
            reset_demo()
            ss.uploaded_dfs = {}
            carregar_csv_demo()
            st.rerun()

    st.markdown("---")
    st.markdown(f"### ⚙️ Configuracao")
    if ss.modelo_label not in MODELOS:
        ss.modelo_label = list(MODELOS.keys())[0]
    ss.modelo_label = st.selectbox(
        "Modelo do agente",
        list(MODELOS.keys()),
        index=list(MODELOS.keys()).index(ss.modelo_label),
        disabled=ss.modo_demo,
        help="Em modo demo, o agente roda offline com respostas pré-gravadas — "
             "este seletor não tem efeito." if ss.modo_demo else None,
    )

    st.markdown("---")
    st.markdown("### 📎 CSVs do extrato")

    def _detectar_sep(amostra: bytes) -> str:
        cand = {",": amostra.count(b","), ";": amostra.count(b";"),
                "\t": amostra.count(b"\t"), "|": amostra.count(b"|")}
        return max(cand, key=cand.get) or ","

    try:
        import pyarrow  # noqa: F401
        _HAS_PYARROW = True
    except ImportError:
        _HAS_PYARROW = False

    def _carregar_csv_bytes(buf, nome: str, nrows: int | None = None):
        """Le bytes em DataFrame com auto-deteccao."""
        head = buf.read(8192); buf.seek(0)
        sep = _detectar_sep(head)

        for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252", "iso-8859-1"):
            try:
                buf.seek(0)
                kwargs = dict(sep=sep, encoding=enc, low_memory=False,
                              on_bad_lines="skip")
                # pyarrow so e seguro com utf-8 puro. Se o encoding e latin-1
                # ou similar, pyarrow le os bytes como sao e quebra depois
                # quando astype(str) tenta decodificar.
                if _HAS_PYARROW and nrows is None and enc in ("utf-8", "utf-8-sig"):
                    try:
                        buf.seek(0)
                        df_loaded = pd.read_csv(buf, sep=sep,
                                                engine="pyarrow")
                    except Exception:
                        buf.seek(0)
                        df_loaded = pd.read_csv(buf, **kwargs)
                else:
                    if nrows:
                        kwargs["nrows"] = nrows
                    df_loaded = pd.read_csv(buf, **kwargs)

                df_loaded.columns = [str(c).strip().lstrip("﻿")
                                     for c in df_loaded.columns]

                # Deduplica nomes de colunas (CSVs as vezes vem com header
                # repetido — sem isso, df[c] retorna DataFrame em vez de Series)
                visto: dict = {}
                novos: list = []
                for nome in df_loaded.columns:
                    if nome in visto:
                        visto[nome] += 1
                        novos.append(f"{nome}_{visto[nome]}")
                    else:
                        visto[nome] = 1
                        novos.append(nome)
                df_loaded.columns = novos

                # Garante que colunas object sejam strings reais (pyarrow as
                # vezes deixa como bytes ou ArrowExtensionArray)
                for i, c in enumerate(df_loaded.columns):
                    col_serie = df_loaded.iloc[:, i]
                    if col_serie.dtype == "object":
                        try:
                            df_loaded.iloc[:, i] = col_serie.map(_safe_str)
                        except Exception:
                            pass
                return df_loaded
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
        return None

    ss.setdefault("loaded_via_path", set())

    st.caption(
        "💡 Para arquivos > 200MB use **Carregar de um caminho local** "
        "logo abaixo (mais rapido e sem memory error)."
    )
    # Opcao 1 — Upload
    uploads = st.file_uploader(
        "Suba o(s) CSV(s) que recebeu da area",
        type=["csv", "tsv", "txt"],
        accept_multiple_files=True,
        help="Recomendado para arquivos < 200MB. Acima disso, prefira o "
             "caminho local.",
    )
    upload_names = {up.name for up in uploads} if uploads else set()
    # Avisa se algum upload e gigante
    if uploads:
        for up in uploads:
            if up.size and up.size > 300 * 1024 * 1024:
                st.warning(
                    f"⚠ {up.name} tem {up.size/1024/1024:.0f}MB — pode dar "
                    f"MemoryError. Recomendo cancelar e usar o caminho local."
                )

    # Opcao 2 — Caminho local (pra arquivos grandes ou pastas protegidas)
    with st.expander("📂 Carregar de um caminho local (rapido pra arquivos grandes)"):
        path_input = st.text_input(
            "Caminho absoluto ou relativo ao app",
            placeholder=r'ex: dados reais/reais_eaps.csv',
        )
        max_linhas = st.number_input(
            "Limite de linhas (0 = ler tudo)",
            min_value=0, max_value=10_000_000, value=0, step=10_000,
            help="Use 50.000 ou 100.000 para iterar rapido em arquivos grandes. "
                 "Depois rode com 0 (tudo) para o treino final.",
        )
        st.caption(
            f"Engine: {'pyarrow (rapido)' if _HAS_PYARROW else 'pandas default'}"
        )
        if st.button("Carregar do caminho", use_container_width=True):
            from pathlib import Path as _P
            p = _P(path_input).resolve() if path_input else None
            if p and p.exists() and p.is_file():
                tam = p.stat().st_size / (1024 * 1024)
                with st.spinner(f"Lendo {p.name} ({tam:.0f} MB)..."):
                    nrows = int(max_linhas) if max_linhas > 0 else None
                    with open(p, "rb") as f:
                        df_path = _carregar_csv_bytes(f, p.name, nrows=nrows)
                if df_path is not None:
                    ss.uploaded_dfs[p.name] = df_path
                    ss.loaded_via_path.add(p.name)
                    nota = (f" (limitado a {nrows:,} linhas)" if nrows else "")
                    st.success(
                        f"✓ {p.name}: {len(df_path):,} linhas × "
                        f"{len(df_path.columns)} cols{nota}"
                    )
                else:
                    st.error(f"Erro ao ler {p.name}")
            else:
                st.error(f"Arquivo nao encontrado: {path_input}")

    # Opcao 3 — CSV de demonstracao (mesmo do notebook_h2o_agente_mvp.ipynb)
    with st.expander("🎁 Demo: 1.500 EAPs sinteticas (mesmo CSV do notebook)"):
        st.caption(
            "Pergunta: **Estamos estimando o prazo corretamente? "
            "Esta EAP vai atrasar?** · Target binario: `vai_atrasar`."
        )
        demo_csv = ROOT / "dados_treino" / "demo_eaps_vai_atrasar.csv"
        demo_meta = ROOT / "dados_treino" / "demo_eaps_vai_atrasar.meta.json"
        if not demo_csv.exists():
            st.warning(
                "Demo nao encontrada. Rode na raiz: "
                "`python gerar_demo_eaps.py`"
            )
        else:
            st.markdown("**Atalho A — direto para o H2O**")
            if st.button(
                "Carregar CSV de demo (pula o agente)",
                use_container_width=True,
                key="btn_demo_a",
                help="Sobe o CSV ja preparado e marca como final. "
                     "Vai direto para a Etapa 2 — Treinar.",
            ):
                df_demo = _carregar_csv_bytes(open(demo_csv, "rb"), demo_csv.name)
                if df_demo is not None:
                    ss.uploaded_dfs[demo_csv.name] = df_demo
                    ss.loaded_via_path.add(demo_csv.name)
                    # Marca tambem como CSV final ja preparado (atalho da banca)
                    ss.final_csv_path = demo_csv
                    if demo_meta.exists():
                        try:
                            ss.final_meta = json.loads(
                                demo_meta.read_text(encoding="utf-8")
                            )
                        except Exception:
                            ss.final_meta = {}
                    st.success(
                        f"✓ {demo_csv.name}: {len(df_demo):,} linhas. "
                        f"Pode rolar ate a Etapa 2 e clicar em Treinar."
                    )
                    st.rerun()

            st.markdown("**Atalho B — simula Copilot do Teams**")
            if st.button(
                "Carregar Demo Caminho B (CSV + bloco)",
                use_container_width=True,
                key="btn_demo_b",
                help="Carrega o CSV, troca para 'Caminho B' e ja preenche o "
                     "bloco do Copilot. Voce so precisa clicar em Processar.",
            ):
                df_demo = _carregar_csv_bytes(open(demo_csv, "rb"), demo_csv.name)
                if df_demo is not None:
                    ss.uploaded_dfs[demo_csv.name] = df_demo
                    ss.loaded_via_path.add(demo_csv.name)
                    ss.bloco_copilot = BLOCO_DEMO_COPILOT
                    ss.caminho = "B"
                    # Limpa CSV final (forca o usuario a clicar em Processar)
                    ss.final_csv_path = None
                    ss.final_meta = {}
                    st.success(
                        "✓ Demo Caminho B carregada. Role e clique "
                        "**Processar bloco e gerar CSV final**."
                    )
                    st.rerun()

    # Sincroniza: limpa arquivos que sumiram do uploader
    # (mantem os carregados via caminho local)
    for n in list(ss.uploaded_dfs.keys()):
        if n not in upload_names and n not in ss.loaded_via_path:
            del ss.uploaded_dfs[n]
    # Carrega novos uploads
    if uploads:
        for up in uploads:
            if up.name not in ss.uploaded_dfs:
                df_loaded = _carregar_csv_bytes(up, up.name)
                if df_loaded is not None:
                    ss.uploaded_dfs[up.name] = df_loaded
                else:
                    st.error(f"Erro ao ler {up.name}")

    if ss.uploaded_dfs:
        for nome, df in ss.uploaded_dfs.items():
            origem = "📂" if nome in ss.loaded_via_path else "⬆"
            st.caption(
                f"{origem} **{nome}** — {len(df):,} linhas × "
                f"{len(df.columns)} cols"
            )
    else:
        st.caption("_nenhum arquivo subido_")

    st.markdown("---")
    st.markdown("### 💾 CSV final")
    if ss.final_csv_path and ss.final_csv_path.exists():
        st.success(f"✓ {ss.final_csv_path.name}")
        st.download_button(
            "⬇️ Baixar CSV de treino",
            ss.final_csv_path.read_bytes(),
            file_name=ss.final_csv_path.name,
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.caption("_o agente ira gerar_")

    st.markdown("---")
    st.caption(f"Turno {ss.turn_count}/{MAX_TURNS}")
    if st.button("🔄 Reiniciar conversa", use_container_width=True):
        ss.messages = []
        ss.turn_count = 0
        ss.final_csv_path = None
        ss.final_meta = {}
        ss.agent_dfs = {}
        ss.h2o_iniciado = False
        ss.h2o_resultado = None
        ss.interpretacao = None
        ss.ultima_predicao = None
        ss.caso_sorteado_idx = None
        ss.valor_real_caso = None
        # Limpa inputs do formulario da Etapa 4
        for k in list(ss.keys()):
            if k.startswith("input_"):
                del ss[k]
        st.rerun()

    if st.button("🧹 Resetar cluster H2O", use_container_width=True,
                 help="Forca shutdown do cluster atual. Util quando o "
                      "treino falha por falta de memoria."):
        try:
            import h2o
            if h2o.cluster() and h2o.cluster().is_running():
                h2o.cluster().shutdown(prompt=False)
                st.success("Cluster H2O encerrado. Sera reiniciado no proximo treino.")
            else:
                st.info("Nenhum cluster H2O ativo.")
        except Exception as e:
            st.error(f"Erro: {e}")


# ----------------------------------------------------------------------------
# Modo: 2 demonstracoes
# ----------------------------------------------------------------------------
ss.setdefault("modo", "treinar")

st.markdown('<div class="modo-tabs">', unsafe_allow_html=True)
modo = st.radio(
    "Modo",
    options=["treinar", "consumir"],
    format_func=lambda x: {
        "treinar": "🎓  Demo 1  ·  Treinar modelo",
        "consumir": "🔮  Demo 2  ·  Consumir modelo treinado",
    }[x],
    horizontal=True,
    key="modo",
    label_visibility="collapsed",
)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("")

if modo == "consumir":
    # =================================================================
    # DEMO 2 — Consumir modelo treinado
    # =================================================================
    st.markdown(
        f"""
        <div style='background:linear-gradient(135deg, {BB_AZUL} 0%, {BB_AZUL_ESCURO} 100%);
                    color:white; padding:1.2rem 1.6rem; border-radius:8px;
                    border-top:5px solid {BB_AMARELO}; margin-bottom:1rem;'>
            <h2 style='color:white !important; margin:0; border:none; padding:0;'>
                🔮 Demo 2 · Cadastrar nova licitacao e prever
            </h2>
            <p style='color:{BB_AMARELO}; margin:0.3rem 0 0 0; font-size:0.95rem;'>
                Selecione um modelo treinado na Demo 1, preencha os dados de uma
                licitacao em planejamento e veja a previsao com semaforo de risco.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Lista modelos disponiveis (pastas em models/ com metadata.json)
    modelos_disponiveis = []
    if MODELS_DIR.exists():
        for d in sorted(MODELS_DIR.iterdir()):
            meta_p = d / "metadata.json"
            if d.is_dir() and meta_p.exists():
                try:
                    m = json.loads(meta_p.read_text(encoding="utf-8"))
                    modelos_disponiveis.append((d, m))
                except Exception:
                    continue

    if not modelos_disponiveis:
        st.markdown(
            f"""
            <div class='bb-card' style='border-left-color:{BB_AMARELO};
                        background:{BB_FUNDO_SUAVE}; text-align:center;
                        padding:2rem;'>
                <div style='font-size:3rem;'>🔒</div>
                <div class='bb-card-titulo'>Nenhum modelo treinado ainda</div>
                <p style='color:{BB_CINZA}; margin:0.4rem 0;'>
                    Volte na aba <b>🎓 Demo 1</b>, treine pelo menos um modelo,
                    e este menu se preenche automaticamente.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

    # Card 1 — Seletor de modelo
    st.markdown(
        '<div class="bb-card"><div class="bb-card-titulo">'
        '1. Modelo treinado disponivel'
        '</div>', unsafe_allow_html=True,
    )
    nomes_modelos = [
        f"{m['target']}  ·  {m['task']}  ·  treinado em {m['treinado_em'][:10]}"
        for _, m in modelos_disponiveis
    ]
    idx_modelo = st.selectbox(
        "Selecione o modelo",
        range(len(modelos_disponiveis)),
        format_func=lambda i: nomes_modelos[i],
        label_visibility="collapsed",
    )
    model_dir, mdl = modelos_disponiveis[idx_modelo]

    # Header do modelo
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Target", mdl["target"])
    mc2.metric("Tipo", mdl["task"])
    metric_principal = (
        ("AUC", mdl["metrics"].get("AUC"))
        if mdl["task"] == "classification" and "AUC" in mdl["metrics"]
        else ("R²", mdl["metrics"].get("R2"))
        if "R2" in mdl["metrics"]
        else (list(mdl["metrics"].keys())[0],
              list(mdl["metrics"].values())[0])
    )
    if metric_principal[1] is not None:
        mc3.metric(metric_principal[0], f"{metric_principal[1]:.4f}")
    mc4.metric("Treinado", mdl["treinado_em"][:10])

    st.caption(
        f"💼 Pergunta: _{mdl.get('pergunta', '—')}_  \n"
        f"📂 `models/{model_dir.name}/{mdl.get('saved_filename', '?')}` · "
        f"{mdl['n_train']:,} treino + {mdl['n_test']:,} teste"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Carrega exemplos pre-preenchidos do conjunto teste
    test_csv = model_dir / "test_sample.csv"
    exemplos_test = None
    if test_csv.exists():
        try:
            exemplos_test = pd.read_csv(test_csv)
        except Exception:
            pass

    ss.setdefault("consumir_input", {})
    ss.setdefault("consumir_resultado", None)

    # Card 2 — Pre-preenchimento
    st.markdown(
        '<div class="bb-card"><div class="bb-card-titulo">'
        '2. Pre-preenchimento (opcional)'
        '</div>', unsafe_allow_html=True,
    )

    # Botao para sortear caso real
    cs1, cs2 = st.columns([2, 1])
    with cs1:
        if exemplos_test is not None and len(exemplos_test) > 0:
            if st.button(
                "🎲 Pre-preencher com exemplo real do conjunto teste",
                use_container_width=True,
            ):
                row = exemplos_test.sample(1).iloc[0].to_dict()
                feature_info = mdl.get("feature_info", {})
                for feat in mdl["features"]:
                    info = feature_info.get(feat, {"type": "text"})
                    val = row.get(feat)
                    key = f"consumir_input_{feat}"
                    if info["type"] == "number":
                        try:
                            ss[key] = (float(val) if pd.notna(val)
                                       else info.get("median", 0.0))
                        except (ValueError, TypeError):
                            ss[key] = info.get("median", 0.0)
                    elif info["type"] == "select":
                        sval = "" if pd.isna(val) else str(val)
                        opcoes = info.get("values", [])
                        ss[key] = (sval if sval in opcoes
                                   else (opcoes[0] if opcoes else ""))
                    else:
                        ss[key] = "" if pd.isna(val) else str(val)
                ss.consumir_resultado = None
                # Guarda valor real do target
                if mdl["target"] in row:
                    ss.consumir_real = row[mdl["target"]]
                st.rerun()
    with cs2:
        if "consumir_real" in ss and ss.get("consumir_real") is not None:
            st.caption(f"Gabarito real: `{ss.consumir_real}`")
    st.markdown('</div>', unsafe_allow_html=True)

    # Card 3 — Formulario
    st.markdown(
        '<div class="bb-card"><div class="bb-card-titulo">'
        '3. Cadastro da nova licitacao'
        '</div>', unsafe_allow_html=True,
    )

    # Formulario dinamico — 3 colunas se tiver muitas features
    with st.form("consumir_form"):
        feature_info = mdl.get("feature_info", {})
        valores: dict = {}
        n_cols = 3 if len(mdl["features"]) > 8 else 2
        cols_form = st.columns(n_cols)
        for i, feat in enumerate(mdl["features"]):
            info = feature_info.get(feat, {"type": "text"})
            container = cols_form[i % n_cols]
            key = f"consumir_input_{feat}"
            if info["type"] == "number":
                if key not in ss:
                    ss[key] = info.get("median", 0.0)
                valores[feat] = container.number_input(
                    feat, key=key,
                    help=f"min={info.get('min', 0):.2f} · "
                         f"max={info.get('max', 0):.2f}",
                )
            elif info["type"] == "select":
                opcoes = info.get("values", [])
                if key not in ss or ss.get(key) not in opcoes:
                    ss[key] = opcoes[0] if opcoes else ""
                valores[feat] = container.selectbox(feat, opcoes, key=key)
            else:
                if key not in ss:
                    ss[key] = ""
                valores[feat] = container.text_input(feat, key=key)

        prever_btn = st.form_submit_button(
            "🚀 Prever",
            type="primary",
            use_container_width=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

    if prever_btn:
        try:
            import h2o
            if not h2o.cluster() or not h2o.cluster().is_running():
                h2o.init(max_mem_size="4G", nthreads=-1)
            saved_fn = mdl.get("saved_filename")
            if not saved_fn:
                st.error("Modelo nao foi salvo em disco. Retreine na Demo 1.")
                st.stop()
            model_path = model_dir / saved_fn
            leader = h2o.load_model(str(model_path))
            df_in = pd.DataFrame([valores])
            hf = h2o.H2OFrame(df_in)
            pred = leader.predict(hf).as_data_frame(use_multi_thread=True)

            if mdl["task"] == "classification":
                classe = str(pred["predict"].iloc[0])
                prob_cols = [c for c in pred.columns if c != "predict"]
                prob = (float(pred[prob_cols[-1]].iloc[0])
                        if len(prob_cols) >= 2 else None)
                if prob is None:
                    sem, cor, acao = "—", "#5C6670", "Sem probabilidade"
                elif prob < 0.10:
                    sem, cor = "Verde", "#1f9e54"
                    acao = "Risco baixo — fluxo padrao."
                elif prob < 0.25:
                    sem, cor = "Amarelo", "#e8a317"
                    acao = ("Risco moderado — checkpoint extra recomendado.")
                else:
                    sem, cor = "Vermelho", "#cf2a2a"
                    acao = ("Risco alto — revisar TR e governanca antes "
                            "de publicar.")
                ss.consumir_resultado = {
                    "tipo": "classification",
                    "classe": classe, "prob": prob,
                    "semaforo": sem, "cor": cor, "acao": acao,
                    "real": ss.get("consumir_real"),
                }
            else:
                valor = float(pred["predict"].iloc[0])
                rmse = mdl["metrics"].get("RMSE")
                ss.consumir_resultado = {
                    "tipo": "regression",
                    "valor": valor, "rmse": rmse,
                    "real": ss.get("consumir_real"),
                }
            st.rerun()
        except Exception as e:
            st.error(f"Erro na predicao: {type(e).__name__}: {e}")

    # Card 4 — Resultado
    if ss.get("consumir_resultado"):
        cr = ss.consumir_resultado
        st.markdown(
            '<div class="bb-card"><div class="bb-card-titulo">'
            '4. Previsao imediata'
            '</div>', unsafe_allow_html=True,
        )
        if cr["tipo"] == "classification":
            rc1, rc2 = st.columns([1, 2])
            with rc1:
                if cr["prob"] is not None:
                    st.metric("Probabilidade", f"{cr['prob']*100:.1f}%")
                st.metric("Classe prevista", cr["classe"])
            with rc2:
                st.markdown(
                    f"<div class='semaforo-box' style='background:{cr['cor']}'>"
                    f"{cr['semaforo']}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"**Acao sugerida:** {cr['acao']}")
            if cr["real"] is not None and not pd.isna(cr["real"]):
                acertou = (str(cr["classe"]).lower() == str(cr["real"]).lower())
                badge_color = "#1f9e54" if acertou else "#cf2a2a"
                st.markdown(
                    f"<div style='margin-top:0.6rem; padding:0.5rem 0.8rem; "
                    f"border-radius:4px; background:{badge_color}22; "
                    f"border-left:3px solid {badge_color}; color:{BB_TEXTO};'>"
                    f"<b>📌 Gabarito (caso de teste):</b> "
                    f"<code>{cr['real']}</code> · "
                    f"{'✓ acertou' if acertou else '✗ errou'}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            rc1, rc2, rc3 = st.columns(3)
            rc1.metric(f"Previsto ({mdl['target']})", f"{cr['valor']:.2f}")
            if cr["rmse"]:
                rc2.metric("Erro tipico", f"±{cr['rmse']:.2f}")
            if cr["real"] is not None and not pd.isna(cr["real"]):
                real = float(cr["real"])
                rc3.metric("Gabarito", f"{real:.2f}",
                           delta=f"{cr['valor']-real:+.2f}")

        with st.expander("📋 Valores enviados ao modelo"):
            st.json({k.replace("consumir_input_", ""): v
                     for k, v in ss.items()
                     if k.startswith("consumir_input_")})
        st.markdown('</div>', unsafe_allow_html=True)

    # Encerra a renderizacao da Demo 2 aqui — nao executa o resto do app
    st.stop()


# ============================================================================
# DEMO 1 — Treinar modelo (codigo abaixo so executa quando modo == 'treinar')
# ============================================================================
st.markdown("## 🤖 Demo 1 — Etapa 1: Conversa com o agente preparador")

if ss.modo_demo:
    # Em modo demo, fixamos o Caminho C
    ss.caminho = "C"
    caminho_label = "C"
    st.info(
        "**Caminho C — Modo demonstração offline.** O agente conduz a "
        "preparação com turnos pré-gravados, executando as ferramentas reais "
        "em cima do CSV pré-carregado. Avance turno a turno com o botão "
        "**Próximo turno** abaixo."
    )
else:
    caminho_label = st.radio(
        "Como voce quer conversar com o agente?",
        options=["A", "B"],
        format_func=lambda x: {
            "A": "Caminho A — OpenAI direto (chat embutido neste app)",
            "B": "Caminho B — Copilot do Teams (colar bloco aqui)",
        }[x],
        horizontal=True,
        key="caminho",
    )

if caminho_label == "A":
    st.markdown(
        "<p style='color:#5C6670'>Suba os CSVs na barra lateral e descreva sua "
        "pergunta preditiva. O agente cuida do resto e devolve um CSV pronto.</p>",
        unsafe_allow_html=True,
    )
elif caminho_label == "B":
    st.info(
        "**Como usar o Caminho B:**\n\n"
        "1. Abra o agente **Preparador BB** no Microsoft Copilot do Teams.\n"
        "2. Anexe seu CSV ou cole uma amostra.\n"
        "3. Conte a pergunta preditiva.\n"
        "4. O Copilot devolve um bloco com `PERGUNTA / TARGET / TASK / "
        "FEATURES_MANTER / FILTRO / JOINS / PASSO_A_PASSO_PANDAS`.\n"
        "5. Suba o CSV correspondente na barra lateral e cole o bloco abaixo."
    )

# ===== CAMINHO C — Modo demonstracao offline (player de turnos) =====
if caminho_label == "C":
    if ss.demo_script is None:
        ss.demo_script = load_demo_script()
    if not ss.demo_carregado:
        carregar_csv_demo()
        ss.demo_carregado = True

    cen = ss.demo_script["cenario"]
    st.markdown(
        f"<div style='background:{BB_FUNDO_SUAVE};border-left:4px solid {BB_AMARELO};"
        f"padding:0.6rem 0.9rem;border-radius:4px;margin-bottom:0.8rem;'>"
        f"<b>Cenário:</b> {cen['titulo']}<br/>"
        f"<span style='color:{BB_CINZA};font-size:0.9rem;'>"
        f"{cen['narrativa_curta']}</span></div>",
        unsafe_allow_html=True,
    )

    # Mostra todas as mensagens ja consumidas do script
    for msg in ss.messages:
        role = msg.get("role")
        content = msg.get("content") or ""
        if role == "user" and content.strip():
            with st.chat_message("user", avatar="👤"):
                st.markdown(content)
        elif role == "assistant" and content.strip():
            with st.chat_message("assistant", avatar="🟡"):
                st.markdown(content)
        elif role == "tool":
            # Mostra resultado da ferramenta de forma compacta
            nome_tool = msg.get("name", "tool")
            try:
                tool_data = json.loads(msg.get("content", "{}"))
            except json.JSONDecodeError:
                tool_data = {"raw": msg.get("content", "")[:500]}
            with st.chat_message("assistant", avatar="🔧"):
                st.caption(f"🔧 ferramenta: `{nome_tool}`")
                if isinstance(tool_data, dict):
                    if "erro" in tool_data:
                        st.error(tool_data["erro"])
                    elif nome_tool == "ler_schema":
                        cols = tool_data.get("colunas", {})
                        st.write(
                            f"**{tool_data.get('nome','?')}** · "
                            f"{tool_data.get('linhas',0):,} linhas · "
                            f"{len(cols)} colunas"
                        )
                        st.json(cols, expanded=False)
                    elif nome_tool == "ler_amostra":
                        amostra = tool_data.get("amostra", [])
                        if amostra:
                            st.dataframe(pd.DataFrame(amostra),
                                         use_container_width=True,
                                         hide_index=True)
                    elif nome_tool == "executar_pandas":
                        if tool_data.get("ok"):
                            shape = tool_data.get("shape")
                            if shape:
                                st.write(
                                    f"✓ DataFrame gerado: "
                                    f"{shape[0]:,} linhas × {shape[1]} colunas"
                                )
                            elif "stdout" in tool_data and tool_data["stdout"]:
                                st.code(tool_data["stdout"][:500])
                            else:
                                st.write("✓ executado")
                    elif nome_tool == "salvar_csv_final":
                        st.success(
                            f"💾 CSV salvo: `{tool_data.get('arquivo','?')}` "
                            f"({tool_data.get('linhas',0):,} linhas, "
                            f"{tool_data.get('colunas',0)} colunas)"
                        )

    # Botao avancar turno
    st.markdown("<br/>", unsafe_allow_html=True)
    col_play1, col_play2 = st.columns([3, 1])
    with col_play1:
        total = len(ss.demo_script["turnos"])
        progresso = ss.demo_turn_idx
        st.caption(f"Turno **{progresso}/{total}** do roteiro")
        st.progress(progresso / max(total, 1))
    with col_play2:
        if not ss.demo_finalizado:
            if st.button(
                "▶ Próximo turno",
                use_container_width=True,
                type="primary",
            ):
                avancar_turno_demo()
                st.rerun()
        else:
            st.success("✓ Demo concluída")

    if ss.demo_finalizado and ss.final_csv_path is None:
        st.warning(
            "Demo terminou mas o CSV final não foi salvo. "
            "Reinicie pela sidebar."
        )

    # Após o player, o resto do app continua (Etapa 2 desbloqueia automaticamente)

# ===== CAMINHO A — OpenAI direto =====
if caminho_label == "A":
    if not os.getenv("OPENAI_API_KEY"):
        st.error(
            "Defina **OPENAI_API_KEY** no arquivo `.env` da raiz do projeto "
            "(use `.env.example` como modelo) ou troque para o Caminho B."
        )
    else:
        try:
            from openai import OpenAI
        except ImportError:
            st.error("Pacote `openai` nao instalado. Rode: `pip install openai`")
            st.stop()

        for msg in ss.messages:
            role = msg.get("role")
            content = msg.get("content") or ""
            if role in ("user", "assistant") and content.strip():
                with st.chat_message(role, avatar="🟡" if role == "assistant" else "👤"):
                    st.markdown(content)

        prompt_input = st.chat_input("Conte sua pergunta (ex: 'quais EAPs vao atrasar?')")

        if prompt_input:
            if ss.turn_count >= MAX_TURNS:
                st.warning(f"Limite de {MAX_TURNS} turnos. Reinicie pela barra lateral.")
                st.stop()

            ss.messages.append({"role": "user", "content": prompt_input})
            ss.turn_count += 1
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt_input)

            system_prompt = load_prompt()
            if ss.uploaded_dfs:
                lista = "\n".join(
                    f"- `{n}` ({len(d)} linhas × {len(d.columns)} cols)"
                    for n, d in ss.uploaded_dfs.items()
                )
                system_prompt += f"\n\n## Arquivos disponiveis agora\n{lista}"
            else:
                system_prompt += (
                    "\n\n## Arquivos disponiveis agora\n"
                    "(nenhum — peca ao usuario para subir na barra lateral)"
                )

            client = OpenAI()
            tools = load_tools()

            with st.chat_message("assistant", avatar="🟡"):
                progress = st.empty()
                progress.markdown("_pensando..._")
                msgs_api = [{"role": "system", "content": system_prompt}]
                for m in ss.messages:
                    msgs_api.append({k: v for k, v in m.items() if k in (
                        "role", "content", "tool_calls", "tool_call_id", "name"
                    )})

                for _ in range(MAX_TOOL_ITERS):
                    try:
                        resp = client.chat.completions.create(
                            model=MODELOS[ss.modelo_label],
                            messages=msgs_api,
                            tools=tools,
                            tool_choice="auto",
                        )
                    except Exception as e:
                        progress.error(f"Erro OpenAI: {e}")
                        break

                    choice = resp.choices[0].message
                    content = choice.content or ""
                    tool_calls = choice.tool_calls or []
                    assistant_msg: dict = {"role": "assistant", "content": content}
                    if tool_calls:
                        assistant_msg["tool_calls"] = [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            } for tc in tool_calls
                        ]
                    msgs_api.append(assistant_msg)
                    ss.messages.append(assistant_msg)

                    if not tool_calls:
                        progress.markdown(content)
                        break

                    nomes = ", ".join(f"`{tc.function.name}`" for tc in tool_calls)
                    progress.markdown(f"🔧 usando {nomes}...")
                    for tc in tool_calls:
                        nome = tc.function.name
                        try:
                            args = json.loads(tc.function.arguments or "{}")
                        except json.JSONDecodeError:
                            args = {}
                        handler = TOOL_HANDLERS.get(nome)
                        res = handler(**args) if handler else {"erro": f"tool '{nome}' nao existe"}
                        msgs_api.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": nome,
                            "content": json.dumps(res, ensure_ascii=False, default=str)[:6000],
                        })
                        ss.messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": nome,
                            "content": json.dumps(res, ensure_ascii=False, default=str)[:6000],
                        })
                else:
                    progress.warning("_(maximo de iteracoes — envie nova mensagem)_")

            st.rerun()

# ===== CAMINHO B — Copilot do Teams (paste) =====
elif caminho_label == "B":
    cb_a, cb_b = st.columns([1, 3])
    with cb_a:
        if st.button(
            "🎁 Pre-preencher com bloco demo",
            use_container_width=True,
            help="Cola o bloco do Copilot ja preparado para a demo "
                 "(EAPs - vai_atrasar). Voce ainda precisa subir o CSV de "
                 "demo na sidebar antes de processar.",
        ):
            ss.bloco_copilot = BLOCO_DEMO_COPILOT
            # Garante que o CSV de demo esteja carregado
            demo_csv_path = ROOT / "dados_treino" / "demo_eaps_vai_atrasar.csv"
            if demo_csv_path.exists() and demo_csv_path.name not in ss.uploaded_dfs:
                df_demo = _carregar_csv_bytes(open(demo_csv_path, "rb"),
                                              demo_csv_path.name)
                if df_demo is not None:
                    ss.uploaded_dfs[demo_csv_path.name] = df_demo
                    ss.loaded_via_path.add(demo_csv_path.name)
            st.rerun()
    with cb_b:
        if ss.bloco_copilot.strip():
            st.caption("✓ Bloco preenchido — clique em **Processar** abaixo.")
        else:
            st.caption("Cole abaixo OU clique no atalho a esquerda.")

    bloco = st.text_area(
        "Cole aqui o bloco que o Copilot do Teams te entregou:",
        value=ss.bloco_copilot,
        height=320,
        placeholder=(
            "PERGUNTA: Estamos estimando o prazo corretamente? Esta EAP vai atrasar?\n"
            "TARGET: vai_atrasar\n"
            "TASK: classification\n"
            "FEATURES_MANTER: modalidade,tipo_servico,unidade_demandante,valor_estimado,"
            "num_etapas,num_participantes,tem_intercorrencia,urgencia,complexidade,"
            "status,dt_abertura_ano,dt_abertura_mes,etapas_duracao_media,etapas_interrompidas\n"
            "FILTRO: nenhum\n"
            "JOINS: nenhum\n"
            "TRATAMENTO_NULOS: usar como esta (H2O lida com NaN nativamente)\n"
            "PASSO_A_PASSO_PANDAS: |\n"
            "  eaps = dfs['demo_eaps_vai_atrasar.csv']\n"
            "  cols = ['modalidade','tipo_servico','unidade_demandante','valor_estimado',\n"
            "          'num_etapas','num_participantes','tem_intercorrencia','urgencia',\n"
            "          'complexidade','status','dt_abertura_ano','dt_abertura_mes',\n"
            "          'etapas_duracao_media','etapas_interrompidas','vai_atrasar']\n"
            "  resultado = eaps[cols].copy()\n"
        ),
        key="bloco_copilot",
    )

    nome_arquivo_final = st.text_input(
        "Nome do CSV de treino (sem extensao)",
        value="treino_copilot",
    )

    if st.button("✅ Processar bloco e gerar CSV final", type="primary",
                 use_container_width=True):
        try:
            import re
            campos = {}
            codigo_pandas = ""
            modo_codigo = False
            for linha in bloco.splitlines():
                if modo_codigo:
                    if linha.startswith(" ") or linha.startswith("\t"):
                        codigo_pandas += linha.lstrip() + "\n"
                        continue
                    modo_codigo = False
                m = re.match(r"^([A-Z_]+):\s*(.*)$", linha)
                if m:
                    chave, valor = m.group(1), m.group(2).strip()
                    if chave == "PASSO_A_PASSO_PANDAS" and valor in ("|", ""):
                        modo_codigo = True
                    else:
                        campos[chave] = valor

            pergunta = campos.get("PERGUNTA", "").strip()
            target = campos.get("TARGET", "").strip()
            task = campos.get("TASK", "").strip().lower()

            if not pergunta or not target or task not in ("classification", "regression"):
                st.error(
                    "Bloco invalido: preciso de PERGUNTA, TARGET e TASK "
                    "(classification ou regression)."
                )
                st.stop()
            if not codigo_pandas.strip():
                st.error("Bloco sem PASSO_A_PASSO_PANDAS. Pede o codigo ao Copilot.")
                st.stop()
            if not ss.uploaded_dfs:
                st.error("Suba os CSVs na barra lateral antes de processar o bloco.")
                st.stop()

            with st.spinner("Executando o codigo do Copilot em sandbox..."):
                res = tool_executar_pandas(codigo_pandas)

            if not res.get("ok"):
                st.error(f"Erro ao executar: {res.get('erro')}")
                with st.expander("stdout"):
                    st.code(res.get("stdout", ""))
                st.stop()

            df_id = res["df_id"]
            df_resultante = ss.agent_dfs[df_id]
            if target not in df_resultante.columns:
                st.error(
                    f"O codigo gerado nao produziu a coluna target '{target}'. "
                    f"Colunas geradas: {list(df_resultante.columns)}"
                )
                st.stop()

            saida = tool_salvar_csv_final(
                df_id=df_id,
                nome_sugerido=nome_arquivo_final,
                pergunta=pergunta,
                target=target,
                task=task,
            )
            st.success(
                f"✓ {saida['arquivo']} gerado · {saida['linhas']} linhas × "
                f"{saida['colunas']} colunas · pronto para a Etapa 2."
            )
            st.rerun()
        except Exception as e:
            st.error(f"Falha: {type(e).__name__}: {e}")


# ----------------------------------------------------------------------------
# Etapa 2 — Modelo analitico (so aparece quando o CSV final esta pronto)
# ----------------------------------------------------------------------------
if ss.final_csv_path and ss.final_csv_path.exists():
    st.markdown("---")
    st.markdown("## 📊 Etapa 2 — Modelo analitico (H2O AutoML)")

    df_final = pd.read_csv(ss.final_csv_path)
    meta = ss.final_meta or {}
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Linhas", f"{len(df_final):,}")
    col2.metric("Variaveis", len(df_final.columns) - 1)
    col3.metric("Target", meta.get("target", "?"))
    col4.metric("Tarefa", meta.get("task", "?"))

    st.caption(f"**Pergunta:** {meta.get('pergunta', '(nao informada)')}")

    cA, cB = st.columns([1, 2])
    with cA:
        budget = st.slider(
            "Tempo de treino (segundos)",
            min_value=30, max_value=600, value=120, step=30,
            help="Datasets >100k linhas precisam de >180s para o AutoML "
                 "produzir leaderboard rico.",
        )
    with cB:
        st.markdown("&nbsp;")
        treinar = st.button(
            "🚀 Treinar modelo H2O",
            type="primary",
            use_container_width=True,
            disabled=ss.h2o_iniciado,
        )

    if treinar:
        ss.h2o_iniciado = True
        ss.training_log = ""

        with st.status("🚀 Treinando modelo H2O AutoML",
                       expanded=True) as status_box:
            try:
                import contextlib as _ctx
                import io as _io
                import sys as _sys
                import h2o
                from h2o.automl import H2OAutoML

                # Buffer pra capturar stdout do H2O e mostrar pro usuario
                captura = _io.StringIO()
                log_placeholder = st.empty()

                class _TeeWriter:
                    """Escreve no terminal e no buffer simultaneamente."""
                    def __init__(self, original):
                        self.original = original
                    def write(self, msg):
                        try:
                            self.original.write(msg)
                        except Exception:
                            pass
                        captura.write(msg)
                    def flush(self):
                        try:
                            self.original.flush()
                        except Exception:
                            pass

                _stdout_old, _stderr_old = _sys.stdout, _sys.stderr
                _sys.stdout = _TeeWriter(_stdout_old)
                _sys.stderr = _TeeWriter(_stderr_old)

                def _atualizar_log(extra: str = ""):
                    """Mostra as ultimas ~60 linhas do log no UI."""
                    if extra:
                        captura.write(extra + "\n")
                    txt = captura.getvalue()
                    linhas = txt.splitlines()
                    visivel = "\n".join(linhas[-60:]) if linhas else "(aguardando...)"
                    log_placeholder.code(visivel, language="log")

                # Heap dinamica
                try:
                    import psutil
                    ram_gb = psutil.virtual_memory().total / (1024**3)
                    heap_gb = max(2, min(8, int(ram_gb * 0.5)))
                except ImportError:
                    heap_gb = 4

                st.write(f"💾 Heap H2O calculada: **{heap_gb} GB**")

                # Cluster check
                cluster_em_uso = (h2o.cluster() and h2o.cluster().is_running())
                if cluster_em_uso:
                    free_mb = None
                    try:
                        free_mb = h2o.cluster().free_mem / (1024 * 1024)
                    except (AttributeError, Exception):
                        try:
                            cstatus = h2o.cluster_status()
                            if isinstance(cstatus, dict):
                                fm = cstatus.get("free_mem")
                                if fm is not None:
                                    free_mb = float(fm) / (1024 * 1024)
                        except Exception:
                            pass
                    if free_mb is not None and free_mb < heap_gb * 1024 * 0.7:
                        st.write(
                            f"⚠ Cluster atual com {free_mb:.0f}MB — reiniciando..."
                        )
                        h2o.cluster().shutdown(prompt=False)
                        cluster_em_uso = False

                if not cluster_em_uso:
                    st.write("🔌 Iniciando cluster H2O...")
                    h2o.init(max_mem_size=f"{heap_gb}G", nthreads=-1)
                else:
                    st.write("🔌 Reutilizando cluster H2O ja ativo")
                _atualizar_log()

                target = meta.get("target", "")
                task = meta.get("task", "classification")

                if target not in df_final.columns:
                    st.error(f"Coluna target '{target}' nao existe no CSV.")
                    ss.h2o_iniciado = False
                    _sys.stdout, _sys.stderr = _stdout_old, _stderr_old
                    st.stop()

                if len(df_final) > 500_000:
                    st.warning(
                        f"Dataset com {len(df_final):,} linhas — amostrando "
                        f"200.000 para o orcamento de {budget}s."
                    )
                    df_final = df_final.sample(n=200_000, random_state=42)

                st.write(
                    f"📊 Split treino/teste: 80/20 — "
                    f"{int(len(df_final)*0.8):,} treino · "
                    f"{int(len(df_final)*0.2):,} teste"
                )
                df_train = df_final.sample(frac=0.8, random_state=42)
                df_test = df_final.drop(df_train.index)

                st.write("📤 Convertendo dados para H2OFrame...")
                hf_train = h2o.H2OFrame(df_train)
                hf_test = h2o.H2OFrame(df_test)
                _atualizar_log()

                if task == "classification":
                    hf_train[target] = hf_train[target].asfactor()
                    hf_test[target] = hf_test[target].asfactor()

                features = [c for c in df_final.columns if c != target]
                st.write(
                    f"🔬 Iniciando AutoML — orcamento {budget}s, "
                    f"target=`{target}`, {len(features)} features"
                )
                _atualizar_log()

                aml = H2OAutoML(
                    max_runtime_secs=budget,
                    seed=42,
                    sort_metric="AUC" if task == "classification" else "RMSE",
                    exclude_algos=["StackedEnsemble", "DeepLearning"],
                )
                aml.train(x=features, y=target, training_frame=hf_train)
                _atualizar_log("\n✅ Treino finalizado")
                _sys.stdout, _sys.stderr = _stdout_old, _stderr_old
                ss.training_log = captura.getvalue()

                st.write("📈 Avaliando no conjunto de teste...")
                lb = aml.leaderboard.as_data_frame(use_multi_thread=True)
                leader = aml.leader

                if leader is None or len(lb) == 0:
                    st.error(
                        "⚠ AutoML nao conseguiu treinar nenhum modelo no "
                        f"orcamento de {budget}s. Tente:\n"
                        "1. Aumentar o tempo de treino (slider acima).\n"
                        "2. Reduzir o numero de linhas do CSV.\n"
                        "3. Verificar se o target tem variacao suficiente."
                    )
                    ss.h2o_iniciado = False
                    ss.h2o_resultado = None
                    st.stop()

                perf_test = leader.model_performance(hf_test)

                metrics: dict = {}
                if task == "classification":
                    metrics["AUC"] = float(perf_test.auc())
                    metrics["LogLoss"] = float(perf_test.logloss())
                    try:
                        metrics["Accuracy"] = float(perf_test.accuracy()[0][1])
                    except Exception:
                        pass
                else:
                    metrics["RMSE"] = float(perf_test.rmse())
                    metrics["MAE"] = float(perf_test.mae())
                    metrics["R2"] = float(perf_test.r2())

                varimp_df = None
                try:
                    varimp = leader.varimp(use_pandas=True)
                    if varimp is not None:
                        varimp_df = varimp.head(15)
                except Exception:
                    pass

                # Captura info dos features para construir o formulario da Etapa 4
                feature_info: dict = {}
                for col in features:
                    s = df_train[col]
                    if pd.api.types.is_numeric_dtype(s):
                        feature_info[col] = {
                            "type": "number",
                            "min": float(s.min()) if pd.notna(s.min()) else 0.0,
                            "max": float(s.max()) if pd.notna(s.max()) else 0.0,
                            "mean": float(s.mean()) if pd.notna(s.mean()) else 0.0,
                            "median": float(s.median()) if pd.notna(s.median()) else 0.0,
                        }
                    else:
                        n_unique = s.nunique(dropna=True)
                        if n_unique <= 30:
                            feature_info[col] = {
                                "type": "select",
                                "values": sorted(
                                    s.dropna().astype(str).unique().tolist()
                                ),
                            }
                        else:
                            feature_info[col] = {"type": "text"}

                # Amostra do conjunto de teste para a Etapa 4 (casos novos
                # que o modelo NUNCA viu em treino).
                test_sample = df_test.sample(
                    n=min(50, len(df_test)), random_state=42
                ).reset_index(drop=True)

                # Tenta capturar o event_log estruturado do AutoML
                event_log_df = None
                try:
                    event_log_df = aml.event_log.as_data_frame(
                        use_multi_thread=True
                    )
                except Exception:
                    pass

                # Persiste o modelo H2O em disco para a Demo 2 (Consumir)
                slug = _slugify(target)
                model_dir = MODELS_DIR / slug
                model_dir.mkdir(parents=True, exist_ok=True)
                # Limpa modelos antigos com mesmo target
                for old in model_dir.glob("*"):
                    if old.is_file() and old.name not in ("metadata.json",):
                        try:
                            old.unlink()
                        except Exception:
                            pass
                try:
                    saved_path = h2o.save_model(
                        model=leader, path=str(model_dir), force=True
                    )
                    saved_filename = Path(saved_path).name
                except Exception as _e:
                    saved_filename = None
                    st.warning(
                        f"⚠ Nao consegui salvar o modelo em disco: {_e}. "
                        f"Demo 2 nao tera acesso a este treino."
                    )

                modelo_metadata = {
                    "slug": slug,
                    "target": target,
                    "task": task,
                    "pergunta": meta.get("pergunta", ""),
                    "leader_id": str(leader.model_id),
                    "saved_filename": saved_filename,
                    "metrics": metrics,
                    "treinado_em": datetime.now().isoformat(timespec="seconds"),
                    "n_train": len(df_train),
                    "n_test": len(df_test),
                    "features": features,
                    "feature_info": feature_info,
                }
                (model_dir / "metadata.json").write_text(
                    json.dumps(modelo_metadata, ensure_ascii=False,
                               indent=2, default=str),
                    encoding="utf-8",
                )
                # Salva tambem 5 casos do conjunto de teste (pre-preenchimento)
                test_sample_path = model_dir / "test_sample.csv"
                test_sample.head(5).to_csv(test_sample_path,
                                           index=False, encoding="utf-8")

                ss.h2o_resultado = {
                    "leaderboard": lb.head(10),
                    "metrics": metrics,
                    "varimp": varimp_df,
                    "leader_id": str(leader.model_id),
                    "task": task,
                    "target": target,
                    "features": features,
                    "feature_info": feature_info,
                    "test_sample": test_sample,
                    "event_log": event_log_df,
                    "n_train": len(df_train),
                    "n_test": len(df_test),
                    "treinado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                st.write(f"🏆 Vencedor: `{leader.model_id}`")
                status_box.update(
                    label="✅ Treino concluido",
                    state="complete",
                    expanded=False,
                )
            except Exception as e:
                # Restaura stdout/stderr e mostra o log capturado
                try:
                    _sys.stdout, _sys.stderr = _stdout_old, _stderr_old
                    ss.training_log = captura.getvalue()
                except Exception:
                    pass
                st.error(f"Falha no treino: {type(e).__name__}: {e}")
                if ss.training_log:
                    with st.expander("📜 Log capturado ate o erro",
                                     expanded=True):
                        st.code(ss.training_log[-3000:], language="log")
                ss.h2o_iniciado = False
                status_box.update(label="❌ Falha no treino",
                                  state="error", expanded=True)

    # -------------------------------------------------------------
    # Relatorio analitico
    # -------------------------------------------------------------
    if ss.h2o_resultado:
        r = ss.h2o_resultado
        st.markdown("### 🏆 Modelo vencedor")
        st.code(r["leader_id"])

        st.markdown("### 📈 Metricas no conjunto de teste")
        mcols = st.columns(len(r["metrics"]))
        for i, (k, v) in enumerate(r["metrics"].items()):
            mcols[i].metric(k, f"{v:.4f}")

        st.markdown("### 🥇 Leaderboard (top 10)")
        st.dataframe(r["leaderboard"], use_container_width=True, hide_index=True)

        if r["varimp"] is not None:
            st.markdown("### 🎯 Importancia das variaveis")
            varimp = r["varimp"].copy()
            col_var = "variable" if "variable" in varimp.columns else varimp.columns[0]
            col_imp = "scaled_importance" if "scaled_importance" in varimp.columns else varimp.columns[1]
            chart_df = varimp.set_index(col_var)[[col_imp]]
            st.bar_chart(chart_df, color=BB_AZUL)

        # Logs estruturados do treino (event_log) + stdout bruto
        if r.get("event_log") is not None or ss.get("training_log"):
            with st.expander("📜 Log do treino — eventos H2O AutoML"):
                if r.get("event_log") is not None and len(r["event_log"]) > 0:
                    ev = r["event_log"][["timestamp", "level", "stage", "message"]] \
                        if {"timestamp", "level", "stage", "message"}.issubset(
                            set(r["event_log"].columns)
                        ) else r["event_log"]
                    st.dataframe(ev, use_container_width=True, hide_index=True)
                else:
                    st.caption("event_log nao disponivel para este modelo.")
            if ss.get("training_log"):
                with st.expander("📋 Saida bruta do H2O (stdout/stderr)"):
                    st.code(ss.training_log[-5000:], language="log")

        # Gera HTML do relatorio
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_report = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>Relatorio Analitico — {r['leader_id']}</title>
<style>
body {{ font-family: 'IBM Plex Sans', Arial, sans-serif; max-width: 960px;
       margin: 2rem auto; padding: 0 1.5rem; color: #1f1f1f; }}
header {{ background: {BB_AZUL}; color: white; padding: 1.5rem;
         border-top: 6px solid {BB_AMARELO}; border-radius: 6px; }}
h1 {{ margin: 0; }}
h2 {{ color: {BB_AZUL_ESCURO}; border-bottom: 2px solid {BB_AMARELO};
      padding-bottom: 0.3rem; margin-top: 2rem; }}
.tag {{ display: inline-block; background: {BB_AMARELO};
        color: {BB_AZUL_ESCURO}; padding: 0.15rem 0.7rem;
        border-radius: 999px; font-size: 0.8rem; font-weight: 700; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #ddd; padding: 0.5rem; text-align: left; }}
th {{ background: {BB_FUNDO_SUAVE}; color: {BB_AZUL_ESCURO}; }}
.metric {{ display: inline-block; margin-right: 2rem; padding: 1rem;
           border-left: 4px solid {BB_AMARELO}; background: {BB_FUNDO_SUAVE}; }}
.metric .v {{ font-size: 1.8rem; font-weight: 700; color: {BB_AZUL}; }}
.metric .l {{ color: {BB_CINZA}; font-size: 0.85rem; }}
footer {{ margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #ddd;
          color: {BB_CINZA}; font-size: 0.85rem; }}
</style></head>
<body>
<header>
<h1>Relatorio Analitico</h1>
<div style="margin-top:0.4rem;">DISEC · Banco do Brasil · Licitacao Eletronica</div>
<span class="tag" style="margin-top:0.5rem;">HyperCopa DISEC 2026</span>
</header>

<h2>Pergunta de negocio</h2>
<p><strong>{meta.get('pergunta', '(nao informada)')}</strong></p>
<p>Variavel-alvo: <code>{r['target']}</code> · Tipo: {r['task']}</p>

<h2>Modelo vencedor</h2>
<p><code>{r['leader_id']}</code></p>
<p>Treinado em {r['treinado_em']} · {r['n_train']:,} linhas treino · {r['n_test']:,} linhas teste.</p>

<h2>Metricas no conjunto de teste</h2>
{''.join(f'<div class="metric"><div class="l">{k}</div><div class="v">{v:.4f}</div></div>' for k, v in r['metrics'].items())}

<h2>Leaderboard (top 10)</h2>
{r['leaderboard'].to_html(index=False, float_format='%.4f')}

{('<h2>Importancia das variaveis (top 15)</h2>' + r['varimp'].to_html(index=False, float_format='%.4f')) if r['varimp'] is not None else ''}

<h2>Recomendacoes</h2>
<ul>
<li>Validar o modelo em janela temporal recente (out-of-time) antes de promover a producao.</li>
<li>Calibrar limiar de decisao com area de negocio para equilibrar falsos positivos/negativos.</li>
<li>Monitorar drift mensalmente nas variaveis de maior importancia.</li>
<li>Reentreinar a cada novo trimestre fiscal ou apos mudanca de politica de licitacao.</li>
</ul>

<footer>
Gerado automaticamente pela jornada Agente Preparador + Modelo Analitico.<br>
Banco do Brasil · DISEC · {datetime.now().strftime('%d/%m/%Y %H:%M')}
</footer>
</body></html>"""

        report_path = REPORT_DIR / f"relatorio_{ts}.html"
        report_path.write_text(html_report, encoding="utf-8")

        # JSON estruturado para o Copilot Teams interpretar (Fase 2)
        relatorio_json = {
            "id": ts,
            "pergunta": meta.get("pergunta", ""),
            "target": r["target"],
            "task": r["task"],
            "leader_id": r["leader_id"],
            "treinado_em": r["treinado_em"],
            "n_train": r["n_train"],
            "n_test": r["n_test"],
            "metrics": r["metrics"],
            "leaderboard": r["leaderboard"].to_dict(orient="records"),
            "varimp": (
                r["varimp"].to_dict(orient="records")
                if r["varimp"] is not None else []
            ),
        }
        json_path = REPORT_DIR / f"relatorio_{ts}.json"
        json_str = json.dumps(relatorio_json, ensure_ascii=False, indent=2,
                              default=str)
        json_path.write_text(json_str, encoding="utf-8")

        st.markdown("---")
        st.markdown("## 📥 Etapa 4 — Documentos obrigatórios da entrega")
        st.markdown(
            "<p style='color:#5C6670'>Pacote único pronto para anexar ao envio "
            "da banca: <b>relatório HTML</b> (apresentação visual) + "
            "<b>relatório JSON</b> (auditoria) + <b>summary.md</b> "
            "(executivo) + <b>como_reproduzir.txt</b> (instruções para "
            "regerar este resultado).</p>",
            unsafe_allow_html=True,
        )

        # Monta summary.md executivo e como_reproduzir.txt para o pacote
        top_vars = ""
        if r.get("varimp") is not None and len(r["varimp"]) > 0:
            top_vars = "\n".join(
                f"  {i+1}. **{row['variable']}** "
                f"(importância {row['scaled_importance']:.2f})"
                for i, row in enumerate(
                    r["varimp"].head(5).to_dict(orient="records")
                )
            )
        metricas_md = "\n".join(
            f"  - **{k}**: {v:.4f}" if isinstance(v, (int, float)) else
            f"  - **{k}**: {v}"
            for k, v in r["metrics"].items()
        )
        summary_md = f"""# Summary executivo — Modelo H2O AutoML

**Pergunta:** {meta.get('pergunta', '(não informada)')}
**Target:** `{r['target']}` ({r['task']})
**Modelo líder:** `{r['leader_id']}`
**Treinado em:** {r['treinado_em']}
**Tamanho:** {r['n_train']:,} treino · {r['n_test']:,} teste

## Métricas no conjunto de teste
{metricas_md}

## Top-5 variáveis mais importantes
{top_vars or '  (não disponível para este modelo)'}

## Recomendação curta
- Use este modelo como **apoio à decisão**, não como decisão automática.
- Para classificação binária, considere limiar 0,5 e priorize casos com
  probabilidade > 0,7 para revisão de gestor.
- Reentreinar a cada trimestre ou após mudança de política de Licitação.

---
*Gerado automaticamente pela jornada HyperCopa DISEC 2026.*
"""
        como_reproduzir_txt = f"""# Como reproduzir este resultado

1. Clone o repositório público da equipe HyperCopa DISEC 2026.
2. Instale dependências: pip install -r requirements_app.txt
3. Garanta Java JDK 17 ou 21 instalado: java -version
4. (opcional) Regere os dados sintéticos: python gerar_dados_sinteticos_eaps.py
5. Inicie o app: streamlit run app_agente_bb.py
6. Ative "Modo demonstração da banca" na sidebar.
7. Avance os turnos da Etapa 1 até gerar o CSV final.
8. Na Etapa 2, treine com budget de 60s.
9. As métricas devem ser idênticas a estas:
{metricas_md}

Reprodutibilidade garantida por:
- random.seed(42), np.random.seed(42) nos geradores de dados sintéticos.
- random_state=42 nos splits treino/teste.
- seed=42 no H2OAutoML.
- Versões pinadas em requirements_app.txt (h2o==3.46.0.6, scikit-learn==1.5.2).

Gerado em: {r['treinado_em']}
"""

        # Botão único: pacote ZIP completo
        import zipfile as _zipfile
        zip_buf = io.BytesIO()
        with _zipfile.ZipFile(zip_buf, "w", _zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("relatorio.html", html_report)
            zf.writestr("relatorio.json", json_str)
            zf.writestr("summary.md", summary_md)
            zf.writestr("como_reproduzir.txt", como_reproduzir_txt)
            # MVP Canvas (se existir no repo)
            canvas_md = ROOT / "docs" / "MVP_CANVAS.md"
            if canvas_md.exists():
                zf.writestr("MVP_CANVAS.md", canvas_md.read_text(encoding="utf-8"))
            canvas_docx = ROOT / "docs" / "MVP_CANVAS.docx"
            if canvas_docx.exists():
                zf.writestr("MVP_CANVAS.docx", canvas_docx.read_bytes())
        zip_bytes = zip_buf.getvalue()

        st.download_button(
            f"📦 Baixar pacote completo da entrega ({len(zip_bytes)/1024:.0f} KB)",
            zip_bytes,
            file_name=f"hypercopa_pacote_{ts}.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True,
            help="ZIP único com relatório HTML + JSON + summary.md + "
                 "como_reproduzir.txt + MVP Canvas. Anexe este arquivo ao "
                 "envio da banca.",
        )

        st.markdown("##### Ou baixe artefatos individuais:")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button(
                "⬇️ Relatório HTML",
                html_report.encode("utf-8"),
                file_name=report_path.name,
                mime="text/html",
                use_container_width=True,
            )
        with c2:
            st.download_button(
                "⬇️ Relatório JSON",
                json_str.encode("utf-8"),
                file_name=json_path.name,
                mime="application/json",
                use_container_width=True,
            )
        with c3:
            st.download_button(
                "⬇️ Summary.md",
                summary_md.encode("utf-8"),
                file_name=f"summary_{ts}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        # ----------------------------------------------------------------
        # Etapa 5 — Interpretacao do relatorio
        # ----------------------------------------------------------------
        st.markdown("---")
        st.markdown("## 💬 Etapa 5 — Interpretar o resultado em linguagem de negócio")

        # Em modo demo, sempre usamos o simulador local rule-based.
        # Nos outros caminhos, oferecemos os 3 sub-caminhos lado a lado.
        if ss.modo_demo or ss.caminho == "C":
            sub_caminho = "C"
            st.info(
                "**Modo demonstração** — o simulador local lê o JSON do relatório "
                "e gera resumo executivo + recomendações sem chamar nenhum LLM "
                "externo. Reproduz o comportamento do agente Copilot Teams "
                "em produção."
            )
        else:
            opcoes_etapa5 = ["A", "B", "C"]
            if ss.caminho == "A":
                idx_default = 0
            elif ss.caminho == "B":
                idx_default = 1
            else:
                idx_default = 2
            sub_caminho = st.radio(
                "Como interpretar o relatório?",
                options=opcoes_etapa5,
                format_func=lambda x: {
                    "A": "(a) OpenAI direto — chat embutido (precisa chave OPENAI_API_KEY)",
                    "B": "(b) Copilot Teams real — copiar bloco para o Teams",
                    "C": "(c) Simulador local — interpretação rule-based offline",
                }[x],
                index=idx_default,
                horizontal=False,
                key="sub_etapa5",
            )

        # ====== Simulador local (Caminho C / modo demo) ======
        if sub_caminho == "C":
            try:
                from app.interprete_rules import (
                    interpretar_relatorio, renderizar_markdown,
                )
            except ImportError:
                st.error(
                    "Módulo `app/interprete_rules.py` não encontrado. "
                    "Garanta que a pasta `app/` está no repositório."
                )
                st.stop()

            interp = interpretar_relatorio(relatorio_json)

            # UI com aparência de "Teams" — header roxo, balão de mensagem
            st.markdown(
                f"""
                <div style='background:linear-gradient(180deg,#4B53BC 0%,#5059C9 100%);
                color:white;padding:0.7rem 1rem;border-radius:8px 8px 0 0;
                font-weight:600;font-size:0.95rem;'>
                💬 Agente Preparador + Intérprete BB · Microsoft Copilot do Teams (simulado offline)
                </div>
                <div style='background:#F5F5FA;border:1px solid #E5E7EA;border-top:none;
                border-radius:0 0 8px 8px;padding:1rem 1.2rem;margin-bottom:1rem;'>
                """,
                unsafe_allow_html=True,
            )

            md = renderizar_markdown(interp)
            st.markdown(md)

            if interp["metrica_ruim"]:
                st.warning(
                    "⚠️ **Aviso explícito do simulador:** as métricas indicam "
                    "que este modelo NÃO deve ir para produção. Trate como "
                    "experimento. Reentrenar com mais dados ou redefinir o target."
                )

            st.markdown("</div>", unsafe_allow_html=True)

            # Permite baixar a interpretação como markdown
            st.download_button(
                "⬇️ Baixar interpretação (.md)",
                md.encode("utf-8"),
                file_name=f"interpretacao_{ts}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        # ====== Caminho A — OpenAI direto ======
        elif sub_caminho == "A":
            # Interpretacao via OpenAI dentro do proprio app
            st.markdown("## 💬 Etapa 3 — Interpretacao do relatorio")

            ss.setdefault("interpretacao", None)

            if ss.interpretacao is None:
                if st.button(
                    "🤖 Gerar interpretacao do relatorio",
                    type="primary",
                    use_container_width=True,
                ):
                    if not os.getenv("OPENAI_API_KEY"):
                        st.error(
                            "Defina OPENAI_API_KEY no .env para gerar a "
                            "interpretacao no Caminho A."
                        )
                    else:
                        try:
                            from openai import OpenAI
                        except ImportError:
                            st.error("Pacote `openai` nao instalado.")
                            st.stop()

                        with st.spinner("Pedindo interpretacao ao agente..."):
                            try:
                                client = OpenAI()
                                sys_interprete = (
                                    "Voce e analista BB / DISEC. Recebe um "
                                    "JSON com o resultado de um modelo H2O "
                                    "AutoML treinado sobre dados de Licitacao "
                                    "Eletronica e produz, em PT-BR e em "
                                    "linguagem de negocio (sem jargao de ML), "
                                    "exatamente:\n\n"
                                    "1. Resumo executivo em <=4 linhas.\n"
                                    "2. Traducao de cada metrica para "
                                    "linguagem de negocio (AUC -> 'discrimina "
                                    "bem'; RMSE -> 'erro medio em <unidade>'; "
                                    "R2 -> 'explica X% da variacao'; Accuracy "
                                    "-> 'acerta X% das vezes').\n"
                                    "3. Top 3 fatores e o que eles indicam.\n"
                                    "4. 3 a 5 recomendacoes operacionais "
                                    "concretas para a area demandante.\n"
                                    "5. Aviso explicito SE a metrica for ruim "
                                    "(AUC<0.65, R2<0.5, Accuracy~50%).\n\n"
                                    "Use **negrito** apenas para metricas-"
                                    "chave e decisoes operacionais. NAO "
                                    "use jargao de ML cru. Frases curtas."
                                )
                                resp = client.chat.completions.create(
                                    model=MODELOS[ss.modelo_label],
                                    messages=[
                                        {"role": "system", "content": sys_interprete},
                                        {"role": "user", "content":
                                            "Interprete este relatorio:\n\n"
                                            "```json\n" + json_str + "\n```"},
                                    ],
                                )
                                ss.interpretacao = resp.choices[0].message.content
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro OpenAI: {e}")

            if ss.interpretacao:
                st.markdown(ss.interpretacao)
                if st.button("🔄 Gerar nova interpretacao", use_container_width=True):
                    ss.interpretacao = None
                    st.rerun()
        elif sub_caminho == "B":
            # Caminho B — copy-paste para o Copilot do Teams
            st.markdown("#### Copie o bloco para o Copilot do Teams real")
            st.markdown(
                "<p style='color:#5C6670'>Copie o bloco abaixo, cole na conversa "
                "com o agente <b>Preparador + Interprete BB</b> no Microsoft "
                "Copilot do Teams e peca <i>'interpreta esse relatorio'</i>. "
                "O Copilot devolve o resumo executivo, traducao das metricas e "
                "recomendacoes operacionais em linguagem de negocio.</p>",
                unsafe_allow_html=True,
            )
            prompt_copilot = (
                "Interpreta esse relatorio em linguagem de negocio para a area "
                "demandante (DISEC / Banco do Brasil). Resumo executivo + traducao "
                "das metricas + recomendacoes operacionais.\n\n"
                "```json\n" + json_str + "\n```"
            )
            st.code(prompt_copilot, language="markdown")
            st.caption(
                "ℹ️ Use o icone de copiar no canto superior direito do bloco acima."
            )

        # ----------------------------------------------------------------
        # Etapa 6 — Caso de evento real (predict de uma EAP/contrato novo)
        # ----------------------------------------------------------------
        st.markdown("---")
        st.markdown("## 🔮 Etapa 6 — Testar em caso de evento real")
        st.markdown(
            "<p style='color:#5C6670'>Simule uma <b>EAP/contrato chegando "
            "agora</b> — caso que o modelo <b>nunca viu durante o treino</b>. "
            "Os campos vêm preenchidos a partir de um cenário real. Você "
            "pode editar e simular variações. Ao consultar, o app mostra a "
            "predição com semáforo de risco e (quando aplicável) o gabarito "
            "do conjunto de teste.</p>",
            unsafe_allow_html=True,
        )

        feature_info = r.get("feature_info", {})
        features = r.get("features", [])
        test_sample = r.get("test_sample")
        target = r["target"]

        ss.setdefault("ultima_predicao", None)
        ss.setdefault("caso_sorteado_idx", None)
        ss.setdefault("valor_real_caso", None)
        ss.setdefault("cenario_demo_ativo", None)

        if not features:
            st.warning(
                "Treine o modelo novamente para habilitar a consulta."
            )
            st.stop()
        if test_sample is None or len(test_sample) == 0:
            st.warning(
                "Sem amostra de teste disponivel — retreine o modelo "
                "para habilitar o sorteio."
            )
            st.stop()

        # Em modo demo: 3 cenários pré-roteirizados como cards clicáveis.
        # Cada cenário usa um caso REAL do conjunto de teste, escolhido
        # de forma determinística para representar perfis distintos.
        if ss.modo_demo:
            st.markdown("#### Escolha um cenário pré-roteirizado:")

            # Define 3 perfis baseados no porte do fornecedor
            cenarios_demo = [
                {
                    "id": "A",
                    "titulo": "Cenário A — DICOI · TI · médio",
                    "descricao": "Software de gestão · ~R$ 850k · fornecedor médio porte · 5 aditivos",
                    "filtro": lambda df: df[
                        (df.get("porte_fornecedor", "") == "Médio") &
                        (df.get("num_aditivos", 0) >= 3)
                    ] if "porte_fornecedor" in df.columns else df.head(0),
                },
                {
                    "id": "B",
                    "titulo": "Cenário B — DISUP · Reforma · ME",
                    "descricao": "Reforma de agência · ~R$ 320k · fornecedor pequeno (ME) · sem aditivos",
                    "filtro": lambda df: df[
                        (df.get("porte_fornecedor", "") == "ME") &
                        (df.get("num_aditivos", 0) <= 1)
                    ] if "porte_fornecedor" in df.columns else df.head(0),
                },
                {
                    "id": "C",
                    "titulo": "Cenário C — DITEC · Cloud · grande",
                    "descricao": "Cloud computing · ~R$ 2,1M · fornecedor grande · contrato continuado",
                    "filtro": lambda df: df[
                        (df.get("porte_fornecedor", "") == "Grande")
                    ] if "porte_fornecedor" in df.columns else df.head(0),
                },
            ]

            cards = st.columns(3)
            for i, cen in enumerate(cenarios_demo):
                with cards[i]:
                    cor_borda = "#FAE128" if ss.cenario_demo_ativo == cen["id"] else "#E5E7EA"
                    st.markdown(
                        f"<div style='border:2px solid {cor_borda};border-radius:6px;"
                        f"padding:0.7rem;background:{BB_FUNDO_SUAVE};min-height:120px;'>"
                        f"<b style='color:{BB_AZUL_ESCURO};'>{cen['titulo']}</b><br/>"
                        f"<small style='color:{BB_CINZA};'>{cen['descricao']}</small>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        f"▶ Carregar Cenário {cen['id']}",
                        key=f"cenario_btn_{cen['id']}",
                        use_container_width=True,
                    ):
                        # Filtra um caso do conjunto teste compatível com o perfil
                        try:
                            subset = cen["filtro"](test_sample)
                        except Exception:
                            subset = test_sample.head(0)
                        if len(subset) == 0:
                            # Fallback: pega um caso qualquer do teste
                            subset = test_sample
                        # Determinístico: pega o primeiro do subset ordenado pelo índice
                        idx = int(subset.sort_index().index[0])
                        row = test_sample.loc[idx]
                        ss.caso_sorteado_idx = idx
                        ss.valor_real_caso = row[target]
                        ss.ultima_predicao = None
                        ss.cenario_demo_ativo = cen["id"]
                        for feat in features:
                            info = feature_info.get(feat, {"type": "text"})
                            val = row.get(feat)
                            key = f"input_{feat}"
                            if info["type"] == "number":
                                try:
                                    ss[key] = float(val) if pd.notna(val) else info.get("median", 0.0)
                                except (ValueError, TypeError):
                                    ss[key] = info.get("median", 0.0)
                            elif info["type"] == "select":
                                sval = "" if pd.isna(val) else str(val)
                                ss[key] = sval if sval in info["values"] else info["values"][0]
                            else:
                                ss[key] = "" if pd.isna(val) else str(val)
                        st.rerun()

            st.markdown(" ")  # espaço

        # Botão de sorteio livre (sempre disponível, em qualquer modo)
        sortcol1, sortcol2 = st.columns([2, 1])
        with sortcol1:
            label_botao = (
                "🎲 Sortear OUTRO caso do conjunto de teste"
                if ss.modo_demo else
                "🎲 Sortear novo caso do conjunto de teste"
            )
            if st.button(label_botao, use_container_width=True):
                idx = int(test_sample.sample(1).index[0])
                row = test_sample.loc[idx]
                ss.caso_sorteado_idx = idx
                ss.valor_real_caso = row[target]
                ss.ultima_predicao = None
                ss.cenario_demo_ativo = None
                for feat in features:
                    info = feature_info.get(feat, {"type": "text"})
                    val = row.get(feat)
                    key = f"input_{feat}"
                    if info["type"] == "number":
                        try:
                            ss[key] = float(val) if pd.notna(val) else info.get("median", 0.0)
                        except (ValueError, TypeError):
                            ss[key] = info.get("median", 0.0)
                    elif info["type"] == "select":
                        sval = "" if pd.isna(val) else str(val)
                        ss[key] = sval if sval in info["values"] else info["values"][0]
                    else:
                        ss[key] = "" if pd.isna(val) else str(val)
                st.rerun()
        with sortcol2:
            if ss.cenario_demo_ativo:
                st.caption(f"📌 Cenário {ss.cenario_demo_ativo} ativo (caso #{ss.caso_sorteado_idx})")
            elif ss.caso_sorteado_idx is not None:
                st.caption(f"Caso #{ss.caso_sorteado_idx} sorteado")

        if ss.caso_sorteado_idx is None:
            st.info(
                "👆 Em modo demo, escolha um **Cenário (A/B/C)** acima. "
                "Ou clique em **Sortear caso** para um exemplo aleatório."
                if ss.modo_demo else
                "👆 Clique em **Sortear novo caso** para preencher o "
                "formulario com um exemplo real."
            )

        with st.form("consulta_modelo"):
            valores: dict = {}
            cols_ui = st.columns(2)
            for i, feat in enumerate(features):
                info = feature_info.get(feat, {"type": "text"})
                container = cols_ui[i % 2]
                key = f"input_{feat}"
                if info["type"] == "number":
                    if key not in ss:
                        ss[key] = info.get("median", 0.0)
                    valores[feat] = container.number_input(
                        feat,
                        key=key,
                        help=f"min={info.get('min', 0):.2f} · "
                             f"max={info.get('max', 0):.2f} · "
                             f"medio={info.get('mean', 0):.2f}",
                    )
                elif info["type"] == "select":
                    opcoes = info["values"]
                    if key not in ss or ss[key] not in opcoes:
                        ss[key] = opcoes[0] if opcoes else ""
                    valores[feat] = container.selectbox(feat, opcoes, key=key)
                else:
                    if key not in ss:
                        ss[key] = ""
                    valores[feat] = container.text_input(feat, key=key)

            predizer = st.form_submit_button(
                "🔮 Consultar modelo",
                type="primary",
                use_container_width=True,
                disabled=ss.caso_sorteado_idx is None,
            )

        if predizer:
            try:
                import h2o
                if not h2o.cluster() or not h2o.cluster().is_running():
                    h2o.init(max_mem_size="4G", nthreads=-1)
                leader = h2o.get_model(r["leader_id"])
                df_consulta = pd.DataFrame([valores])
                hf = h2o.H2OFrame(df_consulta)
                pred = leader.predict(hf).as_data_frame(use_multi_thread=True)

                if r["task"] == "classification":
                    classe = str(pred["predict"].iloc[0])
                    prob_cols = [c for c in pred.columns if c != "predict"]
                    prob = (float(pred[prob_cols[-1]].iloc[0])
                            if len(prob_cols) >= 2 else None)
                    if prob is not None:
                        if prob < 0.30:
                            nivel = "Baixo"
                            acao = "Seguir o fluxo normal. Sem acao adicional."
                        elif prob < 0.60:
                            nivel = "Moderado"
                            acao = ("Revisao previa pela area demandante. "
                                    "Considerar parecer adicional.")
                        else:
                            nivel = "Alto"
                            acao = ("Revisao OBRIGATORIA antes de seguir. "
                                    "Acionar area juridica e gestor.")
                    else:
                        nivel, acao = "—", "Sem probabilidade disponivel."

                    ss.ultima_predicao = {
                        "tipo": "classification",
                        "classe": classe, "prob": prob,
                        "nivel": nivel, "acao": acao,
                        "valores": valores,
                        "real": ss.valor_real_caso,
                    }
                else:
                    valor = float(pred["predict"].iloc[0])
                    rmse = r["metrics"].get("RMSE")
                    ss.ultima_predicao = {
                        "tipo": "regression",
                        "valor": valor, "rmse": rmse,
                        "valores": valores,
                        "real": ss.valor_real_caso,
                    }
                st.rerun()
            except Exception as e:
                st.error(f"Erro na predicao: {type(e).__name__}: {e}")

        # Resultado + semáforo + comparacao predito vs real
        if ss.ultima_predicao:
            up = ss.ultima_predicao
            st.markdown("### 📊 Resultado da consulta")

            if up["tipo"] == "classification":
                # Semáforo visual de risco
                cores_semaforo = {
                    "Baixo": ("#1f9e54", "🟢", "Baixo"),
                    "Moderado": ("#E2A015", "🟡", "Moderado"),
                    "Alto": ("#cf2a2a", "🔴", "Alto"),
                    "—": ("#5C6670", "⚪", "Indeterminado"),
                }
                cor_semaforo, emoji_semaforo, label_semaforo = cores_semaforo.get(
                    up["nivel"], cores_semaforo["—"]
                )
                prob_pct = (f"{up['prob']*100:.1f}%"
                            if up["prob"] is not None else "—")

                st.markdown(
                    f"<div style='background:{cor_semaforo}1F;"
                    f"border-left:6px solid {cor_semaforo};border-radius:6px;"
                    f"padding:1rem 1.2rem;margin:0.5rem 0;'>"
                    f"<div style='font-size:2.2rem;line-height:1;'>{emoji_semaforo}</div>"
                    f"<div style='font-size:1.4rem;font-weight:700;color:{cor_semaforo};margin-top:0.3rem;'>"
                    f"Risco {label_semaforo}</div>"
                    f"<div style='color:{BB_TEXTO};margin-top:0.4rem;'>"
                    f"<b>Classe prevista:</b> <code>{up['classe']}</code> "
                    f"&middot; <b>Probabilidade:</b> {prob_pct}</div>"
                    f"<div style='color:{BB_CINZA};margin-top:0.6rem;font-size:0.92rem;'>"
                    f"<b>Ação sugerida:</b> {up['acao']}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                if up["real"] is not None and not pd.isna(up["real"]):
                    real_str = str(up["real"])
                    acertou = (str(up["classe"]).lower() == real_str.lower())
                    badge = "#1f9e54" if acertou else "#cf2a2a"
                    st.markdown(
                        f"<div style='background:{badge}1F;"
                        f"border-left:3px solid {badge};border-radius:4px;"
                        f"padding:0.5rem 0.8rem;margin-top:0.4rem;color:{BB_TEXTO};'>"
                        f"📌 <b>Gabarito (caso de teste):</b> <code>{real_str}</code> · "
                        f"{'✓ modelo acertou' if acertou else '✗ modelo errou'}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
            else:
                pcol1, pcol2, pcol3 = st.columns(3)
                pcol1.metric(f"Previsto ({target})", f"{up['valor']:.2f}")
                if up["real"] is not None and not pd.isna(up["real"]):
                    real = float(up["real"])
                    erro = up["valor"] - real
                    pcol2.metric("Real (gabarito)", f"{real:.2f}")
                    pcol3.metric(
                        "Erro absoluto",
                        f"{abs(erro):.2f}",
                        delta=f"{erro:+.2f}",
                        delta_color="off",
                    )
                if up["rmse"]:
                    st.caption(
                        f"Intervalo tipico: {up['valor'] - up['rmse']:.2f} a "
                        f"{up['valor'] + up['rmse']:.2f} (±RMSE={up['rmse']:.2f})"
                    )

            with st.expander("Ver entradas enviadas ao modelo"):
                st.json(up["valores"])

else:
    st.markdown("---")
    st.info(
        "🔒 A etapa do modelo analitico aparece aqui assim que o agente entregar "
        "o CSV final."
    )
