"""
Demo end-to-end da jornada Predfy — Preparador + Modelo Analítico.

Funciona com QUALQUER CSV. Reproduz no terminal o que o app_agente_bb.py faz
na UI, gerando os mesmos artefatos (CSV final + meta + relatorio HTML/JSON +
interpretacao em PT-BR).

Uso:
    # Modo automatico (auto-detecta tudo)
    python demo_jornada.py --csv dados_sinteticos/contratos.csv

    # Especificando target
    python demo_jornada.py --csv meu.csv --target teve_atraso

    # Pergunta + target + task explicitos
    python demo_jornada.py \\
        --csv dados_sinteticos/eaps.csv \\
        --target prazo_total_dias \\
        --task regression \\
        --pergunta "Quantos dias uma EAP vai demorar?" \\
        --budget 120

    # Listar candidatos a target sem treinar
    python demo_jornada.py --csv meu.csv --inspecionar

Auto-deteccoes:
  - encoding (utf-8, latin-1, cp1252)
  - separador (',' ou ';')
  - target sugerido (binarios "teve_*", "is_*", "_flag"; OU coluna com 2-10
    valores unicos; OU prompts ao usuario)
  - task: binario/categorico = classification, numerico continuo = regression
  - features: tudo menos ID-like (UUIDs, *_id, alta cardinalidade pura), datas
    convertidas para mes/ano, NaNs preenchidos
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "dados_treino"
REPORT_DIR = ROOT / "relatorios"
OUTPUT_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

BB_AMARELO = "#FAE128"
BB_AZUL = "#003DA5"
BB_AZUL_ESCURO = "#002D72"
BB_FUNDO_SUAVE = "#F7F8FA"
BB_CINZA = "#5C6670"

ID_PATTERN = re.compile(r"^id$|_id$|^uuid$|_uuid$|_codigo$", re.IGNORECASE)
TARGET_HINTS = re.compile(
    r"^(teve|tem|is|has|flag|atrasou|rompeu|aprovou|"
    r"target|alvo|y|label|prazo|ruptura|atraso|intercorrencia)",
    re.IGNORECASE,
)


def detectar_separador(amostra: bytes) -> str:
    """Conta candidatos no inicio do arquivo e devolve o mais frequente."""
    candidatos = {",": amostra.count(b","),
                  ";": amostra.count(b";"),
                  "\t": amostra.count(b"\t"),
                  "|": amostra.count(b"|")}
    return max(candidatos, key=candidatos.get) or ","


def carregar_csv(path: Path) -> pd.DataFrame:
    """Le CSV detectando separador (, ; tab |), encoding e BOM."""
    head = path.read_bytes()[:8192]
    sep = detectar_separador(head)
    last_err = None
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252", "iso-8859-1"):
        try:
            df = pd.read_csv(path, sep=sep, encoding=enc, low_memory=False,
                             on_bad_lines="skip")
            # Limpa nomes de coluna (BOM residual, espacos)
            df.columns = [str(c).strip().lstrip("﻿") for c in df.columns]
            return df
        except (UnicodeDecodeError, pd.errors.ParserError) as e:
            last_err = e
    raise RuntimeError(f"Nao consegui ler {path}: {last_err}")


def detectar_id_cols(df: pd.DataFrame) -> list[str]:
    """Colunas que parecem ID (alta cardinalidade ou nome em padrao ID)."""
    ids = []
    for c in df.columns:
        if ID_PATTERN.search(c):
            ids.append(c)
            continue
        if df[c].dtype == "object":
            n_unique = df[c].nunique(dropna=True)
            # >90% unique values + tipo string -> provavelmente ID
            if n_unique > 0 and n_unique / max(len(df), 1) > 0.9:
                ids.append(c)
    return ids


def sugerir_target(df: pd.DataFrame, ids: list[str]) -> list[str]:
    """Lista candidatos a target, priorizados."""
    candidatos = []

    # Prioridade 1: colunas com nome sugestivo (teve_*, is_*, etc)
    # — exclui colunas constantes (1 valor unico) que sao inuteis como target
    for c in df.columns:
        if c in ids:
            continue
        if df[c].nunique(dropna=True) < 2:
            continue
        if TARGET_HINTS.search(c):
            candidatos.append((1, c))

    # Prioridade 2: colunas binarias (2 valores unicos, exclui IDs)
    for c in df.columns:
        if c in ids or c in [x[1] for x in candidatos]:
            continue
        n_unique = df[c].nunique(dropna=True)
        if n_unique == 2:
            candidatos.append((2, c))

    # Prioridade 3: colunas categoricas com baixa cardinalidade (3-10)
    for c in df.columns:
        if c in ids or c in [x[1] for x in candidatos]:
            continue
        n_unique = df[c].nunique(dropna=True)
        if 3 <= n_unique <= 10 and df[c].dtype == "object":
            candidatos.append((3, c))

    # Prioridade 4: colunas numericas continuas
    for c in df.columns:
        if c in ids or c in [x[1] for x in candidatos]:
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            n_unique = df[c].nunique(dropna=True)
            if n_unique > 10:
                candidatos.append((4, c))

    candidatos.sort(key=lambda x: x[0])
    return [c for _, c in candidatos[:10]]


def detectar_task(serie: pd.Series) -> str:
    n_unique = serie.nunique(dropna=True)
    if n_unique <= 10 or not pd.api.types.is_numeric_dtype(serie):
        return "classification"
    return "regression"


def passo_1_inspecionar(df: pd.DataFrame, csv_path: Path) -> dict:
    print("\n=== PASSO 1 — Agente inspeciona o CSV ===")
    print(f"Arquivo:  {csv_path.name}")
    print(f"Linhas:   {len(df):,}")
    print(f"Colunas:  {len(df.columns)}")

    # Detecta colunas de data e converte (ISO YYYY-MM-DD ou PT-BR DD/MM/YYYY)
    datas_detectadas = []
    for c in df.columns:
        if df[c].dtype == "object":
            sample = df[c].dropna().head(20).astype(str)
            iso = any(re.match(r"^\d{4}-\d{2}-\d{2}", s) for s in sample)
            ptbr = any(re.match(r"^\d{2}/\d{2}/\d{4}", s) for s in sample)
            if iso or ptbr:
                try:
                    fmt = None if iso else "%d/%m/%Y"
                    df[c] = pd.to_datetime(df[c], errors="coerce",
                                           format=fmt, dayfirst=ptbr)
                    datas_detectadas.append(c)
                except Exception:
                    pass

    if datas_detectadas:
        print(f"Datas:    {', '.join(datas_detectadas)}")

    ids = detectar_id_cols(df)
    if ids:
        print(f"IDs:      {', '.join(ids)} (serao removidos)")

    return {"ids": ids, "datas": datas_detectadas}


def passo_2_preparar(
    df: pd.DataFrame, target: str, task: str, ids: list[str], datas: list[str]
) -> pd.DataFrame:
    """Reproduz o codigo pandas que o agente teria gerado."""
    print("\n=== PASSO 2 — Agente prepara o CSV final ===")
    work = df.copy()

    # Expande datas em mes/ano
    for c in datas:
        if c == target:
            continue
        if c in work.columns and pd.api.types.is_datetime64_any_dtype(work[c]):
            work[f"{c}_ano"] = work[c].dt.year
            work[f"{c}_mes"] = work[c].dt.month
            work = work.drop(columns=[c])

    # Remove IDs (target nunca e ID)
    for c in ids:
        if c in work.columns and c != target:
            work = work.drop(columns=[c])

    # Limita features de alta cardinalidade categorica (>50 valores unicos)
    cardinalidade_alta = []
    for c in work.columns:
        if c == target:
            continue
        if work[c].dtype == "object" and work[c].nunique() > 50:
            cardinalidade_alta.append(c)
    if cardinalidade_alta:
        print(f"  Removidas (alta cardinalidade): {', '.join(cardinalidade_alta)}")
        work = work.drop(columns=cardinalidade_alta)

    if target not in work.columns:
        raise ValueError(f"Coluna target '{target}' nao encontrada no CSV.")

    # Tratamento de nulos
    for c in work.select_dtypes(include="number").columns:
        work[c] = work[c].fillna(work[c].median())
    for c in work.select_dtypes(include="object").columns:
        work[c] = work[c].fillna("desconhecido")

    # Drop linhas onde target e nulo
    n_antes = len(work)
    work = work.dropna(subset=[target])
    if len(work) < n_antes:
        print(f"  Drop {n_antes - len(work)} linhas com target nulo")

    features = [c for c in work.columns if c != target]
    print(f"  Linhas finais: {len(work):,}")
    print(f"  Features ({len(features)}): {', '.join(features[:6])}"
          + (f", ... +{len(features)-6}" if len(features) > 6 else ""))
    print(f"  Target:        {target} ({task})")
    if task == "classification":
        dist = work[target].value_counts().to_dict()
        print(f"  Distribuicao:  {dist}")
    else:
        s = work[target]
        print(f"  Distribuicao:  min={s.min():.2f} mean={s.mean():.2f} "
              f"max={s.max():.2f}")

    return work


def passo_3_salvar(df: pd.DataFrame, meta: dict, nome_base: str) -> Path:
    print("\n=== PASSO 3 — Agente salva CSV final + sidecar meta ===")
    csv_path = OUTPUT_DIR / f"demo_{nome_base}.csv"
    df.to_csv(csv_path, index=False)
    csv_path.with_suffix(".meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  -> {csv_path}")
    print(f"  -> {csv_path.with_suffix('.meta.json')}")
    return csv_path


def passo_4_treinar(csv_path: Path, meta: dict, budget: int) -> dict:
    print(f"\n=== PASSO 4 — H2O AutoML ({budget}s) ===")
    import h2o
    from h2o.automl import H2OAutoML

    if not h2o.cluster() or not h2o.cluster().is_running():
        print("  Subindo cluster H2O local...")
        h2o.init(max_mem_size="2G", nthreads=-1)

    df_final = pd.read_csv(csv_path)
    target = meta["target"]
    task = meta["task"]

    df_train = df_final.sample(frac=0.8, random_state=42)
    df_test = df_final.drop(df_train.index)

    hf_train = h2o.H2OFrame(df_train)
    hf_test = h2o.H2OFrame(df_test)
    if task == "classification":
        hf_train[target] = hf_train[target].asfactor()
        hf_test[target] = hf_test[target].asfactor()

    features = [c for c in df_final.columns if c != target]
    aml = H2OAutoML(
        max_runtime_secs=budget,
        seed=42,
        sort_metric="AUC" if task == "classification" else "RMSE",
        exclude_algos=["StackedEnsemble", "DeepLearning"],
    )
    aml.train(x=features, y=target, training_frame=hf_train)

    leader = aml.leader
    perf = leader.model_performance(hf_test)

    metrics: dict = {}
    if task == "classification":
        try:
            metrics["AUC"] = float(perf.auc())
        except Exception:
            pass
        try:
            metrics["LogLoss"] = float(perf.logloss())
        except Exception:
            pass
        try:
            metrics["Accuracy"] = float(perf.accuracy()[0][1])
        except Exception:
            pass
    else:
        metrics["RMSE"] = float(perf.rmse())
        metrics["MAE"] = float(perf.mae())
        try:
            metrics["R2"] = float(perf.r2())
        except Exception:
            pass

    varimp_df = None
    try:
        vi = leader.varimp(use_pandas=True)
        if vi is not None:
            varimp_df = vi.head(15)
    except Exception:
        pass

    print(f"  Vencedor: {leader.model_id}")
    for k, v in metrics.items():
        print(f"  {k}: {v:.4f}")

    return {
        "leaderboard": aml.leaderboard.as_data_frame(use_multi_thread=True).head(10),
        "metrics": metrics,
        "varimp": varimp_df,
        "leader_id": str(leader.model_id),
        "task": task,
        "target": target,
        "n_train": len(df_train),
        "n_test": len(df_test),
        "treinado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def passo_5_relatorios(r: dict, meta: dict, nome_base: str) -> tuple[Path, Path]:
    print("\n=== PASSO 5 — Relatorio HTML + JSON ===")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    relatorio = {
        "id": ts,
        "csv_origem": nome_base,
        "pergunta": meta["pergunta"],
        "target": r["target"],
        "task": r["task"],
        "leader_id": r["leader_id"],
        "treinado_em": r["treinado_em"],
        "n_train": r["n_train"],
        "n_test": r["n_test"],
        "metrics": r["metrics"],
        "leaderboard": r["leaderboard"].to_dict(orient="records"),
        "varimp": (r["varimp"].to_dict(orient="records")
                   if r["varimp"] is not None else []),
    }
    json_path = REPORT_DIR / f"demo_{nome_base}_{ts}.json"
    json_path.write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    html = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>Relatorio Demo — {r['leader_id']}</title>
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
</style></head>
<body>
<header>
<h1>Relatorio Analitico (Demo)</h1>
<div style="margin-top:0.4rem;">DISEC · Banco do Brasil · Licitacao Eletronica</div>
<span class="tag" style="margin-top:0.5rem;">HyperCopa DISEC 2026</span>
</header>
<h2>Pergunta de negocio</h2>
<p><strong>{meta['pergunta']}</strong></p>
<p>Origem: <code>{nome_base}</code> · Variavel-alvo: <code>{r['target']}</code> · Tipo: {r['task']}</p>
<h2>Modelo vencedor</h2>
<p><code>{r['leader_id']}</code></p>
<p>Treinado em {r['treinado_em']} · {r['n_train']:,} linhas treino · {r['n_test']:,} linhas teste.</p>
<h2>Metricas no conjunto de teste</h2>
{''.join(f'<div class="metric"><div class="l">{k}</div><div class="v">{v:.4f}</div></div>' for k, v in r['metrics'].items())}
<h2>Leaderboard (top 10)</h2>
{r['leaderboard'].to_html(index=False, float_format='%.4f')}
{('<h2>Importancia das variaveis (top 15)</h2>' + r['varimp'].to_html(index=False, float_format='%.4f')) if r['varimp'] is not None else ''}
</body></html>"""
    html_path = REPORT_DIR / f"demo_{nome_base}_{ts}.html"
    html_path.write_text(html, encoding="utf-8")

    print(f"  -> {json_path}")
    print(f"  -> {html_path}")
    return html_path, json_path


