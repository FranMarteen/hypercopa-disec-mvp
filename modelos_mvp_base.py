"""
============================================================================
HyperCopa DISEC 2026 — Modelos MVP Base (aprovados)
CESUP-Contratações | Banco do Brasil
============================================================================

3 modelos obrigatórios do plano aprovado:

  Modelo 1: ANÁLISE DE RECORRÊNCIA (K-Means)
    Pergunta: "Quais compras se repetem e poderiam virar contrato continuado?"
    Tipo:     Clustering (não supervisionado)
    Técnica:  K-Means no H2O

  Modelo 2: DETECÇÃO DE ANOMALIAS (Isolation Forest)
    Pergunta: "Quais processos estão fora do padrão e merecem atenção?"
    Tipo:     Detecção de anomalias (não supervisionado)
    Técnica:  Isolation Forest no H2O

  Modelo 3: CONCENTRAÇÃO DE FORNECEDORES (HHI)
    Pergunta: "Estamos dependentes demais de poucos fornecedores?"
    Tipo:     Cálculo estatístico (índice HHI)
    Técnica:  Herfindahl-Hirschman + visualização

Os outputs são exportados em CSV para consumo pelo Time 2 (Agente IA).
============================================================================
"""

import h2o
from h2o.estimators import H2OKMeansEstimator, H2OIsolationForestEstimator
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

OUTPUT_DIR = "./dados_sinteticos"


def print_secao(titulo):
    print("\n" + "=" * 80)
    print(titulo)
    print("=" * 80)


def print_subsecao(titulo):
    print("\n" + "-" * 60)
    print(titulo)
    print("-" * 60)


# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

print_secao("INICIALIZACAO DO H2O")
h2o.init(max_mem_size="2G", nthreads=-1)

# ============================================================================
# CARREGAR DADOS
# ============================================================================

print_secao("CARREGANDO DADOS")

df_eaps = pd.read_csv(f"{OUTPUT_DIR}/eaps.csv")
df_fornecedores = pd.read_csv(f"{OUTPUT_DIR}/fornecedores.csv")
df_contratos = pd.read_csv(f"{OUTPUT_DIR}/contratos.csv")

print(f"EAPs:          {len(df_eaps)} registros")
print(f"Fornecedores:  {len(df_fornecedores)} registros")
print(f"Contratos:     {len(df_contratos)} registros")

# Filtrar concluídos para modelos 1 e 2
df_conc = df_eaps[df_eaps["status"] == "Concluído"].copy()
print(f"Concluídos:    {len(df_conc)} registros (usados nos modelos 1 e 2)")


# ============================================================================
#
#   MODELO 1: ANÁLISE DE RECORRÊNCIA (K-Means)
#   "Quais compras se repetem e poderiam virar contrato continuado?"
#
# ============================================================================

print_secao("MODELO 1: ANALISE DE RECORRENCIA (K-Means)")

# ---------------------------------------------------------------------------
# Passo 1: Escolher features
# ---------------------------------------------------------------------------
print_subsecao("Passo 1: Escolher features a partir da pergunta")

print("""
  PERGUNTA: "Quais compras se repetem e poderiam virar contrato continuado?"

  Para identificar recorrência, precisamos de features que revelem
  PADRÕES DE REPETIÇÃO:
    - O QUE se compra (tipo de serviço)
    - QUEM pede (unidade demandante)
    - QUANDO pede (trimestre — sazonalidade)
    - QUANTO custa (faixa de valor)
    - COM QUE FREQUÊNCIA (quantas vezes no período)

  O K-Means agrupa processos SIMILARES nessas dimensões.
  Se um cluster mostra "TI-Infra + DITEC + todo trimestre + ~R$ 200k",
  é candidato claro a contrato continuado.

  IMPORTANTE: K-Means só trabalha com variáveis numéricas.
  Categóricas precisam ser transformadas antes.
""")

# Criar features de recorrência
df_rec = df_conc.copy()
df_rec["log_valor"] = np.log(df_rec["valor_estimado"])
df_rec["trimestre"] = pd.to_datetime(df_rec["dt_abertura"]).dt.quarter
df_rec["mes"] = pd.to_datetime(df_rec["dt_abertura"]).dt.month
df_rec["ano"] = pd.to_datetime(df_rec["dt_abertura"]).dt.year

