# HyperCopa DISEC 2026 — Agente Preparador BB + H2O AutoML

> **Modelos preditivos sobre Licitação Eletrônica** (Lei 14.133/21) para
> **apoiar decisões e minimizar riscos** em prazos, intercorrências
> (impugnação/recurso), atrasos e ruptura contratual.
>
> ⚖️ **Avaliadores da banca: comece por [`docs/COMO_AVALIAR.md`](docs/COMO_AVALIAR.md).**

---

## O que esse repositório entrega

Uma **jornada de 7 passos** que conduz o usuário do dado bruto à decisão acionável:

```
0. Construção dos dados sintéticos (Faker + regras Lei 14.133, seed=42)
       ↓
1. Agente Preparador (Teams ou local)  ── feature engineering visível,
                                           escolha de target, formulação
                                           da pergunta preditiva
       ↓
2. Treino H2O AutoML  ── compara GBM, GLM, XGBoost, RF; entrega o líder
       ↓
3. Avaliar o modelo  ── leaderboard, métricas no teste, importância
       ↓
4. Baixar pacote da entrega  ── ZIP único: relatório HTML + JSON + summary
       ↓
5. Interpretar resultado  ── agente Teams (simulado ou real) ou OpenAI
                              traduz métricas em recomendações de negócio
       ↓
6. Testar em evento real  ── EAP nova hipotética, predição com semáforo
```

A jornada tem **3 caminhos** para a fase conversacional, escolhidos na sidebar:

| Caminho | LLM | Quando usar |
|---|---|---|
| **A** | OpenAI direto (chat embutido) | Dev local com chave própria |
| **B** | Microsoft Copilot do Teams | Produção BB (acordo M365) |
| **C** | **Modo demonstração offline** | **Avaliação da banca — sem chave OpenAI, sem rede** |

---

## Quickstart para a banca (sem chave OpenAI)

```bash
git clone https://github.com/FranMarteen/hypercopa-disec-mvp.git
cd hypercopa-disec-mvp
python -m venv .venv
.venv\Scripts\activate                    # Windows
# source .venv/bin/activate               # Linux/Mac
pip install -r requirements_app.txt
streamlit run app_agente_bb.py
```

Abra `http://localhost:8501` e na sidebar **ative o toggle "🎓 Modo demonstração da banca"**. A jornada inteira roda sem rede externa, com cenário pré-curado *EAP DICOI / "vai atrasar?"*.

---

## Pré-requisitos

| Item | Versão | Como verificar |
|---|---|---|
| Python | 3.10, 3.11 ou 3.12 | `python --version` |
| Java JDK | 17 ou 21 | `java -version` (o H2O exige Java) |
| Memória RAM | ≥ 4 GB livre | — |

