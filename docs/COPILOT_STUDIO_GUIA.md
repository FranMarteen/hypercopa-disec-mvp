# Como criar o agente no Microsoft Copilot Studio

Guia passo-a-passo para o Time HyperCopa (Equipe HyperCopa DISEC 2026) publicar o agente **Agente Predfy** no Copilot do Teams, sem API e sem código.

> Estimativa de tempo: 20-30 minutos.

---

## Pré-requisitos

| Item | Detalhe |
|---|---|
| Conta M365 | Conta corporativa BB com permissão para criar agentes Copilot Studio |
| Acesso | https://copilotstudio.microsoft.com (login com a conta BB) |
| Licença | Copilot Studio incluso na licença M365 Copilot do tenant BB |
| Navegador | Edge ou Chrome atualizado |

> Se não tiver acesso, peça ao administrador M365 BB para liberar o role **"Copilot Studio Author"** no seu usuário.

---

## Passo 1 — Criar o agente

1. Acesse **https://copilotstudio.microsoft.com**.
2. No canto superior direito, confirme que está **logado com a conta BB** (e-mail @bb.com.br).
3. Clique em **`+ Create`** (canto superior esquerdo).
4. Escolha **`New agent`** → **`Skip to configure`** (pula o assistente).

---

## Passo 2 — Configurar identidade do agente

Na aba **`Overview`** preencha:

| Campo | Valor |
|---|---|
| **Name** | `Agente Predfy` |
| **Description** | `Agente da DISEC para preparar dados de Licitacao Eletronica (Fase 1) e interpretar relatorios de modelos H2O (Fase 2). Sem chamadas externas — totalmente conversacional via copy-paste.` |
| **Icon** | (opcional) Faça upload de um icone amarelo/azul BB |

---

## Passo 3 — Colar o system prompt

1. Vá para a aba **`Instructions`** (ou **`Configure`** → **`Instructions`**).
2. Abra o arquivo `teams_copilot/instructions.md` deste repositório.
3. **Selecione tudo** (Ctrl+A) e **copie** (Ctrl+C).
4. **Cole** no campo de instruções do Copilot Studio (Ctrl+V).
5. Clique em **`Save`**.

> 📌 O system prompt já tem as duas fases (preparador + interprete) e exemplos few-shot prontos. Não precisa adaptar.

---

## Passo 4 — Adicionar conversation starters

Na aba **`Configure`** → **`Suggested prompts`**, adicione **4 prompts**:

| Título | Texto |
|---|---|
| Fase 1 — Preparar dados para prever atraso | `Recebi um extrato de contratos da DICOI e quero prever quais vao atrasar. Vou colar a amostra do CSV — me ajuda a preparar?` |
| Fase 1 — Preparar dados para risco de ruptura | `Tenho dados de fornecedores e contratos e quero prever risco de ruptura contratual. Como monto o CSV de treino?` |
| Fase 1 — Combinar multiplos extratos | `Tenho 3 CSVs (contratos, fornecedores, EAPs). Preciso juntar tudo num unico arquivo. Por onde comecar?` |
| Fase 2 — Interpretar relatorio do modelo | `Treinei o modelo no Streamlit e tenho o JSON do relatorio. Vou colar — me explica o resultado em linguagem de negocio.` |

> Esses prompts aparecem como botões na primeira mensagem do usuário, ajudando a iniciar a conversa.

---

## Passo 5 — Configurações de comportamento (importante)

Na aba **`Settings`** → **`Generative AI`**:

| Opção | Configuração |
|---|---|
| **Knowledge** | `Disabled` (não vamos usar fontes de conhecimento extras) |
| **Web search** | `Enabled` (útil para o agente consultar a Lei 13.303/16) |
| **Code interpreter** | `Disabled` (a execução fica no Streamlit local, NÃO no Copilot) |
| **Image generation** | `Disabled` |
| **Actions / Connectors** | **NENHUMA** — fluxo é puramente conversacional |

> ⚠️ **Não adicione actions/connectors.** Esta versão é copy-paste pura. Se adicionar uma action sem o backend correspondente, o agente vai tentar chamar e falhar.

---

## Passo 6 — Ajustes de governança BB

Na aba **`Settings`** → **`Security & compliance`**:

- ☑️ **`Authentication`** → `Microsoft Entra ID (Azure AD) — single tenant BB`
- ☑️ **`Audit logging`** → `Enabled` (já é padrão; confirma que aparece no Microsoft Purview)
- ☑️ **`DLP (Data Loss Prevention)`** → manter as policies padrão BB
- ☐ **`Anonymous access`** → **DESABILITADO**

