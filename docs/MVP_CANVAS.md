# MVP Canvas — HyperCopa DISEC 2026

**Solução:** **Predfy** — Agente Predfy (preparação) + Modelo Analítico H2O AutoML (treino) + Intérprete Predfy (interpretação)

**Atribuição:** desenvolvido **em conjunto pelos Times 1 e 2 da ECOA do CESUP-Contratações** (Banco do Brasil) durante a HyperCopa DISEC 2026.

**Equipes:**

| Time | Foco | Integrantes |
|---|---|---|
| **Time 1** — Modelos Analíticos | Camadas 0, 2 e 3 (Dados sintéticos · Treino H2O · Avaliação) | João 23 (capitão) · Francisco · Rosali · Silvia |
| **Time 2** — Agente IA + RPA | Camadas 1, 4, 5 e 6 (Agente Predfy · Pacote · Intérprete · Evento real) | Bento 14 (capitão) · Felipe · Amélia · Vânia · Rafael |

**Repositório público:** https://github.com/FranMarteen/hypercopa-disec-mvp
**Data de entrega do MVP:** 07/05/2026

**Visão de produção (objetivo final).** O **Predfy** foi concebido para ser **incorporado ao fluxo de trabalho e à plataforma do BB**, atuando preventivamente sobre dados de Licitação Eletrônica para **indicar riscos e prazos reais por carteira / processo / contrato**, **facilitando a tomada de decisão e a gestão de riscos** das áreas demandantes. Adicionalmente, **acoplado ao Agente Predfy**, o app **se generaliza para qualquer extrato / domínio**: o agente conduz a feature engineering, a escolha do target e o reuso dos modelos a partir das definições de negócio do usuário — sem código.

**Modo demonstração para a banca.** O app oferece um **Caminho C — Modo demonstração offline** que dispensa qualquer API externa de LLM (OpenAI ou similar): o agente roda com turnos pré-gravados executando as ferramentas reais sobre o CSV pré-curado, **inteiramente local**. Para a avaliação, a equipe encaminhará à banca uma **chave brinde de OpenAI** (canal seguro, fora do repo) para também demonstrar o **Caminho A com LLM real**, mas o **Caminho C é suficiente para validar toda a jornada**.

> **Para aproveitamento completo em produção:** o app precisa ser hospedado em ambiente do banco com integração ao Microsoft Copilot Studio (Caminho B) — o agente declarativo já está versionado em `teams_copilot/declarative-agent.json` e o passo-a-passo de publicação está em `docs/COPILOT_STUDIO_GUIA.md`. **O Agente Predfy é exatamente a forma de minimizar a fricção** de ter que escrever código toda vez que uma área demandante traz uma pergunta nova.

---

## 1. Personas segmentadas

> *Para que área foi destinado esse MVP?*

**Categoria do desafio:** Inteligência Acionável para Compras e Fornecedores.

**Personas atendidas (DISEC – CESUP-Contratações):**

- **Demandantes de áreas-cliente** (DICOI, DISEC, DITEC, GECOI) — gestores que recebem pergunta de negócio (ex: *"quais EAPs vão atrasar?"*) e hoje dependem de fila de DBA + Cientista de Dados.
- **Líderes de contratação da DISEC** — quem prioriza carteira de Licitação Eletrônica sob a Lei 13.303/16.
- **Cientistas de dados internos** — deixam de fazer ETL repetitivo e se concentram em modelos de maior valor.

---

## 2. Proposta do MVP

> *Descreva o problema de negócio. Que ações foram simplificadas ou melhoradas?*

**Problema de negócio.** O ciclo entre uma pergunta de negócio (*"qual a chance de ruptura desta carteira?"*) e uma resposta acionável dura **3 a 10 dias**, passando por DBA → Cientista de Dados → Validação. Decisões são adiadas, contratos rompem antes da análise ficar pronta.

**O que foi simplificado/melhorado.**

| Antes | Com o Predfy |
|---|---|
| 3-10 dias do extrato bruto ao modelo | **3-5 minutos** |
| 50-300 linhas de código escritas pelo usuário | **zero linhas** |
| 3-4 pessoas no ciclo | **1** |
| CSV inteiro entregue ao analista | Só **schema + 20 linhas amostra** trafegam para o LLM (Caminho A) ou ficam dentro do tenant BB (Caminho B) |

**Como funciona — jornada de 7 etapas.**

```
0. Construção dos dados sintéticos (seed=42, reprodutível)
1. Agente Predfy   ── feature engineering visível, target, pergunta preditiva
2. Treino H2O AutoML  ── GBM, GLM, XGBoost, RF; entrega o líder
3. Avaliar  ── leaderboard, métricas no teste, importância
4. Documentos  ── pacote ZIP único da entrega (HTML + JSON + summary)
5. Intérprete Predfy  ── traduz métricas em recomendações de negócio
6. Caso de evento real  ── EAP nova hipotética, predição com semáforo
```

