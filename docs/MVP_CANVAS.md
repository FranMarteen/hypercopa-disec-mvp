# MVP Canvas — HyperCopa DISEC 2026

**Equipe:** Equipe HyperCopa DISEC 2026 (Capitão · Bento · João)
**Solução:** Agente Preparador BB + Modelo Analítico (H2O AutoML)
**Data de entrega:** 07/05/2026

---

## 1. Personas segmentadas

> *Para que área foi destinado esse MVP?*

**Categoria do desafio:** Inteligência Acionável para Compras e Fornecedores.

**Personas atendidas (DISEC – CESUP-Contratações):**

- **Demandantes de áreas-cliente** (DICOI, DISUP, DITEC, GECOI) — gestores que recebem pergunta de negócio (ex: *"quais EAPs vão atrasar?"*) e hoje dependem de fila de DBA + Cientista de Dados.
- **Líderes de contratação da DISEC** — quem prioriza carteira de licitações sob a Lei 14.133/21.
- **Cientistas de dados internos** — deixam de fazer ETL repetitivo e se concentram em modelos de maior valor.

---

## 2. Proposta do MVP

> *Descreva o problema de negócio. Que ações foram simplificadas ou melhoradas?*

**Problema de negócio.** O ciclo entre uma pergunta de negócio (*"qual a chance de ruptura desta carteira?"*) e uma resposta acionável dura **3 a 10 dias**, passando por DBA → Cientista de Dados → Validação. Decisões são adiadas, contratos rompem antes da análise ficar pronta.

**O que foi simplificado/melhorado.**

| Antes | Com o MVP |
|---|---|
| 3-10 dias do extrato bruto ao modelo | **3-5 minutos** |
| 50-300 linhas de código escritas pelo usuário | **zero linhas** |
| 3-4 pessoas no ciclo | **1** |
| CSV inteiro entregue ao analista | Só **schema + 20 linhas amostra** trafegam para o LLM (Caminho A) ou ficam dentro do tenant BB (Caminho B) |

**Como funciona.** O usuário sobe o CSV no app BB; um **Agente IA** (OpenAI ou Microsoft Copilot do Teams) entende a pergunta, propõe target/features e gera o CSV final via sandbox `pandas`. O **H2O AutoML** treina 3 modelos preditivos em até 5 min. O **Copilot do Teams** (RPA conversacional) traduz o relatório técnico em recomendações de negócio.

---

## 3. Jornadas

> *Quais jornadas são atendidas/melhoradas? Quais indicadores estratégicos do **Planejamento Estratégico DISEC 2026: Integração para a Ação** estão contemplados?*

**Jornadas DISEC atendidas:**

1. **Priorização de carteira de EAPs** — prever risco de atraso em contratações em andamento.
2. **Gestão de fornecedores** — antecipar intercorrências (impugnação, recurso) antes da homologação.
3. **Mitigação de ruptura contratual** — identificar contratos com alta probabilidade de rescisão.
4. **Atendimento a demanda recorrente das áreas-cliente** — perguntas analíticas sem fila de cientista de dados.

**Indicadores estratégicos contemplados (Planejamento DISEC 2026 — *Integração para a Ação*):**

- **Tempo de resposta a demandas analíticas** (redução de 3-10 dias → 3-5 min).
- **Aderência à governança de dados BB** (Caminho B mantém CSV completo no laptop; só amostra trafega no tenant M365 BB sob Microsoft Purview).
- **Capilaridade analítica** — qualquer demandante usa, sem precisar saber Python.
- **Conformidade Lei 14.133/21** — terminologia oficial (Licitação Eletrônica, EAPs Padrão) embutida no system_prompt versionado.

---

## 4. Tecnologias envolvidas

> *Quais tecnologias foram utilizadas? Justifique a escolha.*

