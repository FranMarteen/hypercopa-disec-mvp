# Entrega MVP — Time 1 (Modelos Analíticos)

**HyperCopa DISEC 2026** · CESUP-Contratações · Banco do Brasil
**Produto:** **Predfy** — camada de Modelo Analítico (Etapas 2-3 da jornada)
**Data de entrega:** 07/05/2026

---

## 1. Identificação

| Item | Conteúdo |
|---|---|
| Time | Time 1 — **Inteligência Analítica para Compras e Fornecedores** |
| Camada no Predfy | Etapas 0, 2 e 3 da jornada (Dados sintéticos + Treino H2O AutoML + Avaliação) |
| Tema HyperCopa | Inteligência Acionável para Compras e Fornecedores |
| Equipe | **Time 1 — ECOA / CESUP-Contratações:** João 23 (capitão) · Francisco · Rosali · Silvia |
| Cooperação | Time 2 (Agente Predfy + Intérprete) — schema único de saída JSON dos modelos |
| Repositório | https://github.com/FranMarteen/hypercopa-disec-mvp (público) |

---

## 2. Resumo executivo

A camada analítica do **Predfy** entrega **3 modelos H2O AutoML treinados, validados e empacotados** sobre dados sintéticos de Licitação Eletrônica (Lei 13.303/16), com schema JSON padronizado consumível pelo Time 2. O escopo de **6 modelos** da proposta original foi **rebalanceado para 3 modelos prioritários** após o Estudo de Campo, com 4 protótipos analíticos auxiliares (recorrência, anomalias, HHI, lock-in) preservados como evidência técnica e backlog de evolução.

A entrega é **reprodutível ponta-a-ponta**: `seed=42` em geradores, splits e AutoML; `h2o==3.46.0.6` pinado em `requirements_app.txt`; dados sintéticos commitados no repo. **A banca clona, instala e vê os mesmos números que a equipe.**

---

## 3. Comparativo — Proposto vs Realizado

### 3.1 Modelos analíticos

| # | Modelo proposto (Mar/2026) | Status | O que foi entregue | Justificativa |
|---|---|---|---|---|
| 1 | Recorrência (K-Means + TF-IDF) | 🟡 protótipo | `analise_clusters.py` + `dados_sinteticos/output_recorrencia.csv` + `analise_clusters_detalhada.png` | Substituído como modelo MVP por **Modelo de Prazo (regressão GBM)**, mais acionável para a DISEC. Código preservado como prova de conceito. |
| 2 | Detecção de anomalias (Isolation Forest) | 🟡 protótipo | `dados_sinteticos/output_anomalias.csv` + integração com semáforo de risco no relatório H2O | Substituído como MVP por **Modelo de Intercorrência (classificação binária GBM)** — anomalia genérica virou sinal de risco específico (impugnação/recurso). |
| 3 | Predição de demanda (GBM/XGBoost séries) | 🟡 redirecionado | Pivotado para **Modelo de Prazo** (regressão GBM): `dados_sinteticos/output_modelo1_prazo.csv` + `models/prazo_total_dias/` | Volume agregado por área é menos acionável que prazo por processo. Pivotagem aprovada após mentoria H2O (07-08/04). |
| 4 | Concentração HHI | 🟡 protótipo | `dados_sinteticos/output_hhi.csv` + `output_hhi_detalhado.csv` + `hhi_concentracao.png` | Mantido como evidência analítica e roadmap. Integração ao app foi adiada por priorização de modelos preditivos. |
| 5 | Lock-in / deserto licitatório | 🟡 protótipo | Análise estatística com critérios da proposta (fornecedor único 2+ ciclos, < 3 participantes, dispersão < 5%) | Saída tabular gerada; visualização e modelo GBM dedicado ficaram como roadmap. |
| 6 | Volume adequado por fornecedor | 🟡 protótipo | Indicadores de balanceamento sobre `fornecedores.csv` | Mantido como prova de conceito; integração full ao app é roadmap. |
| **+1** | **Modelo de Prazo (regressão GBM)** | ✅ **MVP entregue** | `modelos_preditivos.py` + H2O AutoML in-app + modelo salvo em `models/prazo_total_dias/` | **Novo:** RMSE ~18 dias / R² ~0,82 sobre dados sintéticos. |
| **+2** | **Modelo de Intercorrência (classif. binária)** | ✅ **MVP entregue** | `dados_sinteticos/output_modelo2_intercorrencia.csv` | **Novo:** AUC ~0,84. |
| **+3** | **Modelo de Ruptura contratual (classif. binária)** | ✅ **MVP entregue** | `dados_sinteticos/output_modelo3_ruptura.csv` | **Novo:** AUC ~0,79. |