# Contar frequência: quantas vezes a mesma combinação tipo_servico+unidade aparece
freq = df_rec.groupby(["tipo_servico", "unidade_demandante"]).size().reset_index(name="frequencia")
df_rec = df_rec.merge(freq, on=["tipo_servico", "unidade_demandante"], how="left")

features_m1 = [
    "log_valor",
    "prazo_total_dias",
    "num_participantes",
    "trimestre",
    "frequencia",
]

print(f"  Features: {features_m1}")
print(f"  Registros: {len(df_rec)}")

# ---------------------------------------------------------------------------
# Passo 2: Treinar K-Means
# ---------------------------------------------------------------------------
print_subsecao("Passo 2: Encontrar K ideal (Método do Cotovelo)")

hf_m1 = h2o.H2OFrame(df_rec[features_m1])

resultados_k = []
for k in range(2, 10):
    km = H2OKMeansEstimator(k=k, standardize=True, seed=42, max_iterations=100)
    km.train(x=features_m1, training_frame=hf_m1)
    within = km.tot_withinss()
    total = km.totss()
    resultados_k.append({"k": k, "within_ss": within, "ratio": (total - within) / total})

print(f"\n  {'K':>3}  {'Within SS':>12}  {'Ratio':>8}  {'Ganho':>8}")
for i, r in enumerate(resultados_k):
    ganho = ""
    if i > 0:
        g = r["ratio"] - resultados_k[i - 1]["ratio"]
        ganho = f"+{g:.3f}"
    print(f"  {r['k']:>3}  {r['within_ss']:>12.1f}  {r['ratio']:>8.3f}  {ganho:>8}")

# ---------------------------------------------------------------------------
# Passo 3: Treinar modelo final
# ---------------------------------------------------------------------------
print_subsecao("Passo 3: Treinar K-Means final (K=5)")

K_FINAL = 5
modelo_m1 = H2OKMeansEstimator(
    k=K_FINAL,
    standardize=True,
    seed=42,
    max_iterations=100,
    model_id="kmeans_recorrencia_v1",
)
modelo_m1.train(x=features_m1, training_frame=hf_m1)

totss = modelo_m1.totss()
withinss = modelo_m1.tot_withinss()
betweenss = modelo_m1.betweenss()

print(f"\n  Total SS:   {totss:,.0f}")
print(f"  Within SS:  {withinss:,.0f}")
print(f"  Between SS: {betweenss:,.0f}")
print(f"  Ratio:      {betweenss/totss:.3f}")

# Atribuir clusters
pred_m1 = modelo_m1.predict(hf_m1)
df_rec["cluster"] = h2o.as_list(pred_m1)["predict"].values

# ---------------------------------------------------------------------------
# Passo 4: Interpretar clusters
# ---------------------------------------------------------------------------
print_subsecao("Passo 4: Interpretar os clusters (perfil de recorrência)")

print("\n  Perfil numérico:")
perfil = df_rec.groupby("cluster").agg(
    qtd=("eap_id", "count"),
    valor_medio=("valor_estimado", "mean"),
    prazo_medio=("prazo_total_dias", "mean"),
    participantes=("num_participantes", "mean"),
    frequencia_media=("frequencia", "mean"),
).round(1)
print(perfil.to_string())

print("\n  Top tipo de serviço por cluster:")
for cl in sorted(df_rec["cluster"].unique()):
    sub = df_rec[df_rec["cluster"] == cl]
    top = sub["tipo_servico"].value_counts().head(3)
    print(f"\n  Cluster {cl} ({len(sub)} processos):")
    for ts, n in top.items():
        print(f"    {ts:<35} {n:>4} ({n/len(sub):.0%})")

# Identificar clusters com alta recorrência
print("\n  CANDIDATOS A CONTRATO CONTINUADO:")
for cl in sorted(df_rec["cluster"].unique()):
    sub = df_rec[df_rec["cluster"] == cl]
    freq_media = sub["frequencia"].mean()
    if freq_media > df_rec["frequencia"].median():
        top_ts = sub["tipo_servico"].value_counts().index[0]
        top_ud = sub["unidade_demandante"].value_counts().index[0]
        val_med = sub["valor_estimado"].median()
        print(f"    Cluster {cl}: freq={freq_media:.0f} compras/combinação | "
              f"ex: {top_ts} para {top_ud} (~R$ {val_med:,.0f})")