| Categoria | Tecnologia | Justificativa |
|---|---|---|
| **Modelo analítico** | **H2O AutoML 3.46** (GBM, GLM, XGBoost, RF, DRF) | Roda em JVM local — dados nunca saem do laptop. AutoML elimina escolha manual de algoritmo. Leaderboard auditável. Open-source, sem custo de licença. |
| **Agente de IA — Caminho A** | OpenAI `gpt-4o-mini` com **Tool Use** (4 tools: `ler_schema`, `ler_amostra`, `executar_pandas`, `salvar_csv_final`) | Pattern maduro e auditável. Apenas schema + ≤20 linhas saem para o LLM. Sandbox `exec()` com globals restritos. Custo ~R$ 0,30/conversa. Apropriado para demo e desenvolvimento. |
| **Agente de IA — Caminho B (produção BB)** | **Microsoft Copilot do Teams** via Copilot Studio (declarativo, sem código) | Trafega pelo tenant M365 BB sob acordo Microsoft↔BB. Sem chave individual. Auditoria automática Microsoft Purview. **R$ 0** marginal (incluso na licença Copilot já paga). |
| **RPA / Automação** | Copilot do Teams (interpretação executiva do JSON do relatório) + sandbox local de execução `pandas` (substitui scripts ad-hoc do cientista de dados) | Reaproveita licença M365. RPA conversacional > RPA programado: o usuário descreve o resultado, o agente formata. |
| **Frontend / UX** | Streamlit single-page com **identidade visual BB** (paleta `#FAE128` / `#003DA5`, IBM Plex Sans como proxy de BB Texto) | Uma URL, jornada linear, sidebar = estado / centro = ação. Pensado para demandante recorrente, não para data scientist. |
| **Relatório** | HTML autocontido + JSON estruturado | HTML abre em qualquer browser sem dependências; JSON serve de auditoria e entrada do Copilot interpretativo. |
| **Dados** | Sintéticos (`Faker` + regras de negócio Lei 14.133/21) | Acesso a dados reais inviável no prazo. Engloba ciclo pós-contrato (aditivos, rescisão, atrasos). |

---

## 5. Resultados Obtidos

> *Que aprendizados ou resultados foram obtidos?*

**Resultados técnicos do MVP (07/05/2026).**

- **3 modelos preditivos H2O treinados e validados** com dados sintéticos:
  - Modelo 1 — Prazo de contratação (regressão GBM): RMSE ~18 dias / R² ~0,82.
  - Modelo 2 — Intercorrência (classificação binária GBM): AUC ~0,84.
  - Modelo 3 — Ruptura contratual (classificação binária GBM): AUC ~0,79.
- **App entregável funcional** (`app_agente_bb.py`) com identidade visual BB e jornada de 3 etapas (Agente → H2O AutoML → Interpretação).
- **Dois caminhos validados:** OpenAI direto (Caminho A) e Microsoft Copilot Teams (Caminho B). Caminho B é o de produção BB.
- **Repositório privado no GitHub** com `.gitignore` protegendo `.env` e `dados reais/`.

**Aprendizados.**

1. **Velocidade analítica e governança não são trade-offs.** Separando *o que sai para o LLM* (apenas metadados e amostra) de *onde o modelo é treinado* (JVM H2O local), conseguimos a velocidade do LLM sem violar política BB de classificação de dados.
2. **AutoML > escolher algoritmo manualmente** para o caso de uso DISEC. GBM venceu na maioria dos targets, mas nem sempre — a leaderboard expõe a escolha.
3. **Caminho B (Copilot Teams) é o de produção.** Elimina chave individual, custo OpenAI e dependência de LLM público. Trafega no tenant M365 sob Purview.
4. **Sandbox restrito é não-negociável.** Código gerado por LLM precisa de globals limitados, sem `os`, sem `subprocess`, sem rede.

---

## 6. Métricas para validação

> *Indicadores afetados (tempo, custo, qualidade, risco). De que maneira evidenciamos êxito? Quais ganhos na data da entrega?*

| Indicador | Antes | Com o MVP | Como evidenciamos |
|---|---:|---:|---|
| **Tempo CSV bruto → modelo treinado** | 3-10 dias | **3-5 min** | Demo cronometrada no vídeo (segundos visíveis no spinner H2O). |
| **Linhas de código escritas pelo demandante** | 50-300 | **0** | UX: usuário só sobe CSV e conversa. |
| **Pessoas envolvidas no ciclo** | 3-4 | **1** | Jornada única no app. |
| **Vazamento de CSV para LLM** | risco alto | **0% (Caminho A: só amostra; Caminho B: nem amostra completa sai)** | Print da chamada OpenAI — só schema + 20 linhas. |
| **Custo marginal por conversa** | — | **R$ 0** (Caminho B) / R$ 0,30 (Caminho A) | Caminho B usa licença Copilot já paga. |
| **AUC dos modelos de risco (intercorrência / ruptura)** | n/d (não havia modelo) | **0,84 / 0,79** | Relatório HTML gerado pelo H2O com leaderboard e métricas no teste. |
| **Auditabilidade** | scripts ad-hoc | **system_prompt versionado em git + leaderboard H2O + logs Streamlit** | Repo `hypercopa-disec-2026` no GitHub. |

