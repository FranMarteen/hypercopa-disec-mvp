"""Interpretador rule-based do relatório H2O — sem LLM, sem rede.

Lê o JSON do relatório (gerado pela Etapa 2) e devolve em PT-BR,
em linguagem de negócio (sem jargão de ML), seguindo a Fase 2 do
`teams_copilot/instructions.md`:

  1. Resumo executivo (≤4 linhas)
  2. Tradução de cada métrica (AUC, RMSE, R², Accuracy, LogLoss)
  3. Top 3 variáveis com leitura de negócio
  4. 3 a 5 recomendações operacionais
  5. Aviso explícito se a métrica for ruim

Usado pelo "Caminho C — Modo demo" da Etapa 5 e pelo "Simulador local
do Agente Teams". Reproduz o comportamento que o Copilot Teams entrega
em produção, mas localmente, sem custo, sem rede e auditável.
"""
from __future__ import annotations

from typing import Any


def _classifica_confianca(metrics: dict, task: str) -> str:
    """Classifica a confiabilidade do modelo em palavras de negócio."""
    if task == "classification":
        auc = float(metrics.get("AUC", 0) or 0)
        if auc >= 0.85:
            return "muito confiável"
        elif auc >= 0.75:
            return "boa confiança"
        elif auc >= 0.65:
            return "confiança moderada"
        elif auc >= 0.55:
            return "baixa confiança"
        else:
            return "modelo não confiável"
    else:
        # regressão
        r2 = float(metrics.get("R2", metrics.get("R²", 0)) or 0)
        if r2 >= 0.85:
            return "muito confiável"
        elif r2 >= 0.70:
            return "boa confiança"
        elif r2 >= 0.50:
            return "confiança moderada"
        elif r2 >= 0.30:
            return "baixa confiança"
        else:
            return "modelo não confiável"


def _metrica_ruim(metrics: dict, task: str) -> bool:
    """Decide se o modelo deve receber alerta explícito de não-uso."""
    if task == "classification":
        auc = float(metrics.get("AUC", 0) or 0)
        acc = float(metrics.get("Accuracy", 0) or 0)
        if auc and auc < 0.65:
            return True
        if acc and acc < 0.55:
            return True
    else:
        r2 = float(metrics.get("R2", metrics.get("R²", 0)) or 0)
        if r2 and r2 < 0.50:
            return True
    return False


def _traduz_metricas(metrics: dict, task: str) -> list[str]:
    """Traduz cada métrica para linguagem de negócio."""
    linhas = []
    if task == "classification":
        if "AUC" in metrics:
            auc = float(metrics["AUC"])
            qual = (
                "discrimina muito bem" if auc >= 0.85 else
                "discrimina bem" if auc >= 0.75 else
                "discrimina razoavelmente" if auc >= 0.65 else
                "discrimina pouco — moeda jogada está em 0.5"
            )
            linhas.append(
                f"- **AUC = {auc:.3f}** — {qual} entre os casos positivos e negativos."
            )
        if "Accuracy" in metrics:
            acc = float(metrics["Accuracy"])
            linhas.append(
                f"- **Accuracy = {acc:.3f}** — acerta **{acc*100:.1f}%** das vezes no conjunto de teste."
            )
        if "LogLoss" in metrics:
            ll = float(metrics["LogLoss"])
            linhas.append(
                f"- **LogLoss = {ll:.3f}** — quanto menor, mais confiantes e corretas as probabilidades. "
                f"Valores < 0,5 indicam previsão sólida; > 0,7 sugere modelo hesitante."
            )
    else:
        if "RMSE" in metrics:
            rmse = float(metrics["RMSE"])
            linhas.append(
                f"- **RMSE = {rmse:.2f}** — erro típico em torno de "
                f"**{rmse:.0f} unidades** do alvo (mesma unidade da variável prevista)."
            )
        if "R2" in metrics or "R²" in metrics:
            r2 = float(metrics.get("R2", metrics.get("R²", 0)))
            linhas.append(
                f"- **R² = {r2:.3f}** — explica **{r2*100:.1f}%** da variação do alvo. "
                f"O resto é ruído ou variável que ficou de fora."
            )
        if "MAE" in metrics:
            mae = float(metrics["MAE"])
            linhas.append(
                f"- **MAE = {mae:.2f}** — erro médio absoluto de "
                f"**{mae:.0f} unidades** (menos sensível a outliers que o RMSE)."
            )
    return linhas