# ---------------------------------------------------------------------------
# Passo 5: Exportar
# ---------------------------------------------------------------------------
print_subsecao("Passo 5: Exportar output para Time 2")

output_m1 = df_rec[[
    "eap_id", "cluster", "eap_padrao", "tipo_servico",
    "unidade_demandante", "valor_estimado", "prazo_total_dias",
    "num_participantes", "trimestre", "frequencia",
    "fornecedor_vencedor_id", "fornecedor_vencedor_nome",
]].copy()
output_m1.to_csv(f"{OUTPUT_DIR}/output_recorrencia.csv", index=False)
print(f"  Exportado: {OUTPUT_DIR}/output_recorrencia.csv ({len(output_m1)} registros)")


# ============================================================================
#
#   MODELO 2: DETECÇÃO DE ANOMALIAS (Isolation Forest)
#   "Quais processos estão fora do padrão e merecem atenção?"
#
# ============================================================================

print_secao("MODELO 2: DETECÇÃO DE ANOMALIAS (Isolation Forest)")

# ---------------------------------------------------------------------------
# Passo 1: Entender a técnica
# ---------------------------------------------------------------------------
print_subsecao("Passo 1: Entender Isolation Forest")

print("""
  PERGUNTA: "Quais processos estão fora do padrão?"

  Isolation Forest é uma técnica de detecção de anomalias:
    1. Constrói árvores de decisão ALEATÓRIAS
    2. Em cada árvore, escolhe uma feature e um ponto de corte aleatório
    3. Pontos NORMAIS precisam de muitos cortes para serem isolados
    4. Pontos ANÔMALOS são isolados com POUCOS cortes (são diferentes)

  O score de anomalia vai de 0 a 1:
    ~0.0 = muito normal (precisa de muitos cortes)
    ~0.5 = ambíguo
    ~1.0 = muito anômalo (isolado rapidamente)

  Diferente do K-Means, não precisamos definir K.
  O modelo aprende o que é "normal" e sinaliza o que desvia.

  FEATURES: aqui queremos detectar desvios em MÚLTIPLAS dimensões.
  Um processo pode ser normal no valor mas anômalo no prazo,
  ou normal em tudo mas com desconto atípico.
""")

# ---------------------------------------------------------------------------
# Passo 2: Escolher features
# ---------------------------------------------------------------------------
print_subsecao("Passo 2: Escolher features para detecção de anomalias")

df_anom = df_conc.copy()
df_anom["log_valor"] = np.log(df_anom["valor_estimado"])
df_anom["desconto_pct"] = (
    (df_anom["valor_estimado"] - df_anom["valor_contratado"])
    / df_anom["valor_estimado"] * 100
).round(2)

features_m2 = [
    "log_valor",           # Valor fora do padrão?
    "prazo_total_dias",    # Prazo atípico?
    "num_participantes",   # Poucos/muitos participantes?
    "desconto_pct",        # Desconto anormal?
    "num_etapas",          # Fluxo incomum?
]

print(f"""
  Features selecionadas: {features_m2}

  Por que essas?
    log_valor         → Processo com valor muito acima/abaixo da média
    prazo_total_dias  → Processo muito rápido ou muito lento
    num_participantes → Certame sem competição (1 participante) ou incomum
    desconto_pct      → Desconto muito alto (possível conluio?) ou zero
    num_etapas        → Número de etapas diferente do padrão da EAP

  O Isolation Forest detecta combinações atípicas:
    ex: valor alto + poucos participantes + desconto zero = FLAG
""")

# ---------------------------------------------------------------------------
# Passo 3: Treinar Isolation Forest
# ---------------------------------------------------------------------------
print_subsecao("Passo 3: Treinar Isolation Forest")

hf_m2 = h2o.H2OFrame(df_anom[features_m2])