> Se a máquina não tem Java, baixe o [JDK 21 ZIP portátil](https://www.oracle.com/java/technologies/downloads/#jdk21-windows) e descompacte numa pasta — não precisa instalar como administrador.

---

## Reprodutibilidade

A banca clona, instala e **vê os mesmos números** que a equipe.

- `np.random.seed(42)` e `random.seed(42)` em todos os geradores.
- `random_state=42` nos splits treino/teste.
- `H2OAutoML(seed=42)` no AutoML.
- Versões pinadas em `requirements_app.txt` (h2o==3.46.0.6, scikit-learn==1.5.2).
- Dados sintéticos em `dados_sinteticos/` versionados — banca não precisa regerar para reproduzir.

Para confirmar a reprodutibilidade, ver checklist em [`docs/COMO_AVALIAR.md`](docs/COMO_AVALIAR.md).

---

## Estrutura

```
hypercopa-disec-mvp/
├── app_agente_bb.py           ← APP STREAMLIT (entregável principal)
├── requirements_app.txt       ← deps pinadas
├── .env.example               ← template (chave OpenAI opcional)
├── .gitignore                 ← protege segredos e binários
│
├── dados_sinteticos/          ← UNIVERSO DE LICITAÇÃO ELETRÔNICA (sintético)
│   ├── eaps.csv               ← 2.500 EAPs
│   ├── contratos.csv          ← 1.959 contratos pós-assinatura (cenário banca)
│   ├── etapas_eap.csv         ← 21.884 etapas detalhadas
│   ├── participantes.csv      ← 11.645 participantes em certames
│   ├── fornecedores.csv       ← 300 fornecedores
│   ├── eaps_padrao.csv        ← 47 etapas-padrão por categoria
│   └── SCHEMA.md              ← dicionário de dados em PT-BR
│
├── gerar_dados_sinteticos_eaps.py  ← regenera os CSVs (seed=42)
├── gerar_dados_postgres.py         ← versão relacional com UUIDs
│
├── modelos_preditivos.py      ← 3 modelos do MVP (Prazo · Intercorrência · Ruptura)
├── modelos_mvp_base.py        ← código de referência da modelagem
├── analise_clusters.py        ← análise K-Means de recorrência (protótipo)
│
├── notebook_h2o_agente_mvp.ipynb   ← jornada como notebook (alternativa CLI)
├── demo_jornada.py            ← jornada via CLI sem UI
│
├── docs/
│   ├── COMO_AVALIAR.md        ← ⭐ ROTEIRO PARA A BANCA
│   ├── MVP_CANVAS.md / .docx  ← MVP Canvas (template HyperCopa)
│   ├── ENTREGA_TIME1_MODELOS.md / .docx   ← entrega comparativa Time 1
│   ├── ENTREGA_TIME2_AGENTE.md / .docx    ← entrega comparativa Time 2
│   ├── RELATORIO_SOLUCAO.md / .docx       ← documento técnico estendido
│   ├── FLUXOGRAMA.md          ← diagramas Mermaid dos caminhos
│   ├── ACESSO.md              ← pré-requisitos e instalação detalhados
│   ├── COPILOT_STUDIO_GUIA.md ← passo-a-passo para publicar agente no Teams
│   ├── agente/                ← system prompt + tools schema (Caminho A)
│   └── demo/
│       └── script_turnos.json ← turnos pré-gravados do Modo Demo (Caminho C)
│
├── teams_copilot/
│   ├── instructions.md        ← system prompt do Copilot Studio (Caminho B)
│   ├── declarative-agent.json ← manifest do agente declarativo
│   └── actions_openapi.yaml   ← OpenAPI das actions
│
├── api/main.py                ← API REST (FastAPI) para evolução futura
└── relatorios/                ← saídas geradas (gitignored)
```

---

## Modos de uso

### 1. Modo demonstração (Caminho C) — **recomendado para a banca**

Sem chave OpenAI, sem rede externa, resultado idêntico a qualquer máquina.

1. Ative o toggle **"🎓 Modo demonstração da banca"** na sidebar.
2. CSV pré-carregado: `contratos_dicoi.csv` (1.959 contratos).
3. Avance turnos do agente com **▶ Próximo turno** até gerar o CSV final.
4. Treine na Etapa 2 (budget 60s).
5. Baixe o **pacote completo da entrega** (Etapa 4).

### 2. Caminho A — OpenAI direto (chave própria)

Cole sua chave em `.env` (use `.env.example` como template) e inicie o app. O modo demo deve estar desligado.

### 3. Caminho B — Copilot do Teams

Para uso em produção BB. Veja [`docs/COPILOT_STUDIO_GUIA.md`](docs/COPILOT_STUDIO_GUIA.md) para publicar o agente no tenant M365.

---

## Privacidade e segurança

- **Dados sintéticos** — nenhum dado real BB neste repositório.
- **Chave OpenAI** — fica em `.env` local (gitignored), não viaja com o código.
- **Caminho A**: somente schema + ≤ 20 linhas de amostra trafegam para OpenAI.
- **Caminho B**: CSV completo nunca sai do laptop; apenas amostra trafega no tenant M365 BB.
- **Sandbox de execução**: `exec()` com globals restritos, sem `os`, `subprocess`, rede.

---

## Os 3 modelos preditivos do MVP

| # | Modelo | Tipo | Target | Pergunta de negócio |
|---|---|---|---|---|
| 1 | **Prazo / Atraso** | Regressão GBM | `prazo_total_dias` (eaps) ou `teve_atraso` (contratos) | "Quanto tempo / vai atrasar?" |
| 2 | **Intercorrência** | Classif. binária GBM | `tem_intercorrencia` | "Vai ter impugnação/recurso?" |
| 3 | **Ruptura contratual** | Classif. binária GBM | `teve_rescisao` | "Risco de rescisão?" |

O cenário canônico do **modo demonstração** usa o **Modelo 1 binário** (`teve_atraso`).

---

## Licença e uso

Propriedade do Banco do Brasil. Repositório de uso interno da equipe HyperCopa DISEC 2026, **publicado para fins de avaliação da banca HyperCopa**. Após o Pitch Day (10/06/2026), pode ser convertido para privado.

---

*Equipe HyperCopa DISEC 2026 · CESUP-Contratações · Banco do Brasil*
