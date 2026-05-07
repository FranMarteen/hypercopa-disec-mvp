"""
============================================================================
HyperCopa DISEC 2026 — 3 Modelos Preditivos
CESUP-Contratações | Banco do Brasil
============================================================================

Este script treina, avalia e exporta os 3 modelos do MVP:

  Modelo 1: REGRESSÃO DE PRAZO
    Pergunta: "Quanto tempo meu processo vai levar?"
    Target:   prazo_total_dias (número contínuo)
    Tipo:     Regressão

  Modelo 2: CLASSIFICAÇÃO DE INTERCORRÊNCIA
    Pergunta: "Qual a chance de ter impugnação ou recurso?"
    Target:   tem_intercorrencia (True/False)
    Tipo:     Classificação binária

  Modelo 3: CLASSIFICAÇÃO DE RUPTURA CONTRATUAL
    Pergunta: "Esse contrato tem risco de rescisão?"
    Target:   teve_rescisao (True/False)
    Tipo:     Classificação binária

Cada modelo usa GBM (Gradient Boosting Machine) do H2O.
============================================================================
"""

import h2o
from h2o.estimators import H2OGradientBoostingEstimator
import pandas as pd
import numpy as np
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
# CARREGAR E PREPARAR DADOS
# ============================================================================

print_secao("CARREGANDO DADOS")

df_eaps = pd.read_csv(f"{OUTPUT_DIR}/eaps.csv")
df_contratos = pd.read_csv(f"{OUTPUT_DIR}/contratos.csv")

print(f"EAPs:      {len(df_eaps)} registros")
print(f"Contratos: {len(df_contratos)} registros")


# ============================================================================
#
#   MODELO 1: REGRESSÃO DE PRAZO
#   "Quanto tempo meu processo vai levar?"
#
# ============================================================================

print_secao("MODELO 1: REGRESSAO DE PRAZO")

# ---------------------------------------------------------------------------
# PASSO 1: Entender a pergunta e escolher features
# ---------------------------------------------------------------------------
print_subsecao("Passo 1: Escolher features a partir da pergunta")

print("""
  PERGUNTA: "Quanto tempo meu processo vai levar?"

  O que o demandante SABE quando abre o ticket:
    - Que tipo de contratação é (EAP Padrão)
    - Qual o tipo de serviço
    - Qual a unidade demandante
    - Qual o valor estimado
    - Se é urgente ou não
    - Qual a complexidade

  O que ele NÃO SABE (e portanto NÃO pode ser feature):
    - Se vai ter intercorrência (acontece durante o processo)
    - Quem vai ganhar (resultado do certame)
    - O valor contratado (resultado da negociação)

  Isso se chama LEAKAGE: usar informação do futuro para prever o futuro.
  Se incluíssemos 'tem_intercorrencia' como feature, o modelo teria
  acurácia alta mas seria INÚTIL — porque quando o demandante pergunta
  o prazo, ele ainda não sabe se vai ter recurso.
""")

# Filtrar processos concluídos (têm prazo real)
df_m1 = df_eaps[df_eaps["status"] == "Concluído"].copy()
print(f"  Processos concluídos para treino: {len(df_m1)}")

# Features: o que se sabe NO MOMENTO DA ABERTURA
features_m1 = [
    "eap_padrao",               # Tipo de EAP (define o fluxo)
    "categoria_contratacao",    # Licitação / Direta / Inexigibilidade
    "tipo_servico",             # TI, Engenharia, Facilities...
    "unidade_demandante",       # Quem pediu
    "valor_estimado",           # Quanto espera gastar
    "urgencia",                 # Normal / Urgente / Emergencial
    "complexidade",             # Baixa / Média / Alta
    "num_etapas",               # Quantas etapas a EAP tem
]
target_m1 = "prazo_total_dias"

print(f"  Features: {features_m1}")
print(f"  Target:   {target_m1}")