def _ler_top_variaveis(varimp: list[dict], n: int = 3) -> list[dict]:
    """Devolve top N variáveis ordenadas por importância."""
    if not varimp:
        return []
    chaves = ["scaled_importance", "relative_importance", "importance", "value"]
    def chave(row):
        for k in chaves:
            if k in row:
                try:
                    return float(row[k])
                except (TypeError, ValueError):
                    continue
        return 0.0
    ordenado = sorted(varimp, key=chave, reverse=True)
    return ordenado[:n]


def _recomenda(target: str, task: str, metrics: dict,
               top_vars: list[dict]) -> list[str]:
    """Gera 3-5 recomendações operacionais para a área demandante."""
    rec = []

    if task == "classification":
        auc = float(metrics.get("AUC", 0) or 0)
        if auc >= 0.75:
            rec.append(
                "Usar **limiar 0,5** para classificar; priorizar para revisão "
                "do gestor os casos com **probabilidade > 0,7** — concentre "
                "atenção onde o modelo está mais convicto."
            )
        elif auc >= 0.65:
            rec.append(
                "Usar o modelo como **sinal de alerta**, não como decisão. "
                "Priorizar revisão humana em todos os casos com "
                "probabilidade > 0,6."
            )
        else:
            rec.append(
                "⚠️ **Não usar este modelo em produção.** Coletar mais dados "
                "ou rever a definição do target antes de retreinar."
            )
    else:
        r2 = float(metrics.get("R2", metrics.get("R²", 0)) or 0)
        rmse = float(metrics.get("RMSE", 0) or 0)
        if r2 >= 0.70:
            rec.append(
                f"Usar a previsão como **estimativa de planejamento**, "
                f"considerando a margem de erro de ±{rmse:.0f} unidades."
            )
        elif r2 >= 0.50:
            rec.append(
                f"Usar como **referência inicial**, sempre validando com a "
                f"experiência da área. Erro típico de ±{rmse:.0f} unidades — "
                f"não confiar para decisões de alta precisão."
            )
        else:
            rec.append(
                "⚠️ **Não usar para decisão automática.** O modelo explica "
                "menos da metade da variação — coletar mais features ou "
                "redefinir o problema."
            )

    if top_vars:
        nomes = [v.get("variable", v.get("name", "?")) for v in top_vars[:3]]
        rec.append(
            f"Acompanhar mensalmente as variáveis líderes em importância — "
            f"**{nomes[0]}**" + (f", {nomes[1]}" if len(nomes) > 1 else "") +
            (f" e {nomes[2]}" if len(nomes) > 2 else "") +
            ". Se a importância delas cair >50%, é sinal para reentreinar."
        )

    # Recomendação ligada ao target específico (heurística)
    target_lower = target.lower()
    if "atras" in target_lower or "prazo" in target_lower:
        rec.append(
            "Cruzar a saída do modelo com o **calendário de licitações** "
            "para antecipar contratações com risco de estouro de prazo."
        )
    elif "rescis" in target_lower or "ruptu" in target_lower:
        rec.append(
            "Encaminhar contratos com alta probabilidade de ruptura para "
            "**revisão da DIJUR** antes de renovações ou aditivos."
        )
    elif "intercor" in target_lower or "impugn" in target_lower:
        rec.append(
            "Sinalizar processos com alta probabilidade de intercorrência "
            "ao **time jurídico** logo após a abertura do certame, para "
            "preparação de defesa antecipada."
        )
    else:
        rec.append(
            "Validar as previsões com o time de operações da DISEC nos "
            "primeiros 30 dias antes de adotar como apoio à decisão padrão."
        )

    rec.append(
        "Reentreinar o modelo a cada **trimestre fiscal** ou após mudanças "
        "relevantes de política de Licitação Eletrônica (Lei 13.303/16)."
    )

    return rec[:5]