modelo_m2 = H2OIsolationForestEstimator(
    model_id="iforest_anomalias_v1",
    ntrees=100,
    max_depth=8,
    sample_size=256,      # Tamanho da amostra por árvore (padrão do paper original)
    seed=42,
)
modelo_m2.train(x=features_m2, training_frame=hf_m2)

print("  Modelo treinado com sucesso.")
print(f"  Árvores: {modelo_m2.params['ntrees']['actual']}")
print(f"  Profundidade máxima: {modelo_m2.params['max_depth']['actual']}")

# ---------------------------------------------------------------------------
# Passo 4: Calcular scores de anomalia
# ---------------------------------------------------------------------------
print_subsecao("Passo 4: Calcular scores de anomalia")

pred_m2 = modelo_m2.predict(hf_m2)
df_anom["anomaly_score"] = h2o.as_list(pred_m2)["mean_length"].values

# Normalizar o score: mean_length menor = mais anômalo
# Inverter para que score alto = mais anômalo (mais intuitivo)
max_len = df_anom["anomaly_score"].max()
min_len = df_anom["anomaly_score"].min()
df_anom["anomaly_score_norm"] = 1 - (
    (df_anom["anomaly_score"] - min_len) / (max_len - min_len)
)

print(f"""
  Score de anomalia (normalizado 0-1, onde 1 = mais anômalo):
    Média:   {df_anom['anomaly_score_norm'].mean():.3f}
    Mediana: {df_anom['anomaly_score_norm'].median():.3f}
    Std:     {df_anom['anomaly_score_norm'].std():.3f}
    Min:     {df_anom['anomaly_score_norm'].min():.3f}
    Max:     {df_anom['anomaly_score_norm'].max():.3f}
""")

# Definir threshold: top 10% são anomalias
threshold = df_anom["anomaly_score_norm"].quantile(0.90)
df_anom["is_anomaly"] = df_anom["anomaly_score_norm"] >= threshold
n_anomalias = df_anom["is_anomaly"].sum()

print(f"  Threshold (percentil 90): {threshold:.3f}")
print(f"  Processos anômalos: {n_anomalias} ({n_anomalias/len(df_anom):.1%})")

# ---------------------------------------------------------------------------
# Passo 5: Analisar as anomalias
# ---------------------------------------------------------------------------
print_subsecao("Passo 5: Quem são os processos anômalos?")

anomalos = df_anom[df_anom["is_anomaly"]].copy()
normais = df_anom[~df_anom["is_anomaly"]].copy()

print("\n  Comparação: ANOMALOS vs NORMAIS")
print(f"  {'Métrica':<25} {'Normais':>12} {'Anômalos':>12} {'Razão':>8}")
for feat in ["valor_estimado", "prazo_total_dias", "num_participantes", "desconto_pct"]:
    m_norm = normais[feat].mean()
    m_anom = anomalos[feat].mean()
    razao = m_anom / m_norm if m_norm > 0 else 0
    if feat == "valor_estimado":
        print(f"  {feat:<25} R$ {m_norm:>9,.0f} R$ {m_anom:>9,.0f} {razao:>7.1f}x")
    else:
        print(f"  {feat:<25} {m_norm:>12.1f} {m_anom:>12.1f} {razao:>7.1f}x")

print("\n  Top 10 processos MAIS anômalos:")
top_anom = anomalos.nlargest(10, "anomaly_score_norm")
print(f"  {'EAP ID':<20} {'EAP Padrao':<35} {'Valor R$':>12} {'Prazo':>6} {'Part':>5} {'Score':>6}")
for _, row in top_anom.iterrows():
    print(f"  {row['eap_id']:<20} {row['eap_padrao']:<35} "
          f"{row['valor_estimado']:>12,.0f} {row['prazo_total_dias']:>5.0f}d "
          f"{row['num_participantes']:>5} {row['anomaly_score_norm']:>5.2f}")