# ---------------------------------------------------------------------------
# PASSO 2: Converter para H2OFrame e definir tipos
# ---------------------------------------------------------------------------
print_subsecao("Passo 2: Converter para H2OFrame")

colunas_m1 = features_m1 + [target_m1]
hf_m1 = h2o.H2OFrame(df_m1[colunas_m1])

# Marcar categóricas como fator
categoricas_m1 = [
    "eap_padrao", "categoria_contratacao",
    "tipo_servico", "unidade_demandante",
    "urgencia", "complexidade"
]
for col in categoricas_m1:
    hf_m1[col] = hf_m1[col].asfactor()

print(f"  H2OFrame: {hf_m1.nrow} linhas x {hf_m1.ncol} colunas")
print(f"  Tipos: {hf_m1.types}")

# ---------------------------------------------------------------------------
# PASSO 3: Dividir em treino e teste
# ---------------------------------------------------------------------------
print_subsecao("Passo 3: Dividir treino / teste")

print("""
  Por que dividir?
    Se avaliarmos o modelo nos mesmos dados que ele usou para aprender,
    a nota será artificialmente alta — como fazer prova com o gabarito.
    A divisão treino/teste simula: "o modelo nunca viu esses processos".

  80% treino (o modelo aprende aqui)
  20% teste  (avaliamos a qualidade aqui)
""")

train_m1, test_m1 = hf_m1.split_frame(ratios=[0.8], seed=42)
print(f"  Treino: {train_m1.nrow} processos")
print(f"  Teste:  {test_m1.nrow} processos")

# ---------------------------------------------------------------------------
# PASSO 4: Treinar o modelo GBM
# ---------------------------------------------------------------------------
print_subsecao("Passo 4: Treinar GBM de Regressão")

print("""
  GBM = Gradient Boosting Machine
    É um ensemble de árvores de decisão treinadas sequencialmente.
    Cada árvore corrige os erros da anterior.
    É o algoritmo mais popular em competições de ML por bom motivo:
    funciona bem com dados tabulares, lida com categóricas, e é rápido.

  Hiperparâmetros principais:
    ntrees=100        → número de árvores (mais = mais preciso, mas mais lento)
    max_depth=6       → profundidade máxima de cada árvore (controla complexidade)
    learn_rate=0.1    → taxa de aprendizado (quanto cada árvore contribui)
    sample_rate=0.8   → fração dos dados usada em cada árvore (reduz overfitting)
""")

modelo_m1 = H2OGradientBoostingEstimator(
    model_id="modelo_prazo_v1",
    ntrees=100,
    max_depth=6,
    learn_rate=0.1,
    sample_rate=0.8,
    col_sample_rate=0.8,
    seed=42,
    # distribution="gaussian" é o padrão para regressão
)

modelo_m1.train(
    x=features_m1,
    y=target_m1,
    training_frame=train_m1,
    validation_frame=test_m1,
)

# ---------------------------------------------------------------------------
# PASSO 5: Avaliar o modelo
# ---------------------------------------------------------------------------
print_subsecao("Passo 5: Avaliar qualidade do modelo")

perf_m1 = modelo_m1.model_performance(test_m1)
mae_m1 = perf_m1.mae()
rmse_m1 = perf_m1.rmse()
r2_m1 = perf_m1.r2()

print(f"""
  Métricas no conjunto de TESTE (dados que o modelo nunca viu):

    MAE  = {mae_m1:.1f} dias   (erro médio absoluto)
    RMSE = {rmse_m1:.1f} dias   (erro quadrático médio — penaliza erros grandes)
    R²   = {r2_m1:.3f}        (% da variância explicada — 1.0 = perfeito)

  Interpretação:
    O modelo erra em média {mae_m1:.0f} dias na previsão de prazo.
    Para um processo de ~100 dias, isso é um erro de ~{mae_m1/100*100:.0f}%.
""")

