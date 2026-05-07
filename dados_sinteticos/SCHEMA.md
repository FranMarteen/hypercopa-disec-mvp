# Dicionário de Dados — Universo Sintético HyperCopa DISEC 2026

> Dados sintéticos gerados por código auditável (`gerar_dados_sinteticos_eaps.py`)
> com **seed fixo (42)**. A banca pode regenerar e obter os mesmos arquivos.
>
> Universo modelado: ciclo de vida completo de **Licitação Eletrônica** do
> Banco do Brasil (Lei 14.133/21), incluindo etapas pré-assinatura, contrato
> e ciclo pós-assinatura (aditivos, atrasos, rescisão, penalidades).

---

## Visão geral dos arquivos

| Arquivo | Linhas | Granularidade | Use para |
|---|---:|---|---|
| `eaps.csv` | 2.500 | 1 linha = 1 EAP (Estrutura Analítica de Projeto) | Modelo 1 — **Prazo / atraso geral** |
| `contratos.csv` | 1.959 | 1 linha = 1 contrato pós-assinatura | Modelo 1 — **Atraso de contrato** · Modelo 3 — **Ruptura contratual** |
| `etapas_eap.csv` | 21.884 | 1 linha = 1 etapa de uma EAP | Análises de gargalo por etapa |
| `participantes.csv` | 11.645 | 1 linha = 1 participante por certame | Concentração de fornecedores, lock-in |
| `fornecedores.csv` | 300 | 1 linha = 1 fornecedor | Enriquecimento (porte, especialidade, SICAF) |
| `eaps_padrao.csv` | 47 | 1 linha = 1 etapa de uma EAP Padrão | Referência de prazos padrão |

---

## `eaps.csv` — EAPs (processos de contratação)

| Coluna | Tipo | Descrição |
|---|---|---|
| `eap_id` | string | Identificador único (ex: `EAP-2024-00123`) |
| `eap_padrao` | string | Nome da EAP Padrão (ex: "Contratação de Serviços de TI") |
| `categoria_contratacao` | categórica | `Licitação Eletrônica` · `Contratação Direta` · `Inexigibilidade` |
| `modalidade` | categórica | Modalidade detalhada |
| `tipo_servico` | categórica | TI, Obras, Serviços Gerais, Bens, etc. |
| `objeto_resumido` | string | Descrição livre do objeto |
| `unidade_demandante` | categórica | DICOI, DISUP, DITEC, GECOI, etc. |
| `valor_estimado` | numérico | Valor estimado (R$) |
| `valor_contratado` | numérico | Valor de fato contratado (R$) |
| `dt_abertura` | data | Data de abertura do processo |
| `dt_assinatura` | data | Data de assinatura do contrato |
| `prazo_total_dias` | numérico | **Target Modelo 1 (regressão)** — dias entre abertura e assinatura |
| `num_etapas` | numérico | Quantas etapas a EAP tem |
| `fornecedor_vencedor_id` | string | FK para `fornecedores.csv` |
| `fornecedor_vencedor_nome` | string | Razão social do vencedor |
| `num_participantes` | numérico | Quantos fornecedores participaram |
| `tem_intercorrencia` | boolean | **Target Modelo 2 (classificação)** — houve impugnação ou recurso? |
| `tipo_intercorrencia` | categórica | Tipo da intercorrência (se houve) |
| `status` | categórica | `Concluído` · `Em andamento` · `Cancelado` |
| `urgencia` | categórica | Baixa · Média · Alta |
| `complexidade` | categórica | Simples · Moderada · Complexa |

---

## `contratos.csv` — Contratos pós-assinatura

| Coluna | Tipo | Descrição |
|---|---|---|
| `contrato_id` | string | Identificador único |
| `eap_id` | string | FK para `eaps.csv` |
| `fornecedor_id` | string | FK para `fornecedores.csv` |
| `fornecedor_nome` | string | Razão social |
| `tipo_servico` | categórica | TI, Obras, Serviços Gerais, etc. |
| `categoria_contratacao` | categórica | Idem `eaps.csv` |
| `eap_padrao` | string | Idem `eaps.csv` |
| `valor_contratado` | numérico | R$ |
| `dt_assinatura` | data | Início do contrato |
| `dt_vigencia_fim` | data | Fim previsto |
| `vigencia_meses` | numérico | Duração planejada (meses) |
| `num_aditivos` | numérico | Quantos aditivos foram firmados |
| `aditivos_valor_total` | numérico | Soma dos valores aditivados (R$) |
| `teve_rescisao` | boolean | **Target Modelo 3 (classificação)** — contrato foi rescindido? |
| `motivo_rescisao` | categórica | Motivo, se houve |
| `dt_rescisao` | data | Quando, se houve |
| `num_penalidades` | numérico | Quantas penalidades foram aplicadas |
| `teve_atraso` | boolean | **Target Modelo 1 alternativo (classificação binária)** — houve atraso? |
| `dias_atraso_total` | numérico | Total de dias de atraso |
| `nota_fornecedor` | numérico | 0 a 5 |
| `porte_fornecedor` | categórica | ME / EPP / Médio / Grande |