print("\n  POR QUE são anômalos?")
print("  O Isolation Forest não dá uma 'explicação' direta, mas podemos")
print("  comparar cada processo anômalo com a média para entender o desvio:")
for _, row in top_anom.head(3).iterrows():
    print(f"\n  {row['eap_id']}:")
    for feat, label in [("valor_estimado", "Valor"), ("prazo_total_dias", "Prazo"),
                         ("num_participantes", "Participantes"), ("desconto_pct", "Desconto")]:
        media = normais[feat].mean()
        val = row[feat]
        desvio = (val - media) / normais[feat].std()
        flag = " <<<" if abs(desvio) > 2 else ""
        if feat == "valor_estimado":
            print(f"    {label:<15} R$ {val:>12,.0f}  (média R$ {media:>10,.0f}, desvio {desvio:>+.1f}σ){flag}")
        else:
            print(f"    {label:<15} {val:>12.1f}  (média {media:>10.1f}, desvio {desvio:>+.1f}σ){flag}")

# ---------------------------------------------------------------------------
# Passo 6: Exportar
# ---------------------------------------------------------------------------
print_subsecao("Passo 6: Exportar output para Time 2")

output_m2 = df_anom[[
    "eap_id", "eap_padrao", "categoria_contratacao", "tipo_servico",
    "unidade_demandante", "valor_estimado", "valor_contratado",
    "prazo_total_dias", "num_participantes", "desconto_pct",
    "fornecedor_vencedor_id", "fornecedor_vencedor_nome",
    "anomaly_score_norm", "is_anomaly",
]].copy()
output_m2.columns = [
    "eap_id", "eap_padrao", "categoria", "tipo_servico",
    "unidade", "valor_estimado", "valor_contratado",
    "prazo_dias", "participantes", "desconto_pct",
    "fornecedor_id", "fornecedor_nome",
    "score_anomalia", "flag_anomalia",
]
output_m2 = output_m2.sort_values("score_anomalia", ascending=False)
output_m2.to_csv(f"{OUTPUT_DIR}/output_anomalias.csv", index=False)
print(f"  Exportado: {OUTPUT_DIR}/output_anomalias.csv ({len(output_m2)} registros)")
print(f"  Anomalias flagadas: {output_m2['flag_anomalia'].sum()}")


# ============================================================================
#
#   MODELO 3: CONCENTRAÇÃO DE FORNECEDORES (HHI)
#   "Estamos dependentes demais de poucos fornecedores?"
#
# ============================================================================

print_secao("MODELO 3: CONCENTRACAO DE FORNECEDORES (HHI)")

# ---------------------------------------------------------------------------
# Passo 1: Entender o HHI
# ---------------------------------------------------------------------------
print_subsecao("Passo 1: Entender o Índice HHI")

print("""
  PERGUNTA: "Estamos dependentes demais de poucos fornecedores?"

  O HHI (Herfindahl-Hirschman Index) mede concentração de mercado.
  É usado pelo CADE, pelo DOJ americano e por reguladores do mundo todo.

  CÁLCULO:
    1. Para cada categoria, calcular a % de cada fornecedor no volume total
    2. Elevar cada % ao quadrado
    3. Somar

  INTERPRETAÇÃO:
    HHI < 1.500    → Baixa concentração (mercado competitivo)
    1.500 - 2.500  → Moderada (atenção)
    HHI > 2.500    → Alta concentração (risco de dependência)
    HHI = 10.000   → Monopólio (um único fornecedor tem 100%)

  EXEMPLO:
    Categoria "Segurança" com 3 fornecedores:
      Fornecedor A: 70% do volume → 70² = 4.900
      Fornecedor B: 20% do volume → 20² =   400
      Fornecedor C: 10% do volume → 10² =   100
      HHI = 5.400 → ALTA concentração

  Este NÃO é um modelo de ML — é cálculo estatístico direto.
  Mas é poderoso porque o resultado é imediatamente acionável.
""")

# ---------------------------------------------------------------------------
# Passo 2: Calcular HHI por tipo de serviço
# ---------------------------------------------------------------------------
print_subsecao("Passo 2: Calcular HHI por tipo de serviço")

# Usar contratos para ter o volume real por fornecedor
df_hhi = df_contratos[["tipo_servico", "fornecedor_id", "fornecedor_nome", "valor_contratado"]].copy()

# Volume total por categoria
vol_categoria = df_hhi.groupby("tipo_servico")["valor_contratado"].sum()

# Volume por fornecedor por categoria
vol_forn_cat = df_hhi.groupby(["tipo_servico", "fornecedor_id", "fornecedor_nome"])["valor_contratado"].sum().reset_index()

