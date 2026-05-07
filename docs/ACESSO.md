# Como acessar e rodar — Agente Preparador BB

DISEC · Banco do Brasil · HyperCopa DISEC 2026
Time: Equipe HyperCopa DISEC 2026

A solução tem **dois caminhos** que partilham o mesmo app local. Escolha o que preferir.

---

## Caminho A (mais rápido para testar) — chat OpenAI embutido

### Pré-requisitos

| Item | Versão | Como verificar |
|---|---|---|
| Python | ≥ 3.10 | `python --version` |
| Java JDK | 17 ou 21 | `java -version` (necessário para H2O) |
| Chave OpenAI | qualquer | https://platform.openai.com/api-keys |
| Memória RAM | ≥ 4 GB livre | — |

### Instalação (primeira vez)

```bash
git clone https://github.com/FranMarteen/hypercopa-disec-mvp.git
cd hypercopa-disec-2026
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/Mac
pip install -r requirements_app.txt

copy .env.example .env          # Windows
cp .env.example .env            # Linux/Mac
# Edite .env e cole sua chave OpenAI:
# OPENAI_API_KEY=sk-proj-...
```

### Rodar

```bash
streamlit run app_agente_bb.py
```

Abra `http://localhost:8501` e na tela escolha o **Caminho A**.

---

## Caminho B (produção BB) — Copilot do Teams + app local

### Pré-requisitos extras

| Item | Como obter |
|---|---|
| Conta M365 BB | Já tem (e-mail @bb.com.br) |
| Acesso ao Copilot Studio | Solicitar role `Copilot Studio Maker` ao admin M365 |
| Agente publicado no Teams | Ver `docs/COPILOT_STUDIO_GUIA.md` |

### Setup do agente (uma vez por time)

1. Siga **`docs/COPILOT_STUDIO_GUIA.md`** — leva 20-30 min, sem código.
2. O administrador BB aprova a publicação no Teams.
3. Time HyperCopa (Equipe HyperCopa DISEC 2026) e usuários DISEC encontram o agente como **"Preparador BB"** na barra de apps do Teams.

### Rodar (cada usuário, sempre)

1. Abra o agente **Preparador BB** no Microsoft Teams.
2. Clique em um conversation starter (ex: *"Fase 1 — Preparar dados para prever atraso"*) ou comece direto.
3. Anexe o CSV (ou cole uma amostra como tabela markdown).
4. Conte sua pergunta preditiva.
5. Quando o Copilot devolver o **bloco estruturado** (`PERGUNTA / TARGET / TASK / ...`), copie.
6. No app Streamlit local (`streamlit run app_agente_bb.py`):
   - Selecione **Caminho B**.
   - Suba o CSV completo na barra lateral.
   - Cole o bloco no campo de texto.
   - Clique em **✅ Processar bloco e gerar CSV final**.
7. O app gera o CSV final e desbloqueia a **Etapa 2 — Modelo Analítico**.

---

## Etapas comuns (depois da preparação)

Funciona igual nos dois caminhos.

### Etapa 2 — Treinar modelo H2O AutoML

1. Confirme as métricas resumidas (linhas, target, tarefa).
2. Ajuste o **slider de tempo de treino** (default 60s, máximo 300s).
3. Clique em **🚀 Treinar modelo H2O**.
4. Aguarde o spinner finalizar (30s a 5 min dependendo do budget).
5. Veja o **leaderboard top 10**, **métricas no teste** e **importância de variáveis**.
6. Baixe **HTML** (apresentação) ou **JSON** (auditoria/Copilot).

### Etapa 3 — Interpretar no Copilot do Teams (opcional, mas recomendado)

1. Na seção **💬 Etapa 3** do app, clique no ícone **copiar** no canto do bloco.
2. Volte ao Copilot Teams (mesma conversa ou nova).
3. **Cole** e envie.
4. O agente devolve:
   - Resumo executivo em 4 linhas.
   - Tradução das métricas para linguagem de negócio.
   - 3-5 recomendações operacionais.

---

## Roteiro de vídeo de demonstração (1-2 min)

Use OBS Studio ou Loom. Use o **Caminho B** para a demo (mais impressionante para a banca).