---

## Passo 7 — Testar no playground

1. Aba **`Test`** (canto direito).
2. No primeiro turno, clique no conversation starter **"Fase 1 — Preparar dados para prever atraso"**.
3. Cole uma amostra de CSV (use por exemplo as primeiras 5 linhas de `dados_sinteticos/contratos.csv`).
4. Verifique:
   - O agente identifica colunas e linhas.
   - Identifica o target.
   - Propõe a preparação em até 5 bullets.
   - Quando você diz "ok", devolve o **bloco estruturado** com `PERGUNTA / TARGET / TASK / ...`.
5. Em uma nova conversa, teste a Fase 2: cole um JSON exemplo (use `relatorios/relatorio_*.json` gerado pelo Streamlit — ou um JSON de teste) e veja se o agente devolve resumo + tradução de métricas + recomendações.

---

## Passo 8 — Publicar para o Teams

1. Aba **`Channels`** → **`Microsoft Teams`**.
2. Clique em **`Turn on Teams`**.
3. Defina:
   - **App name** (Teams): `Agente Predfy`
   - **Short description**: `Agente DISEC para Licitacao Eletronica`
   - **Long description**: copie a Description do Passo 2.
4. Clique em **`Submit for admin approval`**.

> O administrador M365 BB recebe a solicitação no **Teams Admin Center**. Após aprovação, o agente fica disponível para **todos os usuários** (ou para um grupo específico, conforme política BB) na barra de apps do Teams.

### Atalho para o time durante o desenvolvimento

Antes da aprovação completa, o time HyperCopa (Equipe HyperCopa DISEC 2026) pode adicionar o agente como **"Personal app"** via **`Test in Teams`** (botão no canto superior direito do Copilot Studio) — abre o Teams com o agente já carregado para você.

---

## Passo 9 — Monitorar uso

Após publicado:
- **Copilot Studio → Analytics**: número de conversas, taxa de retenção, mensagens médias por conversa.
- **Microsoft Purview**: auditoria das mensagens trafegadas (todo conteúdo colado fica retido conforme política BB).

---

## Solução de problemas

| Problema | Causa | Solução |
|---|---|---|
| Agente devolve respostas em inglês | Locale errado | Em `Settings` → `Languages`, defina `Portuguese (Brazil)` como primário |
| Agente não detecta a Fase 2 | Usuário colou texto livre, não JSON | Reforce no system prompt o reconhecimento de `{leader_id`, `metrics`, `varimp` |
| Agente quer chamar action e dá erro | Alguém adicionou um connector | `Settings` → `Actions` → remover todos |
| "Submit for admin approval" não aparece | Sua conta não tem permissão | Pedir ao admin M365 BB para promover ao role `Copilot Studio Maker` |
| Mensagens longas truncam | Limite de 4.000 caracteres em mensagens do Teams | Peça ao usuário para colar amostras menores (top 20 linhas) ou anexar arquivo |

---

## Iterar e atualizar

Para atualizar o system prompt:
1. Edite `teams_copilot/instructions.md` no repositório.
2. Commit + push para o GitHub.
3. No Copilot Studio, abra `Instructions`, **substitua todo o conteúdo** pela nova versão.
4. Salve e teste no playground.
5. Republique no Teams (sem precisar de nova aprovação se for só mudança de prompt).

> 💡 **Boa prática**: tag cada versão do prompt no git (`git tag prompt-v1.1`) para conseguir reverter caso uma mudança piore o comportamento.

---

## Evolução futura — ativar actions

Quando o time decidir automatizar (Fase 3+), pode-se ativar `actions_openapi.yaml`:

1. Subir a FastAPI (`api/main.py`) em ambiente BB com Azure AD.
2. No Copilot Studio: **`Actions`** → **`+ Add action`** → **`OpenAPI specification`**.
3. Cole a URL da API (ex: `https://api-disec.bb.com.br/openapi.yaml`).
4. Configure autenticação (Azure AD on-behalf-of).
5. Republique no Teams.

A partir daí, o Copilot pode chamar diretamente a API e dispensar o copy-paste — mas é trabalho adicional que **não é necessário para o MVP HyperCopa**.

---

*Mantido pelo time HyperCopa DISEC 2026 — Equipe HyperCopa DISEC 2026.*