# Market share de cada fornecedor
vol_forn_cat["market_share_pct"] = vol_forn_cat.apply(
    lambda row: row["valor_contratado"] / vol_categoria[row["tipo_servico"]] * 100,
    axis=1
)

# HHI por categoria
vol_forn_cat["share_squared"] = vol_forn_cat["market_share_pct"] ** 2
hhi_por_cat = vol_forn_cat.groupby("tipo_servico")["share_squared"].sum().reset_index()
hhi_por_cat.columns = ["tipo_servico", "hhi"]
hhi_por_cat["hhi"] = hhi_por_cat["hhi"].round(0)

# Classificação
def classificar_hhi(val):
    if val < 1500:
        return "Baixa"
    elif val < 2500:
        return "Moderada"
    else:
        return "Alta"

hhi_por_cat["classificacao"] = hhi_por_cat["hhi"].apply(classificar_hhi)

# Número de fornecedores por categoria
n_forn = vol_forn_cat.groupby("tipo_servico")["fornecedor_id"].nunique().reset_index()
n_forn.columns = ["tipo_servico", "num_fornecedores"]
hhi_por_cat = hhi_por_cat.merge(n_forn, on="tipo_servico")

# Volume total
vol_total = vol_categoria.reset_index()
vol_total.columns = ["tipo_servico", "volume_total"]
hhi_por_cat = hhi_por_cat.merge(vol_total, on="tipo_servico")

# Top fornecedor
top_forn = vol_forn_cat.sort_values("market_share_pct", ascending=False).groupby("tipo_servico").first().reset_index()
top_forn = top_forn[["tipo_servico", "fornecedor_nome", "market_share_pct"]]
top_forn.columns = ["tipo_servico", "top_fornecedor", "top_share_pct"]
hhi_por_cat = hhi_por_cat.merge(top_forn, on="tipo_servico")

hhi_por_cat = hhi_por_cat.sort_values("hhi", ascending=False)

print(f"\n  {'Tipo de Serviço':<30} {'HHI':>6} {'Class':<10} {'Fornec':>6} {'Top Fornecedor':<30} {'Share':>6}")
for _, row in hhi_por_cat.iterrows():
    print(f"  {row['tipo_servico']:<30} {row['hhi']:>6.0f} {row['classificacao']:<10} "
          f"{row['num_fornecedores']:>6} {row['top_fornecedor']:<30} {row['top_share_pct']:>5.1f}%")

# Resumo
n_alta = (hhi_por_cat["classificacao"] == "Alta").sum()
n_mod = (hhi_por_cat["classificacao"] == "Moderada").sum()
n_baixa = (hhi_por_cat["classificacao"] == "Baixa").sum()
print(f"\n  Resumo: {n_alta} categorias Alta | {n_mod} Moderada | {n_baixa} Baixa concentração")

# ---------------------------------------------------------------------------
# Passo 3: Detalhar categorias de ALTA concentração
# ---------------------------------------------------------------------------
print_subsecao("Passo 3: Detalhar categorias de ALTA concentração")

cats_alta = hhi_por_cat[hhi_por_cat["classificacao"] == "Alta"]["tipo_servico"].tolist()

for cat in cats_alta:
    forn_cat = vol_forn_cat[vol_forn_cat["tipo_servico"] == cat].sort_values("market_share_pct", ascending=False)
    hhi_val = hhi_por_cat[hhi_por_cat["tipo_servico"] == cat]["hhi"].values[0]
    print(f"\n  {cat} (HHI = {hhi_val:,.0f}):")
    print(f"  {'Fornecedor':<35} {'Volume R$':>12} {'Share':>6}")
    for _, row in forn_cat.head(5).iterrows():
        print(f"    {row['fornecedor_nome']:<35} {row['valor_contratado']:>12,.0f} {row['market_share_pct']:>5.1f}%")

# ---------------------------------------------------------------------------
# Passo 4: Gerar mapa de calor
# ---------------------------------------------------------------------------
print_subsecao("Passo 4: Gerar visualização (mapa de calor)")

fig, axes = plt.subplots(1, 2, figsize=(18, 8))

