# Agente Preparador + Interprete BB — Microsoft Copilot no Teams

Versao **sem API** (copy-paste). O agente roda 100% conversacional dentro do Microsoft Copilot, sem precisar de servidor, tunel ou autenticacao OAuth.

## Como funciona (visao geral)

```
┌────────────────────┐                    ┌────────────────────────┐
│  Microsoft Copilot │                    │  App Streamlit local   │
│  no Teams (nuvem   │  <- copy-paste ->  │  (treino H2O AutoML +  │
│  Microsoft 365 BB) │                    │   relatorio HTML/JSON) │
└────────────────────┘                    └────────────────────────┘
```

**Fase 1 — Preparador (Teams)**
1. Usuario abre o agente no Teams.
2. Anexa o CSV (ou cola amostra como tabela).
3. Conta a pergunta preditiva em PT-BR.
4. O Copilot devolve um **bloco estruturado** com `PERGUNTA / TARGET / TASK / FEATURES / FILTRO / JOINS / PASSO_A_PASSO_PANDAS`.

**App Streamlit local**
5. Usuario cola o bloco no app `app_agente_bb.py` (campo "Bloco do Copilot").
6. Confirma e treina o modelo H2O AutoML.
7. App gera `relatorios/relatorio_<ts>.html` + `relatorios/relatorio_<ts>.json`.

**Fase 2 — Interprete (Teams)**
8. Usuario clica no app em **Copiar JSON do relatorio**.
9. Cola no Copilot do Teams pedindo *"interpreta esse relatorio"*.
10. O Copilot devolve resumo executivo, traducao das metricas e recomendacoes operacionais.

## Arquivos

- `instructions.md` — system prompt completo do agente (duas fases, regras, exemplos).
- `declarative-agent.json` — manifest do Microsoft 365 Agent (sem actions, so instructions + conversation_starters).
- `actions_openapi.yaml` — **NAO USADO** nesta versao. Mantido como referencia para evolucao futura caso o BB queira automacao via API.

## Como publicar no tenant BB

### Opcao A — Microsoft 365 Agents Toolkit (VS Code)
1. Instale a extensao **Microsoft 365 Agents Toolkit** no VS Code.
2. `Create New Project` -> `Declarative Agent`.
3. Substitua o `declarative-agent.json` e `instructions.md` do template pelos deste diretorio.
4. **Remova** referencias a `actions_openapi.yaml` no manifesto (ja removido nesta versao).
5. `F5` para testar no Copilot playground.
6. `Zip project and upload` -> publicar via Teams Admin Center BB.

### Opcao B — Copilot Studio (no-code)
1. Acesse `https://copilotstudio.microsoft.com` com sua conta BB M365.
2. Create -> Copilot agent (declarative).
3. Cole `instructions.md` em **System prompt**.
4. Copie os 4 itens de `conversation_starters` em **Conversation starters**.
5. **Nao adicione actions/connectors.** O fluxo e copy-paste apenas.
6. Test -> Publish -> Teams channel.

## Privacidade e governanca

- **Onde os dados vao**: o usuario cola **amostras** (top 5-20 linhas) ou anexa o CSV no chat. O conteudo trafega pela infra do Microsoft 365 BB, sob acordo corporativo Microsoft <-> BB. **Nao ha exposicao a OpenAI publica**.
- **Sem persistencia externa**: o Copilot nao salva o CSV em lugar nenhum alem do thread do Teams (politica padrao M365).
- **Modelo treinado fica local**: o H2O AutoML roda no laptop/VDI do usuario via Streamlit. O modelo nao sai da maquina.
- **Auditabilidade**: o Microsoft Purview do tenant BB ja registra todas as conversas com Copilot — auditavel sem instrumentacao adicional.
- **Recomendacao**: o usuario deve **mascarar dados sensiveis** (CPF, CNPJ real, valores nominais de licitacao em andamento) antes de colar.

## Limitacoes desta versao

- Sem execucao real: o Copilot **nao roda** o codigo pandas que ele mesmo gera. O usuario cola no Streamlit para executar.
- Sem leitura direta do relatorio HTML: o usuario precisa colar o **JSON** do relatorio (botao no Streamlit), o HTML e so para arquivamento humano.
- Sem persistencia entre sessoes: cada conversa comeca do zero. O usuario precisa recolar o CSV ou o JSON em cada sessao nova.

## Evolucao futura (opcional)

Se a DISEC quiser automacao plena, o `actions_openapi.yaml` ja existente pode ser ativado:
- Subir a FastAPI (`api/main.py`) em ambiente BB com Azure AD.
- Adicionar a referencia em `declarative-agent.json` -> `actions`.
- Atualizar URL em `actions_openapi.yaml` -> `servers`.

Mas para o **MVP HyperCopa DISEC 2026** o caminho copy-paste e suficiente.