# Importância das features
print("  Importância das features (o que mais influencia o prazo):")
varimp = modelo_m1.varimp()
for feat, rel_imp, scaled, pct in varimp:
    print(f"    {feat:<30} {pct:>6.1f}%")

# ---------------------------------------------------------------------------
# PASSO 6: Exemplo de predição
# ---------------------------------------------------------------------------
print_subsecao("Passo 6: Exemplo de predição")

# Pegar 5 exemplos do teste e comparar
pred_m1 = modelo_m1.predict(test_m1)
df_comp_m1 = h2o.as_list(test_m1[["eap_padrao", "tipo_servico", "valor_estimado", target_m1]])
df_comp_m1["prazo_previsto"] = h2o.as_list(pred_m1)["predict"].values
df_comp_m1["erro_dias"] = (df_comp_m1["prazo_previsto"] - df_comp_m1[target_m1]).round(1)

print("  Exemplos — previsto vs real:")
print(f"  {'EAP Padrao':<35} {'Tipo Servico':<25} {'Valor R$':>12} {'Real':>6} {'Previsto':>8} {'Erro':>6}")
for _, row in df_comp_m1.head(10).iterrows():
    print(f"  {str(row['eap_padrao']):<35} {str(row['tipo_servico']):<25} "
          f"{row['valor_estimado']:>12,.0f} {row[target_m1]:>6.0f}d {row['prazo_previsto']:>7.0f}d {row['erro_dias']:>+6.0f}d")

# Exportar predições
df_export_m1 = h2o.as_list(test_m1)
df_export_m1["prazo_previsto"] = h2o.as_list(pred_m1)["predict"].values
df_export_m1.to_csv(f"{OUTPUT_DIR}/output_modelo1_prazo.csv", index=False)
print(f"\n  Exportado: {OUTPUT_DIR}/output_modelo1_prazo.csv")


# ============================================================================
#
#   MODELO 2: CLASSIFICAÇÃO DE INTERCORRÊNCIA
#   "Qual a chance de ter impugnação ou recurso?"
#
# ============================================================================

print_secao("MODELO 2: CLASSIFICACAO DE INTERCORRENCIA")

print_subsecao("Passo 1: Escolher features a partir da pergunta")

print("""
  PERGUNTA: "Qual a probabilidade de impugnação ou recurso neste processo?"

  Aqui as features são as mesmas do Modelo 1 (o que se sabe na abertura),
  mas o TARGET muda: em vez de prever um número (prazo), prevemos
  uma PROBABILIDADE (sim/não vai ter intercorrência).

  A diferença fundamental:
    Modelo 1 (Regressão):     target = número contínuo (dias)
    Modelo 2 (Classificação): target = categoria (True / False)

  O modelo retorna uma probabilidade entre 0 e 1.
  Ex: 0.73 = "73% de chance de intercorrência"
""")

# Usar TODOS os processos (não só concluídos)
# Intercorrência pode acontecer em processos em andamento também
df_m2 = df_eaps.copy()
print(f"  Processos para treino: {len(df_m2)}")

features_m2 = [
    "eap_padrao",
    "categoria_contratacao",
    "tipo_servico",
    "unidade_demandante",
    "valor_estimado",
    "urgencia",
    "complexidade",
    "num_etapas",
    "num_participantes",  # Mais participantes = mais chance de recurso
]
target_m2 = "tem_intercorrencia"

# Converter para H2O
colunas_m2 = features_m2 + [target_m2]
hf_m2 = h2o.H2OFrame(df_m2[colunas_m2])
for col in categoricas_m1:
    hf_m2[col] = hf_m2[col].asfactor()
# TARGET precisa ser fator para classificação!
hf_m2[target_m2] = hf_m2[target_m2].asfactor()