# Gráfico 1: HHI por categoria (barras horizontais)
hhi_sorted = hhi_por_cat.sort_values("hhi")
colors_bar = []
for _, row in hhi_sorted.iterrows():
    if row["classificacao"] == "Alta":
        colors_bar.append("#e74c3c")
    elif row["classificacao"] == "Moderada":
        colors_bar.append("#f39c12")
    else:
        colors_bar.append("#2ecc71")

axes[0].barh(hhi_sorted["tipo_servico"], hhi_sorted["hhi"], color=colors_bar, edgecolor="white")
axes[0].axvline(x=1500, color="orange", linestyle="--", alpha=0.7, label="Moderada (1.500)")
axes[0].axvline(x=2500, color="red", linestyle="--", alpha=0.7, label="Alta (2.500)")
axes[0].set_xlabel("HHI", fontsize=12)
axes[0].set_title("Concentração por Tipo de Serviço", fontsize=13)
axes[0].legend(fontsize=9)

# Gráfico 2: HHI vs número de fornecedores (scatter)
for _, row in hhi_por_cat.iterrows():
    c = "#e74c3c" if row["classificacao"] == "Alta" else "#f39c12" if row["classificacao"] == "Moderada" else "#2ecc71"
    axes[1].scatter(row["num_fornecedores"], row["hhi"], c=c, s=row["volume_total"] / 1e6 + 20,
                    alpha=0.7, edgecolors="black", linewidth=0.5)
    if row["hhi"] > 2000:
        axes[1].annotate(row["tipo_servico"], (row["num_fornecedores"] + 0.3, row["hhi"]),
                         fontsize=7)
axes[1].axhline(y=1500, color="orange", linestyle="--", alpha=0.5)
axes[1].axhline(y=2500, color="red", linestyle="--", alpha=0.5)
axes[1].set_xlabel("Número de Fornecedores", fontsize=12)
axes[1].set_ylabel("HHI", fontsize=12)
axes[1].set_title("HHI vs Diversidade de Fornecedores\n(tamanho = volume R$)", fontsize=13)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/hhi_concentracao.png", dpi=150, bbox_inches="tight", facecolor="white")
plt.close()
print(f"  Gráfico salvo: {OUTPUT_DIR}/hhi_concentracao.png")

# ---------------------------------------------------------------------------
# Passo 5: Exportar
# ---------------------------------------------------------------------------
print_subsecao("Passo 5: Exportar output para Time 2")

output_m3 = hhi_por_cat[[
    "tipo_servico", "hhi", "classificacao", "num_fornecedores",
    "volume_total", "top_fornecedor", "top_share_pct",
]].copy()
output_m3.to_csv(f"{OUTPUT_DIR}/output_hhi.csv", index=False)
print(f"  Exportado: {OUTPUT_DIR}/output_hhi.csv ({len(output_m3)} categorias)")

# Exportar detalhamento por fornecedor
vol_forn_cat.to_csv(f"{OUTPUT_DIR}/output_hhi_detalhado.csv", index=False)
print(f"  Exportado: {OUTPUT_DIR}/output_hhi_detalhado.csv ({len(vol_forn_cat)} registros)")


# ============================================================================
# RESUMO FINAL
# ============================================================================

print_secao("RESUMO DOS 3 MODELOS MVP BASE")

print(f"""
  Modelo 1 — Recorrência (K-Means, K={K_FINAL})
    Ratio (Between/Total): {betweenss/totss:.3f}
    Clusters: {K_FINAL} perfis de recorrência identificados
    Output: output_recorrencia.csv

  Modelo 2 — Anomalias (Isolation Forest)
    Threshold: {threshold:.3f} (percentil 90)
    Anomalias detectadas: {n_anomalias} processos ({n_anomalias/len(df_anom):.1%})
    Output: output_anomalias.csv

  Modelo 3 — Concentração HHI
    Categorias com alta concentração: {n_alta} de {len(hhi_por_cat)}
    Output: output_hhi.csv + output_hhi_detalhado.csv

  Todos os outputs estão prontos para o Time 2 (Agente IA).
""")

h2o.cluster().shutdown(prompt=False)
print("H2O encerrado.")
