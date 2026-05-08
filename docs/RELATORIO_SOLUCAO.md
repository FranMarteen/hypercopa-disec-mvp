# Relatório da Solução — Predfy

## Predfy — Agente Predfy + Modelo Analítico H2O AutoML + Intérprete Predfy

**HyperCopa DISEC 2026** · Banco do Brasil · CESUP-Contratações
**Repositório público:** https://github.com/FranMarteen/hypercopa-disec-mvp

> Documento elaborado para a banca avaliadora.
> **Versão 2.0 · 07/05/2026** — atualizada com modo demonstração offline,
> stepper visual de 7 etapas, simulador local do agente Teams (rule-based),
> cenários pré-roteirizados na Etapa 6 com semáforo, pacote ZIP unificado
> da entrega e reprodutibilidade total (seed=42).

---

## 1. Sumário executivo

A jornada **Predfy — Preparador + Modelo Analítico** transforma um extrato bruto de Licitação Eletrônica em um **modelo preditivo treinado e auditável** em **menos de 5 minutos**, sem que o usuário de negócio escreva uma única linha de código.

A solução resolve a maior dor da DISEC ao operacionalizar analytics: **o tempo entre receber um extrato da área e ter uma resposta acionável**. Hoje esse ciclo é de **dias a semanas** (DBA → Cientista de Dados → Validação → Modelo). Nossa solução reduz para **minutos**, mantendo a governança técnica via `system_prompt` versionado e sandbox de execução.

| Indicador | Antes | Com a solução |
|---|---:|---:|
| Tempo CSV bruto → modelo treinado | 3-10 dias | **3-5 minutos** |
| Linhas de código escritas pelo usuário | 50-300 | **0** |
| Pessoas envolvidas no ciclo | 3-4 | **1** |
| Risco de vazamento (CSV completo p/ LLM) | alto | **zero** (só schema + 20 linhas amostra) |

---

## 2. Contexto e problema

### 2.1 Realidade DISEC

A DISEC do Banco do Brasil opera **Licitação Eletrônica** sob a Lei 13.303/16. As áreas demandantes (DICOI, DISEC, DITEC, GECOI) periodicamente recebem perguntas de negócio:

- *"Quais EAPs vão atrasar nos próximos 30 dias?"*
- *"Qual o risco de ruptura contratual desta carteira?"*
- *"Que fornecedores tendem a ter intercorrências?"*

### 2.2 O gargalo

Hoje, transformar essas perguntas em modelos passa por:

1. Solicitar extrato a um DBA (1-3 dias).
2. Cientista de dados explora, limpa, gera features (2-5 dias).
3. Treinar e validar o modelo (1-2 dias).
4. Apresentar resultado.

**Custo de oportunidade:** decisões adiadas, contratos que rompem antes da análise ficar pronta, perda de janelas regulatórias.

### 2.3 Decisões estratégicas tomadas

| Decisão | Motivo |
|---|---|
| **Dados 100% sintéticos** | Acesso a dados reais inviável no prazo do hackathon. Geração via `Faker` + regras de negócio realistas. |
| **3 modelos preditivos via H2O AutoML** | GBM venceu na maioria dos casos; H2O permite trocar de algoritmo sem reescrita. |
| **Agente IA via OpenAI function calling** | Pattern maduro (Tool Use), 4 tools auditáveis, sem RAG inicial (escopo justo para MVP). |
| **Streamlit single-page** | Uma URL, tipografia BB, jornada linear — pensada para demanda recorrente, não para data scientists. |

---

## 3. Arquitetura

A solução tem **três caminhos paralelos** para a fase conversacional, com a mesma camada de treino, intérprete e relatório local. **Caminho A** (OpenAI direto) é dev local; **Caminho B** (Microsoft Copilot do Teams) é produção BB; **Caminho C** (Modo Demonstração offline) é o caminho recomendado para a banca avaliadora.

### 3.1 Caminho A — OpenAI direto (chat embutido no app)

```
┌──────────────────────────────────────────────┐
│  APP STREAMLIT (Caminho A)                   │
│                                              │
│  Chat OpenAI ──▶ 4 tools ──▶ CSV ──▶ H2O    │
│  (gpt-4o-mini)   (sandbox)         (local)   │
└──────────────────────────────────────────────┘
              │
              ▼ (apenas schema + 20 linhas)
        ┌─────────────┐
        │   OpenAI    │
        └─────────────┘
```

**Quando usar:** desenvolvimento, demo externa, fora da rede BB.

