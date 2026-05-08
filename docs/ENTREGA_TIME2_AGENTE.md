# Entrega MVP — Time 2 (Agente IA + RPA)

**HyperCopa DISEC 2026** · CESUP-Contratações · Banco do Brasil
**Produto:** **Predfy** — camadas de Agente Predfy (Etapa 1), Documentos (Etapa 4), Intérprete Predfy (Etapa 5) e Caso de Evento Real (Etapa 6)
**Data de entrega:** 07/05/2026

---

## 1. Identificação

| Item | Conteúdo |
|---|---|
| Time | Time 2 — **Inteligência Acionável para Compras e Fornecedores** |
| Camada no Predfy | Etapas 1, 4, 5 e 6 da jornada (Preparação + Pacote ZIP + Interpretação + Evento real) |
| Tema HyperCopa | Inteligência Acionável para Compras e Fornecedores |
| Equipe | **Time 2 — ECOA / CESUP-Contratações:** Bento 14 (capitão) · Felipe · Amélia · Vânia · Rafael |
| Cooperação | Time 1 (Modelos Analíticos) — consome JSON do relatório H2O |
| Repositório | https://github.com/FranMarteen/hypercopa-disec-mvp (público) |

---

## 2. Resumo executivo

A camada de interação do **Predfy** entrega um **Agente Predfy conversacional em três caminhos** (OpenAI direto + Microsoft Copilot do Teams + **Modo demonstração offline para a banca**) integrado a uma jornada Streamlit com identidade visual BB e stepper visual de 7 etapas. O agente conduz o usuário do CSV bruto ao relatório executivo em **3 a 5 minutos**, sem código.

A arquitetura **RAG + ChromaDB** da proposta original foi substituída por **Tool Use (function calling)** com sandbox `pandas`, decisão validada na Mentoria de Agentes IA (01-02/04). Os fluxos RPA de alertas via e-mail/Teams foram substituídos por:

- **Intérprete Predfy** rule-based local (`app/interprete_rules.py`) — UI estilo Teams que lê o JSON do relatório H2O e devolve resumo executivo + recomendações em PT-BR, sem rede externa.
- **3 cenários pré-roteirizados** na Etapa 6 (DICOI/DISEC/DITEC) com **semáforo visual de risco** 🟢/🟡/🔴.
- **Pacote ZIP unificado** na Etapa 4 (HTML + JSON + summary + canvas + instruções de reprodução) — banca anexa um único arquivo à entrega.

---

## 3. Comparativo — Proposto vs Realizado

### 3.1 Agente de IA

| Componente proposto (Mar/2026) | Status | O que foi entregue | Justificativa da mudança |
|---|---|---|---|
| LLM + RAG (LangChain + ChromaDB/FAISS) | 🟡 substituído | **OpenAI gpt-4o-mini com Tool Use (4 tools)**: `ler_schema`, `ler_amostra`, `executar_pandas`, `salvar_csv_final` — sandbox `exec()` com globals restritos | Function calling tem cobertura suficiente para o caso de uso (preparação de dados). RAG normativo (Lei 13.303) virou roadmap. |
| Interface Teams/Web | ✅ entregue (três caminhos) | **Caminho A:** chat embutido em Streamlit. **Caminho B:** Microsoft Copilot do Teams via Copilot Studio (declarativo). **Caminho C — Modo Demonstração offline:** player rule-based (`docs/demo/script_turnos.json`, 10 turnos pré-gravados) que executa as 4 tools reais no sandbox local — banca avalia jornada de 7 etapas inteira sem chave OpenAI/sem rede, com resultado idêntico em qualquer máquina (seed=42). | Caminho B é o de **produção BB** — trafega no tenant M365 sob acordo Microsoft↔BB com auditoria Microsoft Purview automática. Caminho C é o **caminho recomendado para a banca** (validação determinística sem dependências externas). |
| Alertas Proativos (anomalias, concentração, lock-in, picos) | 🟡 substituído | **Semáforo de risco** + interpretação executiva no Copilot do Teams a partir do JSON do relatório H2O | Alerta proativo via e-mail exige RPA agendado (fora de escopo MVP). Substituído por interpretação sob demanda — efeito equivalente ao usuário-demandante. |
| Consultas sob demanda (recorrência, fornecedor, volume, previsão) | ✅ entregue (genérico) | Agente entende qualquer pergunta preditiva (não fica preso aos 4 tipos da proposta) e dispara o pipeline H2O AutoML | Genericidade > catálogo fechado: 1 jornada cobre N perguntas. |
| Recomendações de Ação | ✅ entregue | Etapa 3 do app: Copilot do Teams traduz métricas (AUC, RMSE, importância) em recomendações de negócio | Em linguagem do demandante, não do cientista de dados. |

