# Screenshots — Predfy

Capturas reais do app rodando em modo demonstração da banca, geradas via Playwright headless. Resolução 2880×1800 (retina-like).

> Para regenerar, rode: `streamlit run app_agente_bb.py --server.port 8503` em
> um terminal e em outro `python capturar_screenshots.py http://localhost:8503`.

---

## 01_header_e_stepper.png
**Header BB + Stepper de 7 etapas (modo demo desligado).**
Tela inicial do Predfy: identidade visual BB (amarelo `#FAE128` + azul `#003DA5`), título "Predfy · Preparador + Modelo Analítico", subtítulo "DISEC · Banco do Brasil · Licitação Eletrônica · Lei 13.303/16", tag "HyperCopa DISEC 2026 · MVP". Stepper horizontal mostrando as 7 etapas (0.Dados → 1.Preparar → 2.Treinar → 3.Avaliar → 4.Documentos → 5.Interpretar → 6.Evento real).

## 02_modo_demo_ativo.png
**Modo demonstração ativado.**
Toggle da sidebar ligado, banner amarelo no topo com a mensagem *"Modo demonstração da banca — sem chave OpenAI, sem chamadas externas. Cenário pré-curado: EAP DICOI / 'vai atrasar?'. Resultado idêntico em qualquer máquina (seed=42)."* CSV pré-carregado: `contratos_dicoi.csv` (1.959 linhas). Caminho C selecionado automaticamente.

## 03_etapa0_dados_sinteticos.png
**Etapa 0 — Universo de dados sintéticos (expander aberto).**
6 métricas em destaque: EAPs 2.500 · Contratos 1.959 · Etapas 21.884 · Participantes 11.645 · Fornecedores 300 · EAPs Padrão 47. Tabs com prévia das 5 primeiras linhas de cada CSV. Texto explicativo: *"Por que sintéticos? Acesso a dados reais BB é inviável no prazo. Geramos um universo realista de Licitação Eletrônica (Lei 13.303/16) por código auditável, com seed fixo (42) — qualquer máquina que rode o gerador obtém os mesmos arquivos byte-a-byte."*

## 04_etapa1_agente_predfy.png
**Etapa 1 — Conversa com o Agente Predfy (Caminho C, modo demo).**
Mostra o cenário: *"EAP DICOI — Quais contratos vão atrasar?"* e a primeira interação do agente. Caixa de instruções do Caminho C explicando que o agente conduz a preparação com turnos pré-gravados executando as ferramentas reais sobre o CSV pré-carregado.

## 05_etapa1_apos_turnos.png
**Etapa 1 concluída — Agente entregou o CSV final.**
Histórico completo dos 10 turnos: agente leu schema, propôs target `teve_atraso`, executou pandas no sandbox, validou (1.959 contratos, 10 colunas, distribuição saudável 81/19), salvou `demo_contratos_final.csv`. Mensagem final: *"Pronto para treinar no H2O AutoML."* — desbloqueia a Etapa 2.

## 06_sidebar.png
**Sidebar (zoom).**
Toggle "Modo demonstração da banca" ligado, bloco verde confirmando "Modo demo ativo. CSV carregado: contratos_dicoi.csv (1.959 linhas)", botão "Reiniciar demo do início", configuração do modelo (desabilitada em modo demo), e seções de upload/caminho local/demo de notebook.

## 07_etapa2_h2o.png
**Continuação da Etapa 1 — antes da rolagem para a Etapa 2 H2O.**
Mostra o estado final do agente preparador antes de o usuário descer para clicar em "Treinar modelo H2O". Em uma sessão real da banca, a Etapa 2 desbloqueia automaticamente após o turno 10 do Caminho C.

## 08_full_page.png
**Página inteira (rolando todo o app).**
Captura completa da viewport — útil para apresentações como single-page poster do produto.

---

## Como usar nos documentos da entrega

- **Apresentação ao vivo (Pitch Day 10/06)**: usar `02` (modo demo) e `05` (turnos completos) para mostrar a jornada sem internet.
- **MVP_CANVAS.docx**: anexar `01` (header) e `02` (modo demo) como prova visual.
- **Relatório técnico**: usar todos os 8 para o capítulo de UX.
- **Banca**: ler antes este `INDEX.md` para orientação.

## Roadmap de capturas adicionais

Backlog de screenshots identificados na auditoria de entrega — recomendados para a próxima rodada de captura (rode `streamlit run app_agente_bb.py --server.port 8504` e estenda `capturar_screenshots.py`):

| Próximo screenshot | Tela | Por que |
|---|---|---|
| `09_etapa4_pacote_zip.png` | Etapa 4 — botão e dialog do download do ZIP | Mostra o entregável único da Etapa 4 |
| `10_etapa6_semaforo.png` | Etapa 6 — 3 cards de cenários com semáforo 🟢🟡🔴 | Materializa o componente "semáforo de risco" da banca |
| `11_relatorio_html.png` | Relatório HTML BB com leaderboard + importância | Comprova saída final do H2O com identidade visual BB |

---

*Screenshots gerados em 07/05/2026 · Equipe HyperCopa DISEC 2026 — ECOA / CESUP-Contratações*