### 3.2 Caminho B — Microsoft Copilot do Teams (sem API, copy-paste)

```
┌────────────────────┐                ┌────────────────────────┐
│  Microsoft Copilot │                │  App Streamlit local   │
│  no Teams (BB)     │ ◀── copia ──▶ │  (Caminho B)           │
│                    │   bloco /JSON  │  H2O AutoML + relat.   │
└────────────────────┘                └────────────────────────┘
        │
        ▼ (tenant M365 BB, governado)
        Microsoft Purview / DLP BB
```

**Quando usar:** produção BB. Trafega pelo tenant M365 BB sob acordo Microsoft↔BB. Sem custo OpenAI, sem chave individual, com auditoria automática.

> **Como criar o agente Copilot Studio:** ver `docs/COPILOT_STUDIO_GUIA.md` (passo-a-passo, 20-30 min, sem código).

### 3.3 Caminho C — Modo Demonstração offline (banca avaliadora)

```
┌──────────────────────────────────────────────────────┐
│  APP STREAMLIT — Modo demo (Caminho C)               │
│                                                       │
│  ▶ Player de turnos pré-gravados                     │
│  ──▶ docs/demo/script_turnos.json (10 turnos)        │
│  ──▶ tool_calls REAIS no sandbox local               │
│  ──▶ CSV final + meta.json                           │
│  ──▶ H2O AutoML (seed=42, 60s) ──▶ Relatório         │
└──────────────────────────────────────────────────────┘
              │
              ▼ (zero rede externa)
        ┌─────────────────────────┐
        │   NADA SAI DO LAPTOP    │
        └─────────────────────────┘
```

**Por que Caminho C existe.** A banca testa em ambientes restritos (sem chave OpenAI, sem rede pública confiável) e tem janela curta de avaliação. Caminho C dispensa **qualquer** dependência externa — toda a jornada de 7 etapas roda offline, com cenário pré-curado *"EAP DICOI / vai atrasar?"* e **resultado idêntico em qualquer máquina** (seed=42).

**Como funciona.**

1. Banca ativa o toggle **🎓 Modo demonstração da banca** na sidebar.
2. App pré-carrega `dados_sinteticos/contratos.csv` (1.959 linhas).
3. Botão **▶ Próximo turno** lê o próximo turno determinístico de `docs/demo/script_turnos.json`.
4. Cada turno executa **as mesmas 4 ferramentas** dos Caminhos A/B (`ler_schema`, `ler_amostra`, `executar_pandas`, `salvar_csv_final`) **de verdade** no sandbox local — só o "pensar" do LLM é substituído por leitura do script.
5. Após o turno 10, o CSV final está pronto e a Etapa 2 desbloqueia.
6. Etapas 2–4 são idênticas aos demais caminhos.
7. Etapa 5 usa o intérprete rule-based local `app/interprete_rules.py` (UI estilo Teams, sem rede).
8. Etapa 6 oferece **3 cenários pré-roteirizados** (DICOI / DISEC / DITEC) com **semáforo 🟢🟡🔴** + recomendação operacional.

**Quando usar:** avaliação da banca, demos em ambientes sem rede, validação de reprodutibilidade.

> **Auditabilidade total.** O `script_turnos.json` é versionado em git — qualquer revisor pode comparar passo-a-passo o que o agente "diz" no Caminho C com o que o LLM faria nos Caminhos A/B (mesmo `system_prompt`).

### 3.4 As 4 tools do agente (Caminhos A e C) / blocos estruturados (Caminho B)

| Operação | Caminho A (tool OpenAI) | Caminho B (saída do Copilot) |
|---|---|---|
| Inspecionar schema | `ler_schema` | parte do bloco `PERGUNTA / TARGET / TASK` |
| Ler amostra | `ler_amostra` | usuário cola a amostra na conversa |
| Executar preparação | `executar_pandas` (sandbox) | `PASSO_A_PASSO_PANDAS` no bloco, executado pelo app |
| Salvar CSV final | `salvar_csv_final` | botão "Processar bloco" no app |

### 3.5 Os 3 modelos preditivos disponíveis

| # | Modelo | Tipo | Target | Uso |
|---|---|---|---|---|
| 1 | **Prazo de contratação** | Regressão GBM | dias até assinatura | priorizar EAPs com risco de estouro |
| 2 | **Intercorrência** | Classificação binária GBM | houve impugnação/recurso? | alocação de jurídico |
| 3 | **Ruptura contratual** | Classificação binária GBM | houve rescisão? | retenção de fornecedores |

---

## 4. Identidade visual e UX