> **Decisão estratégica (12/04/2026):** após a Mentoria H2O e revisão com a DISEC, o time concluiu que **3 modelos focados em *risco acionável* por processo** (prazo, intercorrência, ruptura) cobrem mais valor de negócio do que 6 modelos espalhados em camadas heterogêneas. Os 4 modelos remanescentes da proposta original viram **backlog priorizado para o pós-MVP**.

### 3.2 RPA de coleta de dados

| Componente proposto | Status | O que foi feito | Justificativa |
|---|---|---|---|
| RPA semanal de extração de sistemas legados | 🔴 não implementado | Substituído por upload manual de CSV no app; geradores sintéticos `gerar_dados_postgres.py` e `gerar_dados_sinteticos_eaps.py` produzem datasets equivalentes em escala (milhares de linhas) | **Acesso a dados reais BB inviável no prazo** (decisão registrada no Plano de Jogo). RPA real fica como roadmap. |
| RPA SICAF | 🔴 não implementado | Dados de fornecedores gerados sinteticamente respeitando schema | Mesmo motivo. |
| Pré-processamento e re-treino semanal | 🟡 substituído | Re-treino sob demanda no próprio app via H2O AutoML; CSV final é a interface de re-treino | Modelo "uma URL, um clique" é mais alinhado a usuários de negócio. |

### 3.3 Interface de dados (contrato Time 1 ↔ Time 2)

| Output proposto | Schema entregue | Caminho |
|---|---|---|
| Clusters de recorrência | `output_recorrencia.csv` | `dados_sinteticos/` |
| Scores de anomalia | `output_anomalias.csv` | `dados_sinteticos/` |
| Forecast de demanda | substituído por **predição de prazo por processo** (regressão) | `output_modelo1_prazo.csv` |
| Mapa de concentração HHI | `output_hhi.csv` + `output_hhi_detalhado.csv` | `dados_sinteticos/` |
| Scores de lock-in | tabular consolidado | `dados_sinteticos/` |
| Indicadores de volume | tabular consolidado | `dados_sinteticos/` |
| **Schema unificado de saída H2O** *(novo)* | `relatorio_{ts}.json` — leaderboard, métricas no teste, top-15 importância, semáforo de risco | `relatorios/` |

> O **JSON do relatório H2O** virou a **interface única consumida pelo Time 2** (Caminho B do agente). Ele padroniza qualquer modelo treinado, não importa qual target — vantagem em relação aos 6 schemas separados originalmente previstos.

---

## 4. Decisões de adaptação (registro técnico)

1. **6 → 3 modelos focados.** Critério: pergunta de negócio acionável > variedade de algoritmos. Mantemos a evidência técnica dos outros 4 como protótipos.
2. **Dados reais → dados sintéticos.** Risco "Dados não disponíveis no prazo" da proposta (Tabela 10) materializou-se. Mitigação aplicada: geradores sintéticos com regras Lei 13.303/16 e ciclo pós-contrato (aditivos, rescisão, atrasos).
3. **RPA de coleta → upload manual + sandbox `pandas`.** Fora de escopo do MVP; substituído por jornada "usuário sobe CSV no app". RPA real entra no roadmap.
4. **Schema por modelo → schema único do relatório H2O.** Reduz custo de integração com Time 2 e padroniza qualquer target futuro.
5. **Re-treino semanal → re-treino sob demanda.** Mais alinhado ao perfil do usuário-demandante (não há frequência fixa de pergunta).

---

## 5. Métricas de performance — Proposto vs Obtido