**3 caminhos de uso** (selecionáveis na sidebar):

| Caminho | Quem fala com o agente | Quando usar |
|---|---|---|
| **A** | OpenAI direto (chat embutido no app) | Dev local com chave própria |
| **B** | Microsoft Copilot do Teams (paste do bloco) | Produção BB (acordo M365) |
| **C** | **Modo demonstração offline** | **Avaliação da banca — sem chave OpenAI, sem rede** |

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
- **Conformidade Lei 13.303/16** — terminologia oficial (Licitação Eletrônica, EAPs Padrão, EAPs, Etapas, Contratos, Unidades Demandante/Executante) embutida no `system_prompt` versionado.
- **Reprodutibilidade**: banca, equipe e auditoria interna obtêm os mesmos números (seed=42 em todos os pontos de aleatoriedade).

---

## 4. Tecnologias envolvidas

> *Quais tecnologias foram utilizadas? Justifique a escolha.*

| Categoria | Tecnologia | Justificativa |
|---|---|---|
| **Modelo analítico** | **H2O AutoML 3.46.0.6** (GBM, GLM, XGBoost, RF, DRF) | Roda em JVM local — dados nunca saem do laptop. AutoML elimina escolha manual de algoritmo. Leaderboard auditável. Open-source. **Versão pinada** para reprodutibilidade. |
| **Agente Predfy — Caminho A** | OpenAI `gpt-4o-mini` com **Tool Use** (4 tools: `ler_schema`, `ler_amostra`, `executar_pandas`, `salvar_csv_final`) | Pattern maduro e auditável. Apenas schema + ≤20 linhas saem para o LLM. Sandbox `exec()` com globals restritos. Custo ~R$ 0,30/conversa. Apropriado para dev local. |
| **Agente Predfy — Caminho B (produção BB)** | **Microsoft Copilot do Teams** via Copilot Studio (declarativo, sem código) | Trafega pelo tenant M365 BB sob acordo Microsoft↔BB. Sem chave individual. Auditoria automática Microsoft Purview. **R$ 0** marginal (incluso na licença Copilot já paga). |
| **Agente Predfy — Caminho C (banca)** | **Player de turnos pré-gravados** + execução real das ferramentas via sandbox | **Zero rede externa**. Reproduz o comportamento dos Caminhos A/B com respostas determinísticas para a banca testar sem chave nem aprovação Copilot. |
| **Intérprete Predfy (Etapa 5)** | Simulador rule-based local (`app/interprete_rules.py`) + OpenAI ou Copilot Teams (opcional) | Lê o JSON do relatório e gera resumo executivo + tradução de métricas + recomendações em PT-BR. Sem rede. UI estilo Teams. |
| **Frontend / UX** | Streamlit single-page com **identidade visual BB** (paleta `#FAE128` / `#003DA5`, IBM Plex Sans) + **stepper visual de 7 etapas** | Jornada linear, sidebar = estado / centro = ação. Pensado para demandante recorrente, não para data scientist. |
| **Relatório** | HTML autocontido + JSON estruturado + **pacote ZIP unificado** (HTML + JSON + `summary.md` + `como_reproduzir.txt` + `MVP_CANVAS`) | Banca anexa um único ZIP à entrega. Cada artefato auditável separadamente. |
| **Dados** | **Sintéticos** (`Faker` desnecessário — geração própria com regras Lei 13.303/16, seed=42) | Acesso a dados reais inviável no prazo. Inclui ciclo pós-contrato (aditivos, rescisão, atrasos, penalidades). 6 datasets relacionais (EAPs, contratos, etapas, participantes, fornecedores, EAPs Padrão). |

---

## 5. Resultados Obtidos

> *Que aprendizados ou resultados foram obtidos?*

**Resultados técnicos do MVP (07/05/2026).**

- **3 modelos preditivos H2O treinados e validados** com dados sintéticos:
  - Modelo 1 — Prazo de contratação (regressão GBM): RMSE ~18 dias / R² ~0,82.
  - Modelo 2 — Intercorrência (classificação binária GBM): AUC ~0,84.
  - Modelo 3 — Ruptura contratual (classificação binária GBM): AUC ~0,79.