| Segundo | Tela | Narração |
|---|---|---|
| 0:00 - 0:10 | Header BB do app | "Agente Preparador BB. Pergunta de negócio vira modelo analítico em 5 minutos, dentro do Copilot do Teams." |
| 0:10 - 0:25 | Teams + agente Preparador | "Abro o agente no Teams, anexo um extrato de contratos da DICOI, pergunto 'quais vão atrasar?'. O Copilot identifica 2.415 linhas, target `teve_atraso`, propõe 12 features." |
| 0:25 - 0:35 | Bloco devolvido no Teams | "O Copilot devolve um bloco estruturado pronto pra colar." |
| 0:35 - 0:50 | App Streamlit Caminho B | "Colo no app local, clico em processar. CSV final gerado em segundos." |
| 0:50 - 1:10 | Etapa 2 + treino H2O | "60 segundos de treino. H2O AutoML rodou GLM, GBM, XGBoost. AUC 0.84 no teste. GBM venceu." |
| 1:10 - 1:25 | Importância de variáveis + relatório HTML | "Top 3 fatores: porte do fornecedor, valor, número de aditivos. Faz total sentido para a área." |
| 1:25 - 1:50 | Volta ao Teams + paste do JSON | "Copio o JSON, volto ao Copilot, peço pra interpretar. Ele me dá resumo executivo, tradução das métricas e 4 recomendações operacionais — tudo em linguagem de negócio." |
| 1:50 - 2:00 | Tela final | "Pronto. CSV bruto → modelo treinado → recomendação de negócio. Sem código, dentro do tenant BB." |

---

## Solução de problemas

| Problema | Causa provável | Solução |
|---|---|---|
| `OPENAI_API_KEY não definida` (Caminho A) | `.env` faltando | Recriar `.env` ou usar Caminho B |
| `H2OConnectionError` | Java não instalado | Instalar JDK 17 e reabrir terminal |
| Bloco do Copilot não processa | Faltam campos obrigatórios | Pedir ao Copilot pra reformatar incluindo `PERGUNTA`, `TARGET`, `TASK`, `PASSO_A_PASSO_PANDAS` |
| Agente não aparece no Teams | Aprovação pendente | Pedir admin M365 BB para aprovar |
| Copilot quer chamar action e dá erro | Connector adicionado por engano | Em Copilot Studio → Actions → remover todos |
| App lento ao subir CSV grande | Limite default 200 MB | Já elevado para 1024 MB em `.streamlit/config.toml` |
| Mensagem do Copilot trunca | Limite Teams 4.000 caracteres | Pedir pra colar amostra menor (top 20 linhas) |

---

## Acesso seguro (rede BB)

> Para uso interno BB, recomenda-se o **Caminho B** (Copilot do Teams):
> - Trafega pelo tenant M365 BB sob acordo corporativo.
> - Auditoria automática via Microsoft Purview.
> - Sem dependência de chave OpenAI individual.
> - Sem custo adicional (incluso na licença Copilot).

> O **Caminho A** é apropriado para:
> - Desenvolvimento local fora da rede BB.
> - Demo para banca quando o agente Copilot ainda não foi aprovado pelo admin.
> - Backup quando o Teams estiver indisponível.

---

## Estrutura do repositório

```
hypercopa-disec-2026/
├── app_agente_bb.py              ← APP LOCAL (Caminho A e B)
├── docs/
│   ├── ACESSO.md                 ← este arquivo
│   ├── FLUXOGRAMA.md             ← diagramas dos dois caminhos
│   ├── COPILOT_STUDIO_GUIA.md    ← passo-a-passo Copilot Studio
│   ├── RELATORIO_SOLUCAO.md      ← documento para banca
│   ├── RELATORIO_SOLUCAO.docx    ← versão Word
│   └── agente/
│       ├── system_prompt.md      ← prompt usado no Caminho A
│       └── tools_schema.json     ← 4 tools OpenAI
├── teams_copilot/
│   ├── README.md                 ← arquitetura Teams
│   ├── instructions.md           ← prompt usado no Caminho B (Copilot Studio)
│   └── declarative-agent.json    ← manifest do agente declarativo
├── dados_sinteticos/             ← dados gerados para MVP
├── dados_postgres/               ← schema + dados sintéticos relacionais
├── dados_treino/                 ← CSVs gerados (gitignored)
├── relatorios/                   ← HTMLs e JSONs gerados (gitignored)
├── requirements_app.txt          ← dependências
├── .env.example                  ← template para chave OpenAI (Caminho A)
└── .gitignore                    ← protege dados reais e segredos
```