### 3.2 Stack tecnológico

| Camada proposta | Status | O que foi usado | Justificativa |
|---|---|---|---|
| Agente IA: LLM + RAG (Python/LangChain) | 🟡 substituído | OpenAI SDK direto + Tool Use; Microsoft Copilot Studio para Caminho B | LangChain agrega complexidade desnecessária para 4 tools determinísticas. Copilot Studio é mais alinhado à governança BB. |
| RAG: Vector DB (ChromaDB/FAISS) | 🔴 não implementado | n/a — schema + amostra cabem no contexto do LLM | Modelo de vetores prematuro. Roadmap: RAG de Lei 13.303/16 e EAPs Padrão. |
| RPA (automação): PowerAutomate / Python | 🟡 parcial | Sandbox Python in-app + Copilot do Teams (interpretação) | PowerAutomate exigiria integração com sistemas BB ainda fora de escopo. |
| RPA (ingestão): Python + cron | 🔴 não implementado | Substituído por upload manual no app | Coerente com decisão Time 1 (sem dados reais → sem cron de coleta). |
| Interface: Teams / Streamlit | ✅ entregue | **Streamlit single-page com identidade visual BB** + agente Copilot Studio publicável no Teams | Streamlit cobre Caminhos A e B; Teams é nativo no Caminho B. |
| Geração de mocks: Faker + numpy | ✅ entregue | `gerar_dados_sinteticos_eaps.py`, `gerar_dados_postgres.py` (Time 1 produziu, Time 2 valida) | Coerência com o contrato Time 1↔Time 2: o schema único do JSON do relatório H2O elimina a separação mocks/reais. |

### 3.3 RPA — Automação de Processos e Alertas

| Fluxo proposto | Status | O que foi entregue | Justificativa |
|---|---|---|---|
| Ingestão de outputs (semanal) | 🟡 substituído | App lê o CSV final e o JSON do relatório H2O sob demanda | Sem cron porque sem dados reais; jornada é orientada a evento (usuário sobe CSV). |
| Disparo de alertas via e-mail/Teams | 🟡 substituído | **Interpretação Copilot Teams sob demanda** + semáforo no relatório HTML | E-mail automático fica para evolução RPA real. |
| Flag em processos (sistema de aprovação) | 🔴 não implementado | n/a — não há sistema de aprovação acessível | Roadmap: integração via API com sistemas internos BB. |
| Relatórios periódicos (mensal) | ✅ entregue (sob demanda) | **Relatório HTML autocontido** com identidade BB + JSON estruturado, gerado em segundos | Mensalidade trocada por geração instantânea: o usuário pede quando precisa. |
| Registro de ações (feedback loop) | 🔴 não implementado | n/a | Roadmap: persistência de conversas em banco BB. |
| Validação documental SICAF | 🔴 não implementado | n/a | Fora do escopo MVP. |

### 3.4 Estratégia de dados mockados → integração com Time 1

| Fase proposta | Status |
|---|---|
| Plano de Jogo (26-31/03) — definir schema | ✅ realizado: schema único = JSON do relatório H2O |
| Sprint 1-2: desenvolvimento sobre mocks | ✅ realizado: app testado com CSVs sintéticos |
| Integração 26-27/04: substituir mocks por outputs reais do Time 1 | ✅ realizado: como o schema é o do relatório H2O, integração foi nativa — não houve "troca" porque não há dois pipelines |