- **App entregável funcional** (`app_agente_bb.py`) com identidade visual BB, jornada de 7 etapas, **stepper visual** e **modo demonstração offline**.
- **3 caminhos validados:** OpenAI direto (A), Microsoft Copilot Teams (B), Modo demonstração offline (C — para banca).
- **Repositório público no GitHub** (`hypercopa-disec-mvp`) clonável e testável pela banca em ≤ 5 minutos.
- **Reprodutibilidade total**: `seed=42` em geradores, splits e AutoML. Banca obtém os mesmos números que a equipe.
- **Anonimização e segurança auditadas**: nenhum dado real BB, sem nomes pessoais sensíveis, sem chaves no repo.

**Aprendizados.**

1. **Velocidade analítica e governança não são trade-offs.** Separar *o que sai para o LLM* (apenas metadados e amostra) de *onde o modelo é treinado* (JVM H2O local) entrega velocidade do LLM sem violar política BB de classificação de dados.
2. **AutoML > escolher algoritmo manualmente.** GBM venceu na maioria dos targets, mas a leaderboard expõe a escolha quando não venceu.
3. **Caminho B (Copilot Teams) é o de produção.** Caminho C (modo demo) é o de avaliação. Caminho A é o de dev.
4. **Sandbox restrito é não-negociável.** Código gerado por LLM precisa de globals limitados, sem `os`, sem `subprocess`, sem rede.
5. **Reprodutibilidade vale mais que vídeo.** Em vez de gravar uma demo, **publicamos o repo com modo demo offline** — a banca testa do mesmo jeito que rodamos.

---

## 6. Métricas para validação

> *Indicadores afetados (tempo, custo, qualidade, risco). De que maneira evidenciamos êxito? Quais ganhos na data da entrega?*

| Indicador | Antes | Com o Predfy | Como evidenciamos |
|---|---:|---:|---|
| **Tempo CSV bruto → modelo treinado** | 3-10 dias | **3-5 min** | Banca mede no próprio app: stepper marca tempo entre Etapa 0 e Etapa 4. |
| **Linhas de código escritas pelo demandante** | 50-300 | **0** | UX: usuário só sobe CSV e conversa. |
| **Pessoas envolvidas no ciclo** | 3-4 | **1** | Jornada única no app. |
| **Vazamento de CSV para LLM** | risco alto | **0%** (Caminho A: só amostra; Caminho B/C: nem amostra trafega externamente) | Apenas schema + 20 linhas saem para OpenAI; em modo demo, zero rede. |
| **Custo marginal por conversa** | — | **R$ 0** (Caminho B/C) / R$ 0,30 (Caminho A) | Caminho B usa licença Copilot já paga; Caminho C é totalmente local. |
| **AUC dos modelos de risco (intercorrência / ruptura)** | n/d | **0,84 / 0,79** | Relatório HTML gerado pelo H2O com leaderboard e métricas no teste. |
| **R² do modelo de prazo (regressão)** | n/d | **~0,82** | Idem. |
| **Reprodutibilidade banca → equipe** | — | **100%** (mesmos números) | seed=42 em todos os pontos de aleatoriedade; deps pinadas (h2o==3.46.0.6). |
| **Auditabilidade** | scripts ad-hoc | **`system_prompt` versionado em git + leaderboard H2O + logs Streamlit + script de turnos do modo demo versionado** | Repo público. |

**Ganhos obtidos na data da entrega (07/05/2026):**

- App Predfy funcional com 3 caminhos (A/B/C).
- 3 modelos validados com performance acima do baseline (AUC > 0,75).
- Documentação completa: README, COMO_AVALIAR, FLUXOGRAMA, COPILOT_STUDIO_GUIA, RELATORIO_SOLUCAO.
- **Repo clonável publicamente pela banca** com modo demonstração offline.
- Pacote ZIP unificado da entrega (gerado dinamicamente pelo app).

---

## 7. Escalabilidade

> *Outras áreas que podem ser beneficiadas. Previsão de ganhos (horas, financeiro).*

**Outras áreas BB que podem ser beneficiadas (mesmo padrão de jornada).**

| Área | Pergunta de negócio análoga | Reaproveitamento |
|---|---|---|
| **DIRAO / DIROP** | Risco de inadimplência por carteira | Mesma jornada, target diferente. |
| **DICOI / DITEC / DISEC / GECOI** | Atraso em projetos de TI / obras | Já contemplada; reaproveitar templates de prompt. |
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
2. **Médio prazo:** RAG com EAPs Padrão e jurisprudência da Lei 13.303/16; persistência das conversas em banco BB para auditoria; substituir IBM Plex Sans pelas fontes oficiais BB.
3. **Longo prazo:** out-of-time validation trimestral; detecção de drift; agente proativo (alerta a área quando uma EAP cruza limiar de risco); API REST (já em `api/main.py` em FastAPI) para consumo por sistemas internos BB.

---

## 8. Contexto legal · Lei 13.303/16 e termos oficiais

