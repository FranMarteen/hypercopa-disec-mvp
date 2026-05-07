"""
Gera um CSV de demonstracao de EAPs (Eventos de Contratacao / Licitacao
Eletronica) para o notebook_h2o_agente_mvp.ipynb rodar ponta a ponta.

Salva em:
  dados_treino/demo_eaps_vai_atrasar.csv
  dados_treino/demo_eaps_vai_atrasar.meta.json

Pergunta preditiva: "Essa EAP vai atrasar?"  (classification, target = vai_atrasar)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "dados_treino"
OUT_DIR.mkdir(exist_ok=True)

rng = np.random.default_rng(seed=42)
N = 1500

unidades = [
    "DISEC-COMPRAS", "DISEC-CONTRATOS", "DITEC-INFRA",
    "GEINS-CO", "GEINS-NE", "GEINS-NORTE",
    "SUREF-SP1", "SUREF-RJ", "SUREF-DF",
    "SUREF-MG", "SUREF-RS", "SUREF-PE",
]
tipos_servico = ["Bens", "Engenharia - Servicos", "Servicos Diversos", "Tecnica E Preco"]
complexidades = ["Baixa", "Media", "Alta"]
urgencias = ["Normal", "Urgente"]
status_list = ["Em Andamento", "Concluido", "Cancelado", "Suspenso", "Devolvido"]

df = pd.DataFrame({
    "modalidade":          ["Licitacao Eletronica"] * N,
    "tipo_servico":        rng.choice(tipos_servico, size=N, p=[0.45, 0.25, 0.20, 0.10]),
    "unidade_demandante":  rng.choice(unidades, size=N),
    "valor_estimado":      np.round(rng.lognormal(mean=12.5, sigma=1.2, size=N), 2),
    "num_etapas":          rng.integers(low=8, high=13, size=N),
    "num_participantes":   rng.integers(low=3, high=13, size=N),
    "tem_intercorrencia":  rng.choice(["Nao", "Sim"], size=N, p=[0.78, 0.22]),
    "urgencia":            rng.choice(urgencias, size=N, p=[0.80, 0.20]),
    "complexidade":        rng.choice(complexidades, size=N, p=[0.30, 0.45, 0.25]),
    "status":              rng.choice(status_list, size=N, p=[0.55, 0.30, 0.07, 0.05, 0.03]),
    "dt_abertura_ano":     rng.choice([2022, 2023, 2024, 2025, 2026], size=N, p=[0.10, 0.20, 0.30, 0.30, 0.10]),
    "dt_abertura_mes":     rng.integers(low=1, high=13, size=N),
    "etapas_duracao_media": np.round(rng.uniform(low=4.0, high=18.0, size=N), 2),
    "etapas_interrompidas": rng.binomial(n=1, p=0.18, size=N),
})

# Risco latente (combinacao linear que dirige a probabilidade de atraso)
risco = (
    0.45 * (df["tem_intercorrencia"] == "Sim").astype(int)
    + 0.25 * (df["complexidade"] == "Alta").astype(int)
    + 0.18 * (df["complexidade"] == "Media").astype(int)
    + 0.30 * (df["etapas_interrompidas"] == 1).astype(int)
    + 0.20 * (df["urgencia"] == "Urgente").astype(int)
    + 0.10 * (df["tipo_servico"] == "Engenharia - Servicos").astype(int)
    + 0.05 * (df["num_participantes"] < 5).astype(int)
    + 0.04 * (df["valor_estimado"] > df["valor_estimado"].quantile(0.85)).astype(int)
    - 0.30 * (df["status"] == "Concluido").astype(int)   # ja concluiu sem atrasar = -
    + 0.08 * (df["status"] == "Suspenso").astype(int)
)
prob = 1 / (1 + np.exp(-(risco - 0.45) * 3))   # sigmoide
prob = np.clip(prob + rng.normal(0, 0.05, size=N), 0.0, 1.0)
df["vai_atrasar"] = (rng.random(size=N) < prob).astype(int).map({0: "Nao", 1: "Sim"}).values

csv_path  = OUT_DIR / "demo_eaps_vai_atrasar.csv"
meta_path = OUT_DIR / "demo_eaps_vai_atrasar.meta.json"
df.to_csv(csv_path, index=False, encoding="utf-8")
meta_path.write_text(json.dumps({
    "pergunta": "Essa EAP vai atrasar?",
    "target":   "vai_atrasar",
    "task":     "classification",
}, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"OK  {csv_path.name}  -  {len(df):,} linhas x {len(df.columns)} colunas")
print(f"    distribuicao do target:")
print(df["vai_atrasar"].value_counts(normalize=True).round(3).to_string())
print(f"OK  {meta_path.name}")
