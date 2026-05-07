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

## Segurança e privacidade — leia antes de clonar

Este repositório foi **revisado e anonimizado** para distribuição pública à banca avaliadora. **Nenhum dado real do Banco do Brasil ou pessoal está incluído.**

| O que NÃO está no repo | O que ESTÁ no repo |
|---|---|
| ❌ Dados reais de Licitação Eletrônica BB | ✅ Dados 100% sintéticos gerados por código (Faker + regras Lei 14.133) |
| ❌ CPFs, CNPJs, valores nominais reais | ✅ Identificadores e CNPJs gerados artificialmente |
| ❌ Nomes completos da equipe | ✅ Apenas papéis ("Capitão da Equipe") e codinomes |
| ❌ Chaves OpenAI ou de qualquer API | ✅ Apenas `.env.example` (template vazio) |
| ❌ Logs de produção, dumps de banco, screenshots de sistemas BB | ✅ Apenas saídas geradas localmente pela jornada da demo |
| ❌ Documentos com classificação interna BB | ✅ Apenas o MVP Canvas e relatórios gerados pelo MVP |

**Outras camadas de proteção embutidas:**
- `.gitignore` bloqueia `.env`, `dados reais/`, `dados_reais_limpos/`, PDFs, modelos H2O salvos e relatórios gerados.
- **Sandbox de execução**: o agente roda código `pandas` em `exec()` com globals restritos — sem `os`, `subprocess`, rede, abertura de arquivos.
- **Caminho A** (OpenAI): apenas schema + ≤ 20 linhas de amostra trafegam para o LLM. CSV inteiro nunca sai do laptop.
- **Caminho B** (Copilot Teams): em produção BB, trafega no tenant M365 sob acordo Microsoft↔BB com auditoria Microsoft Purview.
- **Caminho C** (Modo demo): zero chamadas externas — todas as respostas do agente são pré-gravadas e versionadas em `docs/demo/script_turnos.json`.

**Após o Pitch Day (10/06/2026)**, este repositório pode ser convertido para privado sem prejuízo para os avaliadores que já testaram.

---

## Pré-requisitos

| Item | Versão | Como verificar |
|---|---|---|
| **Python** | 3.10, 3.11 ou 3.12 (3.13/3.14 podem precisar afrouxar pins do `requirements_app.txt`) | `python --version` |
| **Java JDK** | 17 ou 21 (o H2O exige Java; sem isso o treino não inicia) | `java -version` |
| **Memória RAM** | ≥ 4 GB livre | — |
| **Espaço em disco** | ≥ 2 GB livres (h2o + venv) | — |

> Se a máquina não tem Java, baixe o [JDK 21 ZIP portátil](https://www.oracle.com/java/technologies/downloads/#jdk21-windows) e descompacte numa pasta — não precisa instalar como administrador. Adicione `bin\` ao `PATH` da sessão antes de iniciar o app.

---

## Quickstart — sem chave OpenAI (Modo demonstração da banca)

A jornada inteira roda offline, com cenário pré-curado *"EAP DICOI / vai atrasar?"* e **resultado idêntico em qualquer máquina** (seed=42).

### Windows (PowerShell)

Cole **uma linha por vez** (não cole o bloco inteiro — quebras de linha podem fragmentar URLs):

```powershell
git clone https://github.com/FranMarteen/hypercopa-disec-mvp.git
```

```powershell
cd hypercopa-disec-mvp
```

```powershell
python -m venv .venv
```

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
```

```powershell
.\.venv\Scripts\Activate.ps1
```

> Esperado: o prompt vira `(.venv) PS C:\...\hypercopa-disec-mvp>`. Se não aparecer `(.venv)`, o venv não ativou.

```powershell
python -m pip install --upgrade pip
```

```powershell
pip install -r requirements_app.txt
```

> Demora 3-7 minutos (o H2O tem ~250 MB).

```powershell
streamlit run app_agente_bb.py
```

> Abre `http://localhost:8501` no navegador. Na sidebar, ative o toggle **🎓 Modo demonstração da banca** e siga a jornada de 7 etapas.

Para encerrar: `Ctrl+C` no PowerShell. Para sair do venv depois: `deactivate`.

### Linux / macOS (bash)

```bash
git clone https://github.com/FranMarteen/hypercopa-disec-mvp.git
cd hypercopa-disec-mvp
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements_app.txt
streamlit run app_agente_bb.py
```

### Solução para erros comuns

| Erro | Solução |
|---|---|
| `Activate.ps1 cannot be loaded — execution policies` | Rode `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force` antes |
| `Could not find a version that satisfies h2o==3.46.0.6` (em Python 3.13/3.14) | Edite `requirements_app.txt` e troque `==` por `~=` no `h2o` e `scikit-learn`, ou use Python 3.10–3.12 |
| `H2OConnectionError: Java not found` | Instale o JDK 17 ou 21 e reabra o terminal |
| `MemoryError` ao iniciar H2O | Feche outros apps; H2O precisa de ~2 GB livres |
| App carrega mas modo demo não pré-carrega CSV | Garanta que `dados_sinteticos/contratos.csv` existe (ele vem versionado no repo) |

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