print(f"\n  Distribuição do target:")
print(f"    Sem intercorrência: {(df_m2[target_m2] == False).sum()} ({(df_m2[target_m2] == False).mean():.1%})")
print(f"    Com intercorrência: {(df_m2[target_m2] == True).sum()} ({(df_m2[target_m2] == True).mean():.1%})")

print("""
  DESBALANCEAMENTO: ~79% sem vs ~21% com intercorrência.
  Se o modelo simplesmente chutasse "não" para tudo, acertaria 79%.
  Por isso usamos AUC-ROC como métrica, não acurácia simples.
""")

# Dividir treino/teste
print_subsecao("Passo 2: Treinar GBM de Classificação")

train_m2, test_m2 = hf_m2.split_frame(ratios=[0.8], seed=42)
print(f"  Treino: {train_m2.nrow} | Teste: {test_m2.nrow}")

modelo_m2 = H2OGradientBoostingEstimator(
    model_id="modelo_intercorrencia_v1",
    ntrees=100,
    max_depth=5,
    learn_rate=0.1,
    sample_rate=0.8,
    col_sample_rate=0.8,
    seed=42,
    balance_classes=True,  # Compensa o desbalanceamento
    # distribution="bernoulli" é automático para classificação binária
)

modelo_m2.train(
    x=features_m2,
    y=target_m2,
    training_frame=train_m2,
    validation_frame=test_m2,
)

# Avaliar
print_subsecao("Passo 3: Avaliar qualidade")

perf_m2 = modelo_m2.model_performance(test_m2)
auc_m2 = perf_m2.auc()
aucpr_m2 = perf_m2.aucpr()

# Confusion matrix
cm_m2 = perf_m2.confusion_matrix()

print(f"""
  AUC-ROC = {auc_m2:.3f}
    Interpreta: probabilidade de que um processo COM intercorrência
    receba score maior que um SEM. 0.5 = chute, 1.0 = perfeito.

  AUC-PR  = {aucpr_m2:.3f}
    Mais relevante quando as classes são desbalanceadas.

  Matriz de Confusão (no conjunto de teste):
""")
print(cm_m2)

# Importância
print("\n  Importância das features:")
varimp_m2 = modelo_m2.varimp()
for feat, rel_imp, scaled, pct in varimp_m2:
    print(f"    {feat:<30} {pct:>6.1f}%")

# Exemplos
print_subsecao("Passo 4: Exemplos de predição")

pred_m2 = modelo_m2.predict(test_m2)
df_comp_m2 = h2o.as_list(test_m2[["eap_padrao", "tipo_servico", "valor_estimado", target_m2]])
pred_m2_list = h2o.as_list(pred_m2)
df_comp_m2["prob_intercorrencia"] = pred_m2_list["True"].values
df_comp_m2["previsto"] = pred_m2_list["predict"].values
df_comp_m2 = df_comp_m2.sort_values("prob_intercorrencia", ascending=False)

print("  Top 10 processos com MAIOR probabilidade de intercorrência:")
print(f"  {'EAP Padrao':<35} {'Tipo Servico':<25} {'Valor R$':>12} {'Real':>6} {'Prob':>6}")
for _, row in df_comp_m2.head(10).iterrows():
    real = "SIM" if str(row[target_m2]) == "True" else "NAO"
    print(f"  {str(row['eap_padrao']):<35} {str(row['tipo_servico']):<25} "
          f"{row['valor_estimado']:>12,.0f} {real:>6} {row['prob_intercorrencia']:>5.0%}")

# Exportar
df_export_m2 = h2o.as_list(test_m2)
df_export_m2["prob_intercorrencia"] = pred_m2_list["True"].values
df_export_m2.to_csv(f"{OUTPUT_DIR}/output_modelo2_intercorrencia.csv", index=False)
print(f"\n  Exportado: {OUTPUT_DIR}/output_modelo2_intercorrencia.csv")


# ============================================================================
#
#   MODELO 3: CLASSIFICAÇÃO DE RUPTURA CONTRATUAL
#   "Esse contrato tem risco de rescisão?"
#
# ============================================================================