> **Sinergia:** o schema único (JSON do relatório H2O) eliminou a necessidade de mocks específicos por output. O Time 2 sempre operou sobre o schema final.

---

## 4. Decisões de adaptação (registro técnico)

1. **RAG → Tool Use.** Function calling com 4 tools determinísticas atende preparação de dados com mais auditabilidade do que RAG. RAG fica para a evolução (jurisprudência Lei 13.303, EAPs Padrão).
2. **LangChain → OpenAI SDK direto.** Reduz dependência de framework e ganha controle sobre o sandbox de execução.
3. **Caminho B (Microsoft Copilot do Teams) é a contribuição inesperada.** Não estava na proposta original, mas é o caminho de produção BB: zero custo marginal (incluso na licença Copilot já paga), tenant M365 sob acordo, auditoria Microsoft Purview automática. Materializado via Copilot Studio (declarativo, sem código).
4. **Alertas push → interpretação pull.** Em vez de e-mail/Teams disparado por anomalia, o usuário pede análise quando precisa e o Copilot interpreta. Mais barato e mais respeitoso da atenção dos gestores.
5. **Identidade visual BB de série.** Paleta `#FAE128` / `#003DA5`, IBM Plex Sans (proxy de BB Texto). Substituição por BB Texto/BB Títulos quando licenciados é trivial via `@font-face`.
6. **Privacidade by design.** Caminho A: só schema + 20 linhas de amostra saem para OpenAI. Caminho B: CSV completo nunca sai do laptop — só amostra trafega pelo Teams (no tenant BB).

---

## 5. Métricas de performance — Proposto vs Obtido

| Métrica (proposta) | Critério | Componente | Obtido | Status |
|---|---:|---|---:|---|
| Tempo de resposta do Agente | < 10 s | Agente IA | < 10 s nas 4 tools (preparação) | ✅ |
| Acurácia das respostas | > 85 % (validação por gestores) | Agente IA + RAG | a aferir em piloto DISEC | 🟡 |
| Cobertura de alertas | 100 % dos eventos críticos | RPA de alertas | n/a (alertas substituídos por interpretação Copilot) | 🟡 redirecionado |
| Tempo de geração de relatórios | < 5 min | RPA de relatórios | **< 5 s** (HTML autocontido) | ✅ |
| Taxa de integração (mock → real) | 100 % | Integração com Time 1 | **100 %** — schema único | ✅ |
| Satisfação dos gestores (piloto) | > 4,0 / 5,0 | Agente IA | a aferir em piloto DISEC | 🟡 |
| **Tempo CSV bruto → modelo treinado** *(novo)* | — | Jornada completa | **3-5 min** | ✅ |
| **Custo marginal por conversa** *(novo)* | — | Caminho B | **R$ 0** (Caminho B) / R$ 0,30 (A) | ✅ |
| **Linhas de código escritas pelo demandante** *(novo)* | — | Jornada | **0** | ✅ |

---

## 6. Riscos e mitigações — Status

| Risco da proposta | Probabilidade prevista | O que aconteceu |
|---|---|---|
| Mocks não representam realidade | Média | **Não materializou.** O schema único do relatório H2O eliminou a separação. |
| Integração falha no final | Média | **Não materializou.** Schema único garantiu integração nativa. |
| Agente gera respostas incorretas | Média | **Mitigação ativa:** sandbox `exec()` com globals restritos; system_prompt versionado em git; até 8 iterações tool↔LLM por turno. |
| Latência do Agente alta | Baixa | Não materializou. < 10 s consistente com `gpt-4o-mini`. |
| Prazo apertado | Alta | **Materializou-se.** Mitigação ativada: priorização do MVP mínimo (Agente + relatório); RAG, alertas push e SICAF viraram roadmap. |

---

## 7. Funções do Agente — Cobertura