def passo_6_interpretacao(r: dict, meta: dict, nome_base: str) -> Path:
    print("\n=== PASSO 6 — Interpretacao em PT-BR ===")
    metrics = r["metrics"]
    task = r["task"]

    if task == "classification":
        auc = metrics.get("AUC")
        acc = metrics.get("Accuracy")
        if auc is None:
            confianca, lvl = "indeterminada — sem AUC", "?"
        elif auc >= 0.85:
            confianca, lvl = "muito boa — discrimina bem entre as classes", "OK"
        elif auc >= 0.70:
            confianca, lvl = "moderada — apoio a decisao, nao decisao automatica", "OK"
        elif auc >= 0.65:
            confianca, lvl = "fraca — usar so como segunda opiniao", "ATENCAO"
        else:
            confianca, lvl = "INSUFICIENTE — nao colocar em producao", "PARAR"
    else:
        rmse = metrics.get("RMSE")
        r2 = metrics.get("R2")
        if r2 is None:
            confianca, lvl = "indeterminada — sem R2", "?"
        elif r2 >= 0.7:
            confianca, lvl = (f"muito boa — explica {r2*100:.0f}% da variacao", "OK")
        elif r2 >= 0.5:
            confianca, lvl = (f"moderada — explica {r2*100:.0f}% da variacao", "OK")
        elif r2 >= 0.3:
            confianca, lvl = (f"fraca — explica {r2*100:.0f}% da variacao", "ATENCAO")
        else:
            confianca, lvl = ("INSUFICIENTE — modelo nao captura padrao", "PARAR")

    top3 = ""
    if r["varimp"] is not None and len(r["varimp"]) > 0:
        vi = r["varimp"].head(3)
        col = "variable" if "variable" in vi.columns else vi.columns[0]
        top3 = ", ".join(vi[col].tolist())

    md = f"""# Interpretacao do relatorio (Demo)

**Pergunta:** {meta['pergunta']}
**Origem:** `{nome_base}` · **Target:** `{r['target']}` ({task})

**Resumo executivo:** o modelo responde a pergunta com confianca **{confianca}**.

"""
    if task == "classification":
        if metrics.get("AUC") is not None:
            md += f"O **AUC = {metrics['AUC']:.3f}** indica que, ao comparar dois casos aleatorios (um positivo e um negativo), o modelo classifica corretamente em {metrics['AUC']*100:.1f}% das vezes.\n\n"
        if metrics.get("Accuracy") is not None:
            md += f"Acerta **{metrics['Accuracy']*100:.0f}%** das classificacoes individuais.\n\n"
    else:
        if metrics.get("RMSE") is not None:
            md += f"Erro tipico de **±{metrics['RMSE']:.2f}** unidades em torno do valor previsto.\n\n"
        if metrics.get("MAE") is not None:
            md += f"Erro absoluto medio de **{metrics['MAE']:.2f}** unidades.\n\n"

    if top3:
        md += f"**Top 3 fatores mais relevantes:** {top3}.\n\n"

    md += "## Recomendacoes operacionais\n\n"
    if lvl == "OK":
        md += "- Modelo apto para apoio a decisao do gestor de area.\n"
        md += "- Calibrar limiar com a area DICOI/DISEC/DITEC/GECOI antes de operacionalizar.\n"
        md += "- Monitorar mensalmente o drift das variaveis top — reentreinar se desviar.\n"
        md += "- Reentreinar a cada trimestre fiscal.\n"
    elif lvl == "ATENCAO":
        md += "- Usar somente como **segunda opiniao**, nunca como decisao final.\n"
        md += "- Investigar com a area de negocio se faltam variaveis explicativas (mais features podem subir a metrica).\n"
        md += "- Se possivel, ampliar a base de treino antes de promover.\n"
    else:
        md += "- **NAO COLOCAR EM PRODUCAO** com este desempenho.\n"
        md += "- Investigar com a area: a pergunta esta bem formulada? Existem features faltantes?\n"
        md += "- Considerar redefinir o problema ou pedir extrato com mais variaveis preditivas.\n"

    md += f"""
## Aviso

Esta e uma execucao automatica. Antes de operacionalizar:
- Validar com janela temporal recente (out-of-time).
- Revisar com a area se as features fazem sentido causalmente.
- Garantir conformidade com politica BB de classificacao de dados.

---

*Modelo: {r['leader_id']} · Treinado em {r['treinado_em']}*
"""
    interp_path = REPORT_DIR / f"demo_{nome_base}_interpretacao.md"
    interp_path.write_text(md, encoding="utf-8")
    print(f"  -> {interp_path}")
    return interp_path


