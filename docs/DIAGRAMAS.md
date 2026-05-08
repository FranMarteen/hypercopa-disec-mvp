# Diagramas — Predfy

Diagramas Mermaid da arquitetura, jornada e fluxo de dados do Predfy.
Renderizados nativamente no GitHub e em qualquer Markdown viewer com Mermaid.

---

## 1. Visão geral — Jornada de 7 etapas e os 3 caminhos

```mermaid
flowchart TB
    subgraph DADOS["📂 Etapa 0 — Dados sintéticos (seed=42)"]
        G[gerar_dados_sinteticos_eaps.py] --> CSV1[eaps.csv 2.500]
        G --> CSV2[contratos.csv 1.959]
        G --> CSV3[etapas, participantes, fornecedores]
    end

    subgraph PREP["🤖 Etapa 1 — Agente Predfy"]
        direction LR
        A[Caminho A<br/>OpenAI direto<br/>chat embutido]
        B[Caminho B<br/>Copilot Teams<br/>paste do bloco]
        C[Caminho C<br/>Modo demo<br/>turnos pré-gravados]
    end

    DADOS --> PREP
    PREP -->|CSV final + meta.json| TREINO[📊 Etapa 2<br/>H2O AutoML<br/>GBM · GLM · XGBoost · RF]
    TREINO --> AVAL[📈 Etapa 3<br/>Avaliar<br/>leaderboard · métricas · varimp]
    AVAL --> DOCS[📥 Etapa 4<br/>Pacote ZIP<br/>HTML+JSON+summary+canvas]
    DOCS --> INTERP[💬 Etapa 5<br/>Intérprete Predfy<br/>resumo + recomendações]
    INTERP --> EVENT[🔮 Etapa 6<br/>Caso de evento real<br/>3 cenários · semáforo 🟢🟡🔴]

    style DADOS fill:#FAE128,stroke:#003DA5,stroke-width:2px,color:#1F1F1F
    style PREP fill:#003DA5,stroke:#FAE128,stroke-width:2px,color:#FFFFFF
    style TREINO fill:#003DA5,stroke:#FAE128,stroke-width:2px,color:#FFFFFF
    style AVAL fill:#003DA5,stroke:#FAE128,stroke-width:2px,color:#FFFFFF
    style DOCS fill:#FAE128,stroke:#003DA5,stroke-width:2px,color:#1F1F1F
    style INTERP fill:#003DA5,stroke:#FAE128,stroke-width:2px,color:#FFFFFF
    style EVENT fill:#FAE128,stroke:#003DA5,stroke-width:2px,color:#1F1F1F
    style A fill:#FFFFFF,stroke:#003DA5,color:#1F1F1F
    style B fill:#FFFFFF,stroke:#003DA5,color:#1F1F1F
    style C fill:#FAE128,stroke:#003DA5,stroke-width:3px,color:#1F1F1F
```

> **Caminho C destacado** porque é o que a **banca avaliadora** usa: dispensa chave OpenAI e qualquer rede externa.

---

## 2. Privacidade — fluxo de dados sensíveis

```mermaid
flowchart LR
    subgraph LOCAL["💻 Laptop do usuário (CSV completo nunca sai daqui)"]
        CSV[CSV bruto<br/>milhares de linhas]
        SAND[Sandbox pandas<br/>exec restrito]
        H2O_LOCAL[H2O AutoML<br/>JVM local]
        REL[Relatório HTML<br/>+ JSON]
    end

    subgraph EXT["🌐 Externo"]
        OAI[OpenAI API<br/>Caminho A]
        TEAMS[Copilot Teams<br/>tenant M365 BB · Caminho B]
        DEMO[Caminho C<br/>NADA sai]
    end

    CSV -->|schema + 20 linhas amostra| OAI
    CSV -->|amostra colada manualmente| TEAMS
    CSV -.->|zero rede| DEMO

    OAI -->|código pandas| SAND
    TEAMS -->|bloco PASSO_A_PASSO| SAND
    DEMO -->|tool_calls do script| SAND

    SAND --> H2O_LOCAL
    H2O_LOCAL --> REL

    style LOCAL fill:#F7F8FA,stroke:#003DA5,stroke-width:2px
    style EXT fill:#FFFFFF,stroke:#5C6670,stroke-width:1px
    style DEMO fill:#FAE128,stroke:#003DA5,stroke-width:2px,color:#1F1F1F
    style OAI fill:#FFFFFF,stroke:#cf2a2a
    style TEAMS fill:#FFFFFF,stroke:#5059C9
```

**Garantias:**
- O **CSV completo nunca sai do laptop**, em nenhum dos 3 caminhos.
- No **Caminho A**, apenas schema + 20 linhas de amostra trafegam para OpenAI.
- No **Caminho B**, o usuário escolhe o que cola no Teams (texto pequeno, dentro do tenant BB).
- No **Caminho C** (banca), **zero rede externa**.

---

## 3. Sequência típica — sessão da banca em modo demo