> *Por que esta seção?* A banca pode estranhar a ausência da Lei 14.133/21. A escolha é proposital — o BB é estatal, e operações próprias do banco são regidas por outra lei.

### Por que Lei 13.303/16 (Lei das Estatais), não Lei 14.133/21?

| Regime | Quem aplica | Aplica ao BB? |
|---|---|---|
| **Lei 13.303/16** ("Lei das Estatais") | Empresas públicas e sociedades de economia mista (Banco do Brasil, Caixa, Petrobras, etc.) | **Sim** — para suas contratações próprias. |
| Lei 14.133/21 ("Nova Lei de Licitações") | Administração pública direta, autarquias, fundações da União, Estados, DF e Municípios | **Não** se aplica ao BB para suas contratações próprias. |

Toda terminologia do app, do `system_prompt` do agente e dos modelos foi calibrada para a **Lei 13.303/16**. Os geradores sintéticos refletem o ciclo de **Licitação Eletrônica** (modalidade preferencial das estatais), com **EAPs**, **EAPs Padrão**, **Etapas**, **Contratos** e ciclo pós-contratação (aditivos, intercorrências, rescisão).

### Termos oficiais usados no app, dados e documentação

| Termo | Significado no contexto BB · DISEC |
|---|---|
| **EAP** (Estimativa Anual de Provisionamento) | Documento que projeta a contratação para o período; gera demanda para a CESUP-Contratações. |
| **EAP Padrão** | Modelo de EAP por categoria de objeto, com etapas-padrão pré-definidas. |
| **Etapa** | Sub-passo da execução da EAP/contrato (definição de objeto → publicação → habilitação → adjudicação → assinatura → execução → encerramento). |
| **Licitação Eletrônica** | Modalidade preferencial sob a Lei 13.303/16; equivale ao "pregão eletrônico" das estatais. |
| **DISEC** | Diretoria de Logística e Suprimentos do BB. |
| **CESUP-Contratações** | Centro de Suporte às Contratações da DISEC — área onde nasceu o Predfy. |
| **DICOI / DITEC / DISEC / GECOI** | Áreas demandantes que abrem EAPs e consomem o output do Predfy. |
| **Aditivo** | Alteração formal do escopo, prazo ou valor de um contrato em vigor. |
| **Intercorrência** | Evento que afeta o curso da Licitação Eletrônica (impugnação, recurso, suspensão). |

> Esta seção é o "glossário oficial" do projeto. O `system_prompt` do agente em `docs/agente/system_prompt.md` espelha exatamente esses termos para garantir que respostas conversacionais usem a linguagem da DISEC.

---

## Anexos / artefatos da entrega

| Artefato | Caminho no repositório |
|---|---|
| App principal Streamlit (Caminhos A/B/C) | `app_agente_bb.py` |
| Roteiro narrado para a banca avaliadora | **`docs/COMO_AVALIAR.md`** |
| Fluxograma da jornada (Mermaid) | `docs/FLUXOGRAMA.md` |
| Doc de acesso e instalação | `docs/ACESSO.md` |
| Relatório técnico estendido | `docs/RELATORIO_SOLUCAO.md` / `.docx` |
| Guia Copilot Studio passo-a-passo | `docs/COPILOT_STUDIO_GUIA.md` |
| Entrega comparativa Time 1 (Modelos) | `docs/ENTREGA_TIME1_MODELOS.md` / `.docx` |
| Entrega comparativa Time 2 (Agente IA + RPA) | `docs/ENTREGA_TIME2_AGENTE.md` / `.docx` |
| System prompt OpenAI (Caminho A) | `docs/agente/system_prompt.md` |
| Schema das 4 tools (Caminho A) | `docs/agente/tools_schema.json` |
| Manifest Copilot declarativo (Caminho B) | `teams_copilot/declarative-agent.json` |
| Instructions Copilot Studio (Caminho B) | `teams_copilot/instructions.md` |
| Script de turnos pré-gravados (Caminho C / modo demo) | `docs/demo/script_turnos.json` |
| Intérprete rule-based (modo demo) | `app/interprete_rules.py` |
| Geradores de dados sintéticos | `gerar_dados_sinteticos_eaps.py`, `gerar_dados_postgres.py` |
| Dicionário de dados | `dados_sinteticos/SCHEMA.md` |
| Dados sintéticos commitados | `dados_sinteticos/*.csv` (4 MB total, seed=42) |
| Notebook H2O do agente | `notebook_h2o_agente_mvp.ipynb` |
| Repo público | https://github.com/FranMarteen/hypercopa-disec-mvp |

---

*MVP Canvas elaborado para a banca avaliadora · HyperCopa DISEC 2026 · Banco do Brasil · 07/05/2026*
