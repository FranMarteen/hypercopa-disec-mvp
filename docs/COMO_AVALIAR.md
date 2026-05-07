# Como avaliar — Roteiro para a banca HyperCopa DISEC 2026

> Documento dirigido aos avaliadores. Tempo estimado: **5 a 10 minutos**.
>
> A jornada **roda inteira sem chave OpenAI e sem rede externa**. O resultado
> é **idêntico** ao da equipe (seed=42 em todos os pontos de aleatoriedade).

---

## 1. Pré-requisitos

| Item | Versão | Como verificar |
|---|---|---|
| **Python** | 3.10, 3.11 ou 3.12 | `python --version` |
| **Java JDK** | 17 ou 21 | `java -version` (o H2O exige Java) |
| **Memória RAM** | ≥ 4 GB livre | — |
| Espaço em disco | ≥ 1 GB livre | — |

> **Sem Java?** Baixe o [JDK 21 ZIP portátil](https://www.oracle.com/java/technologies/downloads/#jdk21-windows) e descompacte numa pasta. Não precisa instalar como administrador. Adicione `bin\` ao `PATH` da sessão antes de iniciar o app.

---

## 2. Como rodar em 3 minutos

```bash
git clone https://github.com/FranMarteen/hypercopa-disec-mvp.git
cd hypercopa-disec-mvp
python -m venv .venv
.venv\Scripts\activate                    # Windows
# source .venv/bin/activate               # Linux/Mac
pip install -r requirements_app.txt
streamlit run app_agente_bb.py
```

O navegador abre em `http://localhost:8501`. Se não abrir, copie a URL do terminal.

**Próximo passo:** na sidebar, ative o toggle **"🎓 Modo demonstração da banca"**.

---

## 3. Roteiro narrado dos 7 passos

### Etapa 0 — Construção dos dados sintéticos

**O que esperar.** Os CSVs já estão no repositório (`dados_sinteticos/`), gerados com `seed=42`. A banca pode regenerar para reproduzir:

```bash
python gerar_dados_sinteticos_eaps.py
```

Saída esperada (resumida):
```
EAPs:           2.500
Fornecedores:    300
Etapas:        21.884
Contratos:      1.959
Com atraso:       367 (18.7%)
```

**Verificação de reprodutibilidade.** Em qualquer máquina, esses números devem ser **idênticos**.

### Etapa 1 — Agente Predfy (Caminho C, modo demo)

**O que esperar.** Cenário pré-curado: *"EAP DICOI — vai atrasar?"*. CSV pré-carregado: `contratos_dicoi.csv` (1.959 linhas, 21 colunas).

1. Clique em **▶ Próximo turno** repetidamente.
2. Acompanhe os turnos do agente:
   - Turno 1: usuário descreve a pergunta.
   - Turnos 2–3: agente lê schema e amostra (executa as ferramentas reais).
   - Turno 4: agente identifica o target `teve_atraso`.
   - Turnos 5–7: agente propõe 9 features e executa o `pandas` no sandbox.
   - Turno 8: validação (distribuição do target, nulos).
   - Turno 9: salva o CSV final.

Quando a barra de progresso chega a `10/10`, o **CSV final está pronto** e a Etapa 2 desbloqueia automaticamente.

### Etapa 2 — Treino H2O AutoML

**O que esperar.**
1. Slider de tempo de treino: deixe em **60s** (default).
2. Clique em **🚀 Treinar modelo H2O**.
3. Aguarde 60 a 90 segundos. O cluster H2O inicia, faz split 80/20, treina GBM/GLM/XGBoost/RF e avalia.

**Resultado esperado** (com seed=42 e `h2o==3.46.0.6`):
- **Leaderboard** com `GBM_grid_*` no topo.
- **AUC no teste**: ~0.83 a 0.85.
- **LogLoss** ~0.40 a 0.45.

### Etapa 3 — Avaliar o modelo

Logo abaixo do leaderboard:
- **Métricas no teste** (AUC, LogLoss, Accuracy).
- **Importância de variáveis** (top-15) — esperado top-3: `num_aditivos`, `num_penalidades`, `valor_contratado`.
- **Curva ROC** e/ou plot de importância.

### Etapa 4 — Documentos obrigatórios da entrega

**O que esperar.** Botão único **"📦 Baixar pacote completo da entrega"** que gera um ZIP com:

| Arquivo | Conteúdo |
|---|---|
| `relatorio.html` | Relatório visual autocontido (paleta BB) |
| `relatorio.json` | Estrutura para auditoria + Copilot |
| `summary.md` | Resumo executivo de 1 página |
| `como_reproduzir.txt` | Instruções para regerar este resultado |
| `MVP_CANVAS.md` / `.docx` | Canvas do MVP |

> **Anexe esse ZIP à entrega da banca.** Substitui o vídeo regulamentar (que era opcional na entrega 07/05/2026 — vídeo só seria essencial se a ferramenta não fosse testável; aqui ela é).

### Etapa 5 — Interpretar o resultado

Há 3 sub-caminhos:

- **(a) Caminho A** (OpenAI direto) — só funciona se a chave for fornecida pela equipe.
- **(b) Caminho B** (Copilot Teams real) — requer agente publicado no Teams BB.
- **(c) Modo demo** — interpretação rule-based local (sem rede). Lê o JSON do relatório e gera resumo + recomendações.

**O que esperar do caminho (c):**
- Resumo executivo em ≤ 4 linhas.
- Tradução das métricas em PT-BR (AUC ~0.84 = "discrimina bem").
- Top-3 fatores explicados (porte, valor, aditivos).
- 3-5 recomendações operacionais.

### Etapa 6 — Testar em evento real

**O que esperar.**
- Em modo demo: 3 cenários pré-roteirizados como cards clicáveis (EAPs hipotéticas das áreas DICOI, DISUP, DITEC).
- Clicar num cenário pré-preenche o formulário com valores realistas.
- Predição mostrada com **semáforo** (🟢 / 🟡 / 🔴) e probabilidade.
- Botão **"Pedir interpretação"** leva o resultado para a Etapa 5.

---

## 4. Verificação de reprodutibilidade

Confronto rápido para a banca confirmar que vê o mesmo que a equipe:

| Item | Valor esperado |
|---|---|
| Linhas de `contratos.csv` | 1.959 |
| Linhas de `eaps.csv` | 2.500 |
| Distribuição do target `teve_atraso` (0 / 1) | 1.592 / 367 (~81% / ~19%) |
| AUC no teste do modelo demo (60s budget) | 0.82 a 0.85 |
| Modelo líder | algum `GBM_*` da AutoML |
| Top variável (importância 1.0) | `num_aditivos` ou `num_penalidades` |

> Pequenas variações de AUC (±0.005) podem ocorrer entre versões de Java JDK ou builds menores do H2O. As versões dos splits e o leaderboard são determinísticos.

---

## 5. Solução de problemas

| Problema | Causa provável | Solução |
|---|---|---|
| `streamlit: command not found` | venv não ativado | `.venv\Scripts\activate` antes |
| `H2OConnectionError: Java not found` | JDK não instalado | Instale o JDK 17/21 e reabra o terminal |
| `MemoryError` ao iniciar H2O | RAM insuficiente | Feche outros apps; H2O precisa de ~2 GB livre |
| App carrega mas sidebar vazia | Cache antigo do Streamlit | `streamlit cache clear` e reabra |
| Modo demo não pré-carrega CSV | `dados_sinteticos/contratos.csv` ausente | Rode `python gerar_dados_sinteticos_eaps.py` |
| Botões individuais retornam 404 | popup blocker do navegador | Permita downloads para `localhost:8501` |
| Caminho A pede chave | sem `.env` configurado | Use o **Modo demo** ou configure `.env` |

---

## 6. Caminho A real — usando chave OpenAI (opcional)

Se a banca quiser testar com OpenAI real:

1. Receba a chave por canal seguro (a equipe entrega separadamente).
2. Crie o arquivo `.env` na raiz:
   ```
   OPENAI_API_KEY=sk-proj-...
   ```
3. **Desative** o toggle do modo demo na sidebar.
4. Selecione **Caminho A** no radio.
5. O agente fica disponível como chat livre — pergunte qualquer coisa preditiva.

---

## 7. Caminho B real — usando Copilot do Teams (opcional)

Para testar dentro do tenant M365 BB:

1. Veja [`COPILOT_STUDIO_GUIA.md`](COPILOT_STUDIO_GUIA.md) — passo-a-passo de 20-30 min, sem código.
2. Submeta `teams_copilot/declarative-agent.json` ao admin M365.
3. Após aprovação, o agente aparece no Teams como **"Agente Predfy"**.
4. Use-o como interface conversacional; o app local apenas processa o bloco devolvido.

---

## 8. Onde reportar problemas

Abra uma issue no repositório ou contate a equipe pelo canal HyperCopa DISEC 2026.

---

*Bom teste! · Equipe HyperCopa DISEC 2026 · CESUP-Contratações*