**Ganhos obtidos na data da entrega (07/05/2026):**

- App funcional e entregável (Caminhos A e B).
- 3 modelos validados com performance acima do baseline (AUC > 0,75).
- Documentação completa: fluxograma, acesso, relatório, guia Copilot Studio.
- Vídeo de demonstração da jornada ponta-a-ponta.

---

## 7. Escalabilidade

> *Outras áreas que podem ser beneficiadas. Previsão de ganhos (horas, financeiro).*

**Outras áreas BB que podem ser beneficiadas (mesmo padrão de jornada).**

| Área | Pergunta de negócio análoga | Reaproveitamento |
|---|---|---|
| **DIRAO / DIROP** | Risco de inadimplência por carteira | Mesma jornada, target diferente. |
| **DICOI / DITEC / DISUP / GECOI** | Atraso em projetos de TI / obras | Já contemplada; reaproveitar templates de prompt. |
| **DICAR / DIPES** | Turnover por agência / função | Trocar dataset; arquitetura idêntica. |
| **CRGOV / DIRIS** | Risco regulatório por contrato | Adicionar tools de leitura de cláusulas (RAG). |

**Previsão de ganhos (cenário DISEC anualizado, hipóteses conservadoras anotadas).**

| Item | Hipótese | Valor anual |
|---|---|---:|
| Demandas evitadas a cientista de dados | 60 demandas/ano × 6h economizadas | **360 horas** |
| Economia em homem-hora carregada | 360h × R$ 150/h | **R$ 54.000** |
| Contratos com ruptura evitada | 0,5 % de 4.000 contratos × R$ 200 mil | **R$ 4.000.000** |
| Custo marginal Caminho A (OpenAI) | 1.000 conversas × R$ 0,30 | R$ 300 |
| Custo marginal Caminho B (Copilot Teams) | já incluso na licença M365 BB | **R$ 0** |
| **Saldo estimado primeiro ano (DISEC)** | — | **~ R$ 4 milhões** |

**Caminho de escala.**

1. **Curto prazo (até Pitch Day 10/06/2026):** publicar agente Copilot no Teams via Copilot Studio (Caminho B oficial); rodar pilotos com extratos sintéticos das 4 áreas DISEC.
2. **Médio prazo:** RAG com EAPs Padrão e jurisprudência da Lei 14.133/21; persistência das conversas em banco BB para auditoria; substituir IBM Plex Sans pelas fontes oficiais BB (BB Texto / BB Títulos).
3. **Longo prazo:** out-of-time validation trimestral; detecção de drift; agente proativo (alerta a área quando uma EAP cruza limiar de risco); API REST (já há `api/main.py` em FastAPI) para consumo por sistemas internos BB.

---

## Anexos / artefatos da entrega

| Artefato | Caminho no repositório |
|---|---|
| App principal Streamlit (Caminhos A e B) | `app_agente_bb.py` |
| Fluxograma da jornada (2 caminhos, Mermaid) | `docs/FLUXOGRAMA.md` |
| Doc de acesso e instalação | `docs/ACESSO.md` |
| Relatório técnico estendido | `docs/RELATORIO_SOLUCAO.md` / `.docx` |
| Guia Copilot Studio passo-a-passo | `docs/COPILOT_STUDIO_GUIA.md` |
| System prompt OpenAI (Caminho A) | `docs/agente/system_prompt.md` |
| Schema das 4 tools (Caminho A) | `docs/agente/tools_schema.json` |
| Manifest Copilot declarativo (Caminho B) | `teams_copilot/declarative-agent.json` |
| Instructions Copilot Studio (Caminho B) | `teams_copilot/instructions.md` |
| Notebook H2O do agente | `notebook_h2o_agente_mvp.ipynb` |
| Repo privado | https://github.com/FranMarteen/hypercopa-disec-mvp |

---

*MVP Canvas elaborado para a banca avaliadora · HyperCopa DISEC 2026 · Banco do Brasil · 07/05/2026*