### 4.1 Tipografia
- **Fonte primária**: IBM Plex Sans (Google Fonts) — humanista, semelhante a *BB Texto*.
- **Substituição futura**: troca trivial via `@font-face` para fontes oficiais BB quando licenciadas.

### 4.2 Paleta
- Amarelo BB `#FAE128` (Pantone 116C) — destaque, CTAs, header stripe.
- Azul BB `#003DA5` (Pantone 286C) — títulos, ícones, header.
- Azul Escuro BB `#002D72` — gradiente do header.
- Cinza BB `#5C6670` — texto secundário.

### 4.3 Princípios da jornada
1. **Uma URL, uma jornada** — sem multi-page do Streamlit.
2. **Sidebar = estado**, **centro = ação** — usuário vê uploads e CSV gerado à esquerda, age no centro.
3. **Etapa 2 desbloqueia automaticamente** quando o agente entrega o CSV — sem necessidade de navegação.
4. **Relatório HTML autocontido** — abre em qualquer navegador, sem dependências, com identidade BB.
5. **Stepper visual de 7 etapas** no topo de toda a página — círculos numerados na paleta BB (atual em amarelo, concluídos em azul, futuros em cinza). Banca acompanha o progresso em tempo real, sem precisar lembrar onde está.
6. **Banner amarelo "Modo demonstração"** confirma sessão Caminho C; **botão único "📦 Baixar pacote"** na Etapa 4 entrega o ZIP unificado; **semáforo 🟢🟡🔴** na Etapa 6 traduz a probabilidade em decisão.

### 4.4 Pacote ZIP unificado da entrega (Etapa 4)

O botão **"📦 Baixar pacote da entrega"** monta em memória um único `.zip` com **5 artefatos auditáveis**:

| Arquivo | Função |
|---|---|
| `relatorio.html` | Relatório visual autocontido (paleta BB) |
| `relatorio.json` | Estrutura para auditoria + Copilot |
| `summary.md` | Resumo executivo de 1 página |
| `como_reproduzir.txt` | Comandos para regerar o resultado em qualquer máquina |
| `MVP_CANVAS.md` / `.docx` | Canvas do MVP completo |

> Esse ZIP é o anexo único da entrega oficial à banca. Substitui o vídeo regulamentar.

---

## 5. Privacidade e governança

| Risco | Mitigação Caminho A | Mitigação Caminho B |
|---|---|---|
| CSV inteiro vazar para LLM | Apenas schema + ≤20 linhas saem para OpenAI | CSV completo **nunca** sai do laptop; só amostra trafega pelo Teams |
| LLM público fora do controle BB | Risco residual aceito em piloto | **Eliminado**: Copilot M365 sob acordo BB↔Microsoft |
| Código gerado executar comando malicioso | Sandbox: `exec()` com globals restritos | Mesmo sandbox; bloco `PASSO_A_PASSO_PANDAS` validado |
| Chave/credencial vazar | `.gitignore` protege `.env` | Sem chave individual — usa licença Copilot do tenant |
| Dados reais BB em repo externo | `.gitignore` bloqueia `dados reais/` | Idem |
| Auditabilidade | Logs Streamlit + git do `system_prompt` | **Microsoft Purview** automático |
| Custo marginal por conversa | ~ R$ 0,30 (OpenAI) | **R$ 0** (incluso em licença Copilot) |

---

## 6. Resultados e métricas

### 6.1 Performance dos 3 modelos (dados sintéticos, 60s budget)

| Modelo | Métrica primária | Valor (teste) |
|---|---|---:|
| Prazo (regressão) | RMSE / R² | ~ 18 dias / 0.82 |
| Intercorrência (classificação) | AUC | ~ 0.84 |
| Ruptura (classificação) | AUC | ~ 0.79 |

> **Observação**: valores típicos obtidos em rodadas de validação no MVP. A solução final medirá exatamente as métricas de cada execução no relatório HTML.

### 6.2 Métricas operacionais

- **3-5 minutos** do CSV cru ao modelo treinado.
- **0 linhas de código** escritas pelo usuário de negócio.
- **15 turnos** máximos por conversa (limite de segurança).
- **8 iterações** máximas tool↔LLM por turno.

---

## 7. ROI estimado (cenário DISEC anualizado)

> Estimativas conservadoras com hipóteses anotadas — não são compromissos.