| Métrica (proposta) | Critério | Modelo | Obtido | Status |
|---|---:|---|---:|---|
| Silhouette Score | > 0,5 | Recorrência (K-Means) | gerado em `analise_clusters.py` | 🟡 protótipo |
| AUC-ROC anomalias | > 0,75 | Isolation Forest | n/a (substituído por GBM intercorrência) | 🟡 redirecionado |
| MAPE predição | < 20 % | GBM/XGBoost | n/a (pivotado para regressão de prazo) | 🟡 redirecionado |
| Cobertura categorias HHI | 100 % | Concentração | 100 % das categorias sintéticas | ✅ |
| Acurácia lock-in | > 70 % | GBM | analítico tabular gerado | 🟡 protótipo |
| Ciclo de atualização | Semanal | RPA pipeline | re-treino sob demanda no app | 🟡 substituído |
| **AUC Intercorrência** *(novo)* | > 0,75 (referência) | GBM | **~0,84** | ✅ |
| **AUC Ruptura** *(novo)* | > 0,75 (referência) | GBM | **~0,79** | ✅ |
| **R² Prazo** *(novo)* | > 0,70 (referência) | GBM | **~0,82** | ✅ |
| **RMSE Prazo** *(novo)* | < 30 dias (referência) | GBM | **~18 dias** | ✅ |

---

## 6. Riscos e mitigações — Status

| Risco da proposta | Probabilidade prevista | O que aconteceu |
|---|---|---|
| Dados não disponíveis no prazo | Média | **Materializou-se.** Mitigação ativada: geradores sintéticos. |
| Performance dos modelos baixa | Baixa | Não materializou. AUC > 0,75 nos modelos MVP. |
| Schema de interface desalinhado | Média | Não materializou. Schema único H2O simplificou a integração. |
| Prazo apertado para 6 modelos | Alta | **Materializou-se.** Mitigação ativada: priorização para 3 modelos MVP + 4 protótipos. |

---

## 7. Artefatos entregues — Time 1

| Categoria | Artefato | Caminho |
|---|---|---|
| Modelo MVP 1 (Prazo) | Script de treino | `modelos_preditivos.py` |
| Modelo MVP 1 (Prazo) | Modelo H2O salvo | `models/prazo_total_dias/` |
| Modelo MVP 1 (Prazo) | Output CSV | `dados_sinteticos/output_modelo1_prazo.csv` |
| Modelo MVP 2 (Intercorrência) | Output CSV | `dados_sinteticos/output_modelo2_intercorrencia.csv` |
| Modelo MVP 3 (Ruptura) | Output CSV | `dados_sinteticos/output_modelo3_ruptura.csv` |
| Protótipo Recorrência | Script + visualização | `analise_clusters.py` · `dados_sinteticos/analise_clusters_detalhada.png` |
| Protótipo HHI | Outputs + heatmap | `dados_sinteticos/output_hhi*.csv` · `dados_sinteticos/hhi_concentracao.png` |
| Protótipos Anomalia / Lock-in / Volume | Outputs CSV | `dados_sinteticos/output_anomalias.csv` + tabulares de lock-in/volume |
| Geração de dados sintéticos | Scripts | `gerar_dados_sinteticos_eaps.py` · `gerar_dados_postgres.py` |
| Schema relacional sintético | DDL + 17 CSVs | `dados_postgres/schema.sql` + tabelas |
| Notebook H2O integrado | Documento técnico-pedagógico | `notebook_h2o_agente_mvp.ipynb` |
| Schema de saída unificado | JSON do relatório H2O | `relatorios/relatorio_*.json` |
| Repositório privado | GitHub | https://github.com/FranMarteen/hypercopa-disec-mvp |

---

## 8. Próximos passos (pós-MVP até Pitch Day 10/06/2026)

1. **Promover 3 dos 4 protótipos a modelos completos** (anomalia, HHI, lock-in) com avaliação H2O AutoML padronizada e integração ao app.
2. **Implementar RPA de coleta** quando a DISEC liberar acesso a dados reais (substituir geradores sintéticos sem alterar o schema).
3. **Out-of-time validation trimestral** dos 3 modelos MVP (split temporal).
4. **Detecção de drift** nas variáveis top-15 do leaderboard.
5. **API REST** já estruturada em `api/main.py` (FastAPI) para servir os modelos a sistemas internos BB.

---

*Entrega Time 1 — HyperCopa DISEC 2026 · 07/05/2026*