def main():
    p = argparse.ArgumentParser(
        description="Demo end-to-end da jornada Predfy — Preparador + Modelo Analítico.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--csv", required=True, help="Caminho do CSV de entrada.")
    p.add_argument("--target", help="Coluna alvo. Auto-deteccao se omitido.")
    p.add_argument("--task", choices=["classification", "regression"],
                   help="Tipo de tarefa. Auto-deteccao se omitido.")
    p.add_argument("--pergunta", default="",
                   help="Pergunta preditiva em PT-BR.")
    p.add_argument("--budget", type=int, default=60,
                   help="Tempo de treino H2O em segundos (default 60).")
    p.add_argument("--inspecionar", action="store_true",
                   help="So lista candidatos a target e sai.")
    args = p.parse_args()

    csv_path = Path(args.csv).resolve()
    if not csv_path.exists():
        sys.exit(f"ERRO: CSV nao encontrado: {csv_path}")

    print("=" * 70)
    print("DEMO — JORNADA AGENTE PREPARADOR + MODELO ANALITICO")
    print("=" * 70)
    print(f"CSV: {csv_path}")

    df = carregar_csv(csv_path)
    info = passo_1_inspecionar(df, csv_path)
    ids = info["ids"]
    datas = info["datas"]

    candidatos = sugerir_target(df, ids)

    if args.inspecionar:
        print("\nCandidatos a target (ordenados):")
        for c in candidatos:
            n = df[c].nunique(dropna=True)
            tipo = str(df[c].dtype)
            print(f"  - {c}  (tipo={tipo}, valores unicos={n})")
        return

    target = args.target
    if not target:
        if not candidatos:
            sys.exit("ERRO: nenhum target candidato encontrado. "
                     "Especifique com --target.")
        target = candidatos[0]
        print(f"\nTarget auto-detectado: {target} "
              f"(outros candidatos: {', '.join(candidatos[1:5])})")

    if target not in df.columns:
        sys.exit(f"ERRO: coluna '{target}' nao existe no CSV. "
                 f"Colunas disponiveis: {', '.join(df.columns)}")

    task = args.task or detectar_task(df[target])
    print(f"Task: {task}")

    pergunta = args.pergunta or f"Prever {target}?"
    nome_base = csv_path.stem

    df_final = passo_2_preparar(df, target, task, ids, datas)
    meta = {"pergunta": pergunta, "target": target, "task": task}

    csv_out = passo_3_salvar(df_final, meta, nome_base)
    r = passo_4_treinar(csv_out, meta, budget=args.budget)
    html_path, json_path = passo_5_relatorios(r, meta, nome_base)
    interp_path = passo_6_interpretacao(r, meta, nome_base)

    print("\n" + "=" * 70)
    print("CONCLUIDO")
    print("=" * 70)
    print(f"\nArtefatos:")
    print(f"  CSV final         {csv_out}")
    print(f"  Relatorio HTML    {html_path}")
    print(f"  Relatorio JSON    {json_path}")
    print(f"  Interpretacao     {interp_path}")
    print(f"\nMetricas:")
    for k, v in r["metrics"].items():
        print(f"  {k:10s} {v:.4f}")


if __name__ == "__main__":
    main()