print_secao("MODELO 3: CLASSIFICACAO DE RUPTURA CONTRATUAL")

print_subsecao("Passo 1: Escolher features a partir da pergunta")

print("""
  PERGUNTA: "Esse contrato tem risco de rescisão?"

  Aqui trocamos de dataset: usamos contratos.csv (pós-assinatura).
  O momento da pergunta é DEPOIS da assinatura, então temos mais
  informação disponível:
    - Quem é o fornecedor (nota, porte)
    - Qual o valor contratado real
    - Qual a vigência
    - Quantos aditivos já teve
    - Se já teve penalidades

  A NOTA DO FORNECEDOR é a feature mais importante aqui.
  No mundo real, essa nota viria do histórico do SICAF.
""")

df_m3 = df_contratos.copy()
print(f"  Contratos para treino: {len(df_m3)}")

features_m3 = [
    "eap_padrao",
    "categoria_contratacao",
    "tipo_servico",
    "valor_contratado",
    "vigencia_meses",
    "num_aditivos",
    "num_penalidades",
    "teve_atraso",
    "dias_atraso_total",
    "nota_fornecedor",
    "porte_fornecedor",
]
target_m3 = "teve_rescisao"

# Converter
colunas_m3 = features_m3 + [target_m3]
hf_m3 = h2o.H2OFrame(df_m3[colunas_m3])

categoricas_m3 = [
    "eap_padrao", "categoria_contratacao",
    "tipo_servico", "porte_fornecedor"
]
for col in categoricas_m3:
    hf_m3[col] = hf_m3[col].asfactor()
hf_m3["teve_atraso"] = hf_m3["teve_atraso"].asfactor()
hf_m3[target_m3] = hf_m3[target_m3].asfactor()

print(f"\n  Distribuição do target:")
print(f"    Sem rescisão: {(df_m3[target_m3] == False).sum()} ({(df_m3[target_m3] == False).mean():.1%})")
print(f"    Com rescisão: {(df_m3[target_m3] == True).sum()} ({(df_m3[target_m3] == True).mean():.1%})")

print("""
  DESBALANCEAMENTO FORTE: ~86% sem vs ~14% com rescisão.
  balance_classes=True ajuda o modelo a não ignorar a classe rara.
""")

# Treinar
print_subsecao("Passo 2: Treinar GBM de Classificação")

train_m3, test_m3 = hf_m3.split_frame(ratios=[0.8], seed=42)
print(f"  Treino: {train_m3.nrow} | Teste: {test_m3.nrow}")

modelo_m3 = H2OGradientBoostingEstimator(
    model_id="modelo_ruptura_v1",
    ntrees=120,
    max_depth=5,
    learn_rate=0.08,
    sample_rate=0.8,
    col_sample_rate=0.8,
    seed=42,
    balance_classes=True,
)

modelo_m3.train(
    x=features_m3,
    y=target_m3,
    training_frame=train_m3,
    validation_frame=test_m3,
)

# Avaliar
print_subsecao("Passo 3: Avaliar qualidade")

perf_m3 = modelo_m3.model_performance(test_m3)
auc_m3 = perf_m3.auc()
aucpr_m3 = perf_m3.aucpr()
cm_m3 = perf_m3.confusion_matrix()

print(f"""
  AUC-ROC = {auc_m3:.3f}
  AUC-PR  = {aucpr_m3:.3f}

  Matriz de Confusão:
""")
print(cm_m3)

# Importância
print("\n  Importância das features:")
varimp_m3 = modelo_m3.varimp()
for feat, rel_imp, scaled, pct in varimp_m3:
    print(f"    {feat:<30} {pct:>6.1f}%")

# Exemplos
print_subsecao("Passo 4: Exemplos de predição")