def interpretar_relatorio(relatorio_json: dict[str, Any]) -> dict[str, Any]:
    """Função principal — recebe o JSON do relatório e devolve estrutura
    pronta para renderização no UI do Streamlit (Etapa 5 — modo demo)."""
    target = str(relatorio_json.get("target", "?"))
    task = str(relatorio_json.get("task", "classification"))
    metrics = relatorio_json.get("metrics", {}) or {}
    varimp = relatorio_json.get("varimp", []) or []
    leader_id = str(relatorio_json.get("leader_id", "?"))
    pergunta = str(relatorio_json.get("pergunta", ""))

    confianca = _classifica_confianca(metrics, task)
    metrica_ruim = _metrica_ruim(metrics, task)
    top_vars = _ler_top_variaveis(varimp, n=3)
    metricas_md = _traduz_metricas(metrics, task)
    recomendacoes = _recomenda(target, task, metrics, top_vars)

    # Resumo executivo (≤ 4 linhas)
    if pergunta:
        linha1 = f"O modelo responde: *\"{pergunta}\"*."
    else:
        linha1 = (
            f"O modelo prediz **{target}** "
            f"({'classificação' if task == 'classification' else 'regressão'})."
        )

    if metrica_ruim:
        linha2 = (
            f"⚠️ **Atenção:** as métricas indicam que o modelo **não está "
            f"pronto para uso operacional** — {confianca}. Ver recomendações."
        )
    else:
        linha2 = f"Avaliação geral: **{confianca}**."

    if top_vars:
        nomes_top = ", ".join(
            f"`{v.get('variable', v.get('name', '?'))}`" for v in top_vars
        )
        linha3 = f"Top fatores que pesam na predição: {nomes_top}."
    else:
        linha3 = ""

    linha4 = f"Modelo líder: `{leader_id}`."

    resumo_executivo = "\n\n".join(filter(None, [linha1, linha2, linha3, linha4]))

    # Top variáveis com leitura de negócio
    leitura_top = []
    for i, v in enumerate(top_vars, start=1):
        nome = v.get("variable", v.get("name", "?"))
        imp = float(
            v.get("scaled_importance",
                  v.get("relative_importance",
                        v.get("importance", 0))) or 0
        )
        leitura_top.append(
            f"{i}. **{nome}** — peso relativo {imp:.2f}"
        )

    return {
        "resumo_executivo": resumo_executivo,
        "metricas_traduzidas": metricas_md,
        "top_variaveis": leitura_top,
        "recomendacoes": recomendacoes,
        "confianca_classificacao": confianca,
        "metrica_ruim": metrica_ruim,
        "checkpoint": (
            "Quer que eu detalhe alguma das variáveis acima ou alguma "
            "métrica em específico?"
        ),
    }


def renderizar_markdown(interp: dict[str, Any]) -> str:
    """Converte a saída de `interpretar_relatorio` em um markdown único
    pronto para `st.markdown()` ou para colar em qualquer canal de chat."""
    blocos = []
    blocos.append("### 📋 Resumo executivo\n\n" + interp["resumo_executivo"])
    blocos.append(
        "### 📊 Tradução das métricas\n\n" +
        "\n".join(interp["metricas_traduzidas"])
    )
    if interp["top_variaveis"]:
        blocos.append(
            "### 🧠 Fatores que mais pesam\n\n" +
            "\n".join(interp["top_variaveis"])
        )
    blocos.append(
        "### ✅ Recomendações operacionais\n\n" +
        "\n".join(f"- {r}" for r in interp["recomendacoes"])
    )
    blocos.append("---\n*" + interp["checkpoint"] + "*")
    return "\n\n".join(blocos)