| Item | Hipótese | Valor anual |
|---|---|---:|
| **Demandas evitadas a cientista de dados** | 60 demandas/ano × 6h economizadas | 360h |
| **Economia em homem-hora (R$ 150/h carregado)** | 360h × R$ 150 | **R$ 54.000** |
| **Contratos com ruptura evitada** | 0,5% de 4.000 contratos × R$ 200k médio | **R$ 4.000.000** |
| **Custo Caminho A (OpenAI)** | 1.000 conversas × R$ 0,30 | R$ 300 |
| **Custo Caminho B (Copilot Teams)** | já incluso em licença M365 BB | **R$ 0** |
| **Saldo estimado primeiro ano** | — | **~ R$ 4 MM** |

---

## 8. Plano de evolução

### 8.1 Curto prazo (até Pitch Day, 10/06/2026)
- [x] MVP funcional com agente + 3 modelos.
- [x] Identidade visual BB.
- [x] Relatório HTML auto-contido.
- [ ] Demonstração com extratos sintéticos das 4 áreas (DICOI, DISEC, DITEC, GECOI).
- [ ] Vídeo de 2 min + slides de pitch.

### 8.2 Médio prazo (após aprovação)
- [ ] Substituir IBM Plex Sans pelas fontes oficiais BB (BB Texto / BB Títulos).
- [ ] Publicar agente Copilot no Teams via Copilot Studio (Caminho B oficial — ver `docs/COPILOT_STUDIO_GUIA.md`).
- [ ] RAG com EAPs Padrão e jurisprudência da Lei 13.303/16.
- [ ] Integração com Microsoft Teams (Copilot Studio — já há `teams_copilot/declarative-agent.json`).
- [ ] Persistência das conversas em banco BB para auditoria.

### 8.3 Longo prazo
- [ ] Out-of-time validation automática a cada trimestre.
- [ ] Detecção de drift nas variáveis top do leaderboard.
- [ ] Recomendação ativa: agente alerta a área quando uma EAP cruzar o limiar de risco.
- [ ] API REST (já há `api/main.py` em FastAPI) para consumo por sistemas internos BB.

---

## 9. Estrutura entregável

| Entregável | Arquivo | Status |
|---|---|---|
| App principal (Caminhos A e B) | `app_agente_bb.py` | ✅ |
| System prompt OpenAI (Caminho A) | `docs/agente/system_prompt.md` | ✅ |
| Schema das 4 tools (Caminho A) | `docs/agente/tools_schema.json` | ✅ |
| System prompt Copilot Studio (Caminho B) | `teams_copilot/instructions.md` | ✅ |
| Manifest Copilot declarativo | `teams_copilot/declarative-agent.json` | ✅ |
| **Guia Copilot Studio passo-a-passo** | `docs/COPILOT_STUDIO_GUIA.md` | ✅ |
| Fluxograma da jornada (2 caminhos) | `docs/FLUXOGRAMA.md` | ✅ |
| Doc de acesso e instalação | `docs/ACESSO.md` | ✅ |
| Relatório de avaliação (este) | `docs/RELATORIO_SOLUCAO.md` / `.docx` | ✅ |
| Dados sintéticos | `dados_sinteticos/`, `dados_postgres/` | ✅ |
| Modelos preditivos base | `modelos_preditivos.py`, `modelos_mvp_base.py` | ✅ |
| Repo privado GitHub | https://github.com/FranMarteen/hypercopa-disec-mvp | ✅ |

---

## 10. Equipe e responsabilidades

**Time 1 — Modelos Analíticos (camada analítica):**
- **João 23** (capitão) · Francisco · Rosali · Silvia.
- Responsabilidades: dados sintéticos, modelagem H2O AutoML, validação dos 3 modelos, schema unificado de saída JSON.

**Time 2 — Agente IA + RPA (camada de interação):**
- **Bento 14** (capitão) · Felipe · Amélia · Vânia · Rafael.
- Responsabilidades: Agente Predfy (Caminhos A/B/C), pacote ZIP unificado, Intérprete Predfy, semáforo Etapa 6, identidade visual BB.

**Apoio:** DISEC / CESUP-Contratações — terminologia oficial BB e conformidade Lei 13.303/16.

---

## 11. Conclusão

A solução demonstra que **velocidade analítica** é alcançável sem sacrificar **governança**. A separação entre *o que sai para o LLM* (apenas metadados e amostra) e *onde o modelo é treinado* (local, na JVM do H2O) garante **conformidade com políticas BB de classificação de dados** mesmo em um piloto rodado fora do datacenter.

A jornada está pronta para apresentação ao Pitch Day em **10/06/2026**.

---

*Relatório gerado em 2026-05-06 · DISEC · Banco do Brasil*