pred_m3 = modelo_m3.predict(test_m3)
df_comp_m3 = h2o.as_list(test_m3[["tipo_servico", "nota_fornecedor",
                                   "porte_fornecedor", "num_aditivos", target_m3]])
pred_m3_list = h2o.as_list(pred_m3)
# A coluna de probabilidade de True pode ser "True" ou "1"
prob_col = "True" if "True" in pred_m3_list.columns else "1"
df_comp_m3["prob_rescisao"] = pred_m3_list[prob_col].values
df_comp_m3 = df_comp_m3.sort_values("prob_rescisao", ascending=False)

print("  Top 10 contratos com MAIOR risco de rescisão:")
print(f"  {'Tipo Servico':<25} {'Nota':>5} {'Porte':<8} {'Adit':>4} {'Real':>5} {'Prob':>6}")
for _, row in df_comp_m3.head(10).iterrows():
    real = "SIM" if str(row[target_m3]) == "True" else "NAO"
    print(f"  {str(row['tipo_servico']):<25} {row['nota_fornecedor']:>5.1f} "
          f"{str(row['porte_fornecedor']):<8} {row['num_aditivos']:>4} "
          f"{real:>5} {row['prob_rescisao']:>5.0%}")

# Exportar com nome do fornecedor
df_export_m3 = df_m3.copy()
pred_m3_full = modelo_m3.predict(hf_m3)
pred_m3_full_list = h2o.as_list(pred_m3_full)
df_export_m3["prob_rescisao"] = pred_m3_full_list[prob_col].values
df_export_m3.to_csv(f"{OUTPUT_DIR}/output_modelo3_ruptura.csv", index=False)
print(f"\n  Exportado: {OUTPUT_DIR}/output_modelo3_ruptura.csv")

# Ranking de fornecedores por risco
print_subsecao("Passo 5: Ranking de fornecedores por risco de rescisão")

ranking = df_export_m3.groupby(["fornecedor_id", "fornecedor_nome"]).agg(
    num_contratos=("contrato_id", "count"),
    prob_media=("prob_rescisao", "mean"),
    rescisoes_reais=("teve_rescisao", "sum"),
    nota_media=("nota_fornecedor", "mean"),
).reset_index()
ranking = ranking.sort_values("prob_media", ascending=False)

print("  Top 15 fornecedores com MAIOR risco médio de rescisão:")
print(f"  {'Fornecedor':<35} {'Contratos':>9} {'Prob Media':>10} {'Rescisoes':>9} {'Nota':>5}")
for _, row in ranking.head(15).iterrows():
    print(f"  {row['fornecedor_nome']:<35} {row['num_contratos']:>9} "
          f"{row['prob_media']:>9.0%} {int(row['rescisoes_reais']):>9} "
          f"{row['nota_media']:>5.1f}")


# ============================================================================
# RESUMO FINAL
# ============================================================================

print_secao("RESUMO DOS 3 MODELOS")

print(f"""
  Modelo 1 — Prazo Previsto (Regressão GBM)
    MAE:  {mae_m1:.1f} dias de erro médio
    R²:   {r2_m1:.3f}
    Uso:  "Seu processo deve levar entre X e Y dias"

  Modelo 2 — Probabilidade de Intercorrência (Classificação GBM)
    AUC:  {auc_m2:.3f}
    Uso:  "Este processo tem Z% de chance de impugnação/recurso"

  Modelo 3 — Risco de Ruptura Contratual (Classificação GBM)
    AUC:  {auc_m3:.3f}
    Uso:  "Este contrato com fornecedor X tem Z% de risco de rescisão"

  Arquivos exportados para o Time 2 (Agente IA):
    {OUTPUT_DIR}/output_modelo1_prazo.csv
    {OUTPUT_DIR}/output_modelo2_intercorrencia.csv
    {OUTPUT_DIR}/output_modelo3_ruptura.csv
""")

# Encerrar
h2o.cluster().shutdown(prompt=False)
print("H2O encerrado.")