---

## `etapas_eap.csv` — Etapas de cada EAP

| Coluna | Tipo | Descrição |
|---|---|---|
| `eap_id` | string | FK para `eaps.csv` |
| `eap_padrao` | string | Idem `eaps.csv` |
| `etapa_seq` | numérico | Ordem da etapa na EAP |
| `etapa_nome` | string | Nome da etapa (ex: "Análise de Conformidade") |
| `dt_inicio` | data | Início real da etapa |
| `dt_fim` | data | Fim real |
| `duracao_dias` | numérico | Dias gastos |
| `status_etapa` | categórica | Concluída / Em andamento / Pendente |
| `responsavel` | categórica | Área responsável (Demandante / Jurídico / DISEC / etc.) |

---

## `participantes.csv` — Participantes por certame

| Coluna | Tipo | Descrição |
|---|---|---|
| `eap_id` | string | FK para `eaps.csv` |
| `fornecedor_id` | string | FK para `fornecedores.csv` |
| `valor_proposta` | numérico | Proposta do fornecedor (R$) |
| `classificacao` | numérico | Posição final no certame |
| `vencedor` | boolean | Foi o vencedor? |
| `situacao` | categórica | Habilitado / Inabilitado / Desistente |

---

## `fornecedores.csv` — Base de fornecedores

| Coluna | Tipo | Descrição |
|---|---|---|
| `fornecedor_id` | string | Identificador único |
| `razao_social` | string | Nome (sintético, não real) |
| `cnpj` | string | CNPJ (sintético) |
| `uf` | categórica | Estado |
| `porte` | categórica | ME / EPP / Médio / Grande |
| `especialidade_principal` | categórica | Tipo principal de serviço |
| `especialidades` | string | Lista separada por `;` |
| `nota_desempenho` | numérico | 0 a 5 |
| `num_contratos_ativos` | numérico | Contratos vigentes |
| `situacao_sicaf` | categórica | Regular / Em análise / Irregular |
| `dt_cadastro` | data | Quando entrou no SICAF |

---

## `eaps_padrao.csv` — Referência das EAPs Padrão

| Coluna | Tipo | Descrição |
|---|---|---|
| `eap_padrao` | string | Nome da EAP Padrão |
| `categoria` | categórica | Categoria de contratação |
| `modalidade` | categórica | Modalidade |
| `etapa_seq` | numérico | Ordem da etapa |
| `etapa_nome` | string | Nome da etapa |
| `prazo_padrao_dias` | numérico | Prazo médio esperado |
| `prazo_desvio_dias` | numérico | Desvio padrão |
| `responsavel` | categórica | Área responsável |

---

## Targets dos 3 modelos do MVP

| Modelo | Pergunta de negócio | Tabela | Target | Tipo |
|---|---|---|---|---|
| **1** | Quanto tempo um processo vai durar? | `eaps.csv` | `prazo_total_dias` | Regressão |
| **1' (binária)** | O contrato vai atrasar? | `contratos.csv` | `teve_atraso` | Classificação |
| **2** | Vai ter impugnação ou recurso? | `eaps.csv` | `tem_intercorrencia` | Classificação |
| **3** | Esse contrato corre risco de rescisão? | `contratos.csv` | `teve_rescisao` | Classificação |

---

## Reprodutibilidade

Para regenerar exatamente os mesmos arquivos:

```bash
cd hypercopa-disec-mvp
python gerar_dados_sinteticos_eaps.py
```

A primeira linha do script fixa `SEED = 42` antes de qualquer chamada
aleatória. Em qualquer máquina que rode a versão pinada de NumPy
(ver `requirements_app.txt`), os arquivos sairão idênticos byte-a-byte.