```mermaid
sequenceDiagram
    autonumber
    actor Banca as 👤 Banca
    participant App as Predfy (Streamlit)
    participant Script as docs/demo/script_turnos.json
    participant Sand as Sandbox pandas
    participant H2O as H2O AutoML local
    participant Rules as app/interprete_rules.py

    Banca->>App: Ativa "Modo demonstração"
    App->>App: Pré-carrega contratos.csv (1.959 linhas)
    App-->>Banca: Banner amarelo + Stepper 7 etapas

    loop 10 turnos pré-gravados
        Banca->>App: ▶ Próximo turno
        App->>Script: lê próximo turno
        alt turno tem tool_calls
            App->>Sand: executa ler_schema / ler_amostra / executar_pandas
            Sand-->>App: resultado
            App-->>Banca: mostra DataFrame / schema
        else turno só de texto
            App-->>Banca: mostra mensagem do agente
        end
    end

    App->>App: salvar_csv_final (CSV final + meta.json)
    Banca->>App: 🚀 Treinar modelo H2O (60s)
    App->>H2O: AutoML(seed=42, max_runtime=60s)
    H2O-->>App: leaderboard + leader + métricas
    App-->>Banca: AUC ~0,84 · top features · curva ROC

    Banca->>App: 📦 Baixar pacote da entrega
    App-->>Banca: hypercopa_pacote_TS.zip<br/>(HTML+JSON+summary+canvas)

    Banca->>App: Etapa 5 — Interpretar
    App->>Rules: interpretar_relatorio(JSON)
    Rules-->>App: resumo + métricas traduzidas + 5 recomendações
    App-->>Banca: UI estilo Teams (header roxo)

    Banca->>App: Etapa 6 — Cenário B (DISEC/Reforma/ME)
    App->>App: pré-preenche form com caso real do teste
    Banca->>App: 🔮 Consultar modelo
    App->>H2O: predict
    H2O-->>App: classe + probabilidade
    App-->>Banca: 🟡 Risco moderado · ação sugerida · gabarito
```

---

## 4. Mapa de tecnologias por camada

```mermaid
flowchart TB
    subgraph UI["UX / Frontend"]
        STREAMLIT[Streamlit single-page<br/>Identidade visual BB<br/>Stepper visual 7 etapas]
        TEAMS_UI[Microsoft Teams<br/>Copilot Studio]
    end

    subgraph LLM["LLM / Agente"]
        OPENAI[OpenAI API<br/>gpt-4o-mini · Tool Use<br/>4 tools auditáveis]
        COPILOT_LLM[Microsoft Copilot M365<br/>tenant BB]
        DEMO_PLAYER[Player rule-based<br/>script_turnos.json]
        RULES[interprete_rules.py<br/>tradutor JSON→PT-BR]
    end

    subgraph EXEC["Execução"]
        SANDBOX[exec sandbox<br/>globals restritos<br/>pandas + numpy]
    end

    subgraph ML["Machine Learning"]
        H2O_AML[H2O AutoML 3.46.0.6<br/>GBM · GLM · XGBoost · RF<br/>seed=42]
    end

    subgraph DATA["Dados"]
        SYNTH[Geradores Python<br/>seed=42<br/>Lei 13.303/16]
        CSV_DATA[6 datasets relacionais<br/>commitados no repo]
    end

    subgraph OUT["Saídas"]
        HTML[HTML autocontido]
        JSON_OUT[JSON estruturado]
        ZIP[Pacote ZIP unificado]
    end

    UI --> LLM
    LLM --> EXEC
    EXEC --> ML
    DATA --> EXEC
    ML --> OUT
    OUT --> RULES

    style UI fill:#FAE128,stroke:#003DA5,color:#1F1F1F
    style LLM fill:#003DA5,stroke:#FAE128,color:#FFFFFF
    style EXEC fill:#5C6670,stroke:#FAE128,color:#FFFFFF
    style ML fill:#003DA5,stroke:#FAE128,color:#FFFFFF
    style DATA fill:#F7F8FA,stroke:#003DA5,color:#1F1F1F
    style OUT fill:#FAE128,stroke:#003DA5,color:#1F1F1F
```

---

## 5. Visão de produção — futuro Predfy no BB

```mermaid
flowchart LR
    subgraph HOJE["📦 MVP HyperCopa (07/05/2026)"]
        APP_LOCAL[App local Streamlit<br/>3 caminhos A/B/C<br/>dados sintéticos]
    end

    subgraph PROD["🏦 Predfy em produção BB"]
        PORTAL[Portal BB / Plataforma<br/>integrado ao fluxo]
        AGENTE_BB[Agente Predfy<br/>publicado no Copilot Studio<br/>tenant M365 BB]
        DADOS_REAIS[Dados reais BB<br/>via API + governança]
        H2O_BB[H2O AutoML em ambiente BB<br/>retreino periódico]
        ALERTAS[Alertas proativos<br/>e-mail · Teams · Dashboards]
    end

    subgraph BENEF["📊 Benefício para o BB"]
        DEC[Decisão preventiva<br/>de risco]
        PRZ[Prazos reais<br/>por carteira]
        REUSE[Reuso para qualquer<br/>extrato / domínio]
    end

    HOJE -->|hospedar em ambiente BB<br/>+ aprovação Copilot Studio| PROD
    PROD --> BENEF
    AGENTE_BB -.->|minimiza fricção<br/>sem código novo| REUSE

    style HOJE fill:#FAE128,stroke:#003DA5,color:#1F1F1F
    style PROD fill:#003DA5,stroke:#FAE128,color:#FFFFFF
    style BENEF fill:#1f9e54,stroke:#003DA5,color:#FFFFFF
    style REUSE fill:#FAE128,stroke:#003DA5,stroke-width:3px,color:#1F1F1F
```

> **Tese da equipe:** o **Agente Predfy** é o **componente que generaliza** o produto. Sem ele, cada nova pergunta de área demandante exigiria código. Com ele, qualquer extrato vira modelo treinado em minutos, no idioma de negócio.

---

*Diagramas mantidos pela Equipe HyperCopa DISEC 2026 — ECOA / CESUP-Contratações.*