| Função proposta | Status no MVP | Observação |
|---|---|---|
| Alertas de anomalia | 🟡 substituído por semáforo no relatório | Disparo proativo via e-mail = roadmap |
| Alertas de concentração HHI | 🟡 substituído por interpretação Copilot | idem |
| Alertas de lock-in | 🟡 substituído por interpretação Copilot | idem |
| Alertas de pico de demanda | 🟡 redirecionado para predição de prazo | em coerência com pivotagem do Time 1 |
| Consultas de recorrência | 🟡 protótipo via Time 1 | RAG interpretativo no roadmap |
| Consultas de fornecedores | 🟡 protótipo via Time 1 | idem |
| Consultas de volume | 🟡 protótipo via Time 1 | idem |
| Consultas de forecast | ✅ entregue como predição de prazo | regressão GBM Modelo 1 |
| Recomendação de modalidade | 🟡 roadmap | depende de RAG normativo |
| Recomendação de diversificação | 🟡 roadmap | depende de outputs HHI promovidos |
| Recomendação de redistribuição | 🟡 roadmap | depende de modelo de volume promovido |

---

## 8. Artefatos entregues — Time 2

| Categoria | Artefato | Caminho |
|---|---|---|
| App principal | Streamlit single-page (Caminhos A e B) | `app_agente_bb.py` |
| Identidade visual | Paleta BB + IBM Plex Sans + CSS embutido | `app_agente_bb.py` (CSS inline) |
| System prompt do Agente (Caminho A) | Prompt versionado em git | `docs/agente/system_prompt.md` |
| Schema das 4 tools (Caminho A) | JSON Schema OpenAI | `docs/agente/tools_schema.json` |
| Manifest do Copilot declarativo (Caminho B) | Declarative agent manifest | `teams_copilot/declarative-agent.json` |
| Instruções do Copilot Studio (Caminho B) | System prompt para Copilot Studio | `teams_copilot/instructions.md` |
| OpenAPI das actions (Caminho B) | Esqueleto OpenAPI | `teams_copilot/actions_openapi.yaml` |
| Guia Copilot Studio passo-a-passo | Como publicar o agente no Teams | `docs/COPILOT_STUDIO_GUIA.md` |
| Fluxograma da jornada | Mermaid, dois caminhos | `docs/FLUXOGRAMA.md` |
| Doc de acesso e instalação | Pré-requisitos + roteiro de vídeo | `docs/ACESSO.md` |
| Geração de relatório HTML | Template autocontido com identidade BB | `app_agente_bb.py` (função embutida) |
| Demos de jornada CLI | Reprodutível para testes | `demo_jornada.py` · `gerar_demo_eaps.py` |
| Relatórios gerados (exemplos) | Provas de execução | `relatorios/relatorio_*.html` + `.json` |
| API REST (esqueleto) | FastAPI para evolução | `api/main.py` |
| Repositório privado | GitHub | https://github.com/FranMarteen/hypercopa-disec-mvp |

---

## 9. Próximos passos (pós-MVP até Pitch Day 10/06/2026)

1. **Publicar o agente Copilot do Teams oficialmente** — submeter `teams_copilot/declarative-agent.json` ao admin M365 BB (Caminho B em produção).
2. **RAG da Lei 13.303/16 + EAPs Padrão.** ChromaDB ou Vector DB do tenant Microsoft.
3. **Alertas push** (e-mail/Teams) quando a integração com sistemas internos BB liberar trigger por evento.
4. **Validação SICAF** via API SICAF (quando acesso for liberado).
5. **Piloto DISEC** com 4 áreas-cliente (DICOI, DISEC, DITEC, GECOI) para aferir métrica de "satisfação dos gestores > 4,0/5,0" da proposta original.
6. **Persistência de conversas em banco BB** para auditoria e feedback loop.
7. **Substituir IBM Plex Sans** pelas fontes oficiais BB (BB Texto / BB Títulos) via `@font-face` quando licenciadas.

---

*Entrega Time 2 — HyperCopa DISEC 2026 · 07/05/2026*
