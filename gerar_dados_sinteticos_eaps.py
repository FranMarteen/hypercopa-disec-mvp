"""
============================================================================
HyperCopa DISEC 2026 - Gerador de Dados Sintéticos
CESUP-Contratações | Banco do Brasil
============================================================================

Este script gera dados sintéticos realistas que simulam o ciclo de vida
das EAPs (Estruturas Analíticas de Processos) de contratação no
Banco do Brasil, estruturados por EAP Padrão.

Cada tipo de contratação possui uma EAP Padrão com etapas e prazos
específicos: licitações (fluxo completo), contratações diretas e
inexigibilidades (fluxo reduzido). Toda licitação é eletrônica.

Datasets gerados:
  1. eaps.csv           - Processos de contratação (dataset principal)
  2. fornecedores.csv   - Base de fornecedores
  3. etapas_eap.csv     - Etapas detalhadas de cada EAP
  4. participantes.csv  - Participantes dos certames
  5. eaps_padrao.csv    - Referência das EAPs padrão e suas etapas

Uso:
  python gerar_dados_sinteticos_eaps.py

Os arquivos são salvos na pasta ./dados_sinteticos/
============================================================================
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

SEED = 42
NUM_EAPS = 2500
NUM_FORNECEDORES = 300
DATA_INICIO = datetime(2022, 1, 1)
DATA_FIM = datetime(2025, 12, 31)
OUTPUT_DIR = "./dados_sinteticos"

random.seed(SEED)
np.random.seed(SEED)

# ============================================================================
# DOMÍNIOS DE NEGÓCIO - EAPs PADRÃO DO BB
# ============================================================================

# Cada EAP Padrão define:
#   - categoria: Licitação / Contratação Direta / Inexigibilidade
#   - modalidade: derivada (toda licitação é eletrônica)
#   - peso: probabilidade de ocorrência
#   - etapas: lista de (nome_etapa, prazo_media_dias, prazo_std_dias, responsavel)

EAPS_PADRAO = {
    "Contratação de Serviços": {
        "categoria": "Licitação",
        "modalidade": "Licitação Eletrônica",
        "peso": 0.35,
        "etapas": [
            ("Análise da Demanda",                   15, 5, "Equipe Técnica"),
            ("Complementação de Informações",        10, 4, "Equipe Técnica"),
            ("Elaboração do Edital",                 25, 8, "Equipe Técnica"),
            ("Publicação do Edital",                  3, 1, "Pregoeiro"),
            ("Prazo de Elaboração das Propostas",    15, 5, "Externo"),
            ("Sessão de Disputa",                     1, 0, "Pregoeiro"),
            ("Habilitação",                          10, 4, "Pregoeiro"),
            ("Declaração de Vencedor",                3, 1, "Pregoeiro"),
            ("Convocação para Assinatura",            8, 3, "Gestor do Contrato"),
            ("Assinatura do Contrato",                5, 2, "Ordenador"),
        ],
    },
    "ARP Engenharia": {
        "categoria": "Licitação",
        "modalidade": "Licitação Eletrônica",
        "peso": 0.15,
        "etapas": [
            ("Análise da Demanda",                   20, 7, "Equipe Técnica"),
            ("Complementação de Informações",        12, 5, "Equipe Técnica"),
            ("Elaboração do Edital",                 35, 10, "Equipe Técnica"),
            ("Publicação do Edital",                  3, 1, "Pregoeiro"),
            ("Prazo de Elaboração das Propostas",    20, 7, "Externo"),
            ("Sessão de Disputa",                     1, 0, "Pregoeiro"),
            ("Habilitação",                          12, 5, "Pregoeiro"),
            ("Declaração de Vencedor",                5, 2, "Pregoeiro"),
            ("Convocação para Assinatura",           10, 4, "Gestor do Contrato"),
            ("Assinatura do Contrato",                7, 3, "Ordenador"),
        ],
    },
    "ARP Bens": {
        "categoria": "Licitação",
        "modalidade": "Licitação Eletrônica",
        "peso": 0.20,
        "etapas": [
            ("Análise da Demanda",                   12, 4, "Equipe Técnica"),
            ("Complementação de Informações",         8, 3, "Equipe Técnica"),
            ("Elaboração do Edital",                 20, 6, "Equipe Técnica"),
            ("Publicação do Edital",                  3, 1, "Pregoeiro"),
            ("Prazo de Elaboração das Propostas",    12, 4, "Externo"),
            ("Sessão de Disputa",                     1, 0, "Pregoeiro"),
            ("Habilitação",                           8, 3, "Pregoeiro"),
            ("Declaração de Vencedor",                3, 1, "Pregoeiro"),
            ("Convocação para Assinatura",            7, 3, "Gestor do Contrato"),
            ("Assinatura do Contrato",                5, 2, "Ordenador"),
        ],
    },
    "Contratação Direta por Limite de Valor": {
        "categoria": "Contratação Direta",
        "modalidade": "Contratação Direta",
        "peso": 0.15,
        "etapas": [
            ("Análise de Conformidade",              10, 4, "Equipe Técnica"),
            ("Complementação de Informações",         5, 2, "Equipe Técnica"),
            ("Verificação de Documentação",           5, 2, "Equipe Técnica"),
            ("Ratificação/Aprovação",                 3, 1, "Ordenador"),
            ("Convocação para Assinatura",            5, 2, "Gestor do Contrato"),
            ("Assinatura do Contrato",                3, 1, "Ordenador"),
        ],
    },
    "Contratação Direta Exceto Limite de Valor": {
        "categoria": "Contratação Direta",
        "modalidade": "Contratação Direta",
        "peso": 0.10,
        "etapas": [
            ("Análise de Conformidade",              12, 5, "Equipe Técnica"),
            ("Complementação de Informações",         7, 3, "Equipe Técnica"),
            ("Verificação de Documentação",           7, 3, "Equipe Técnica"),
            ("Ratificação/Aprovação",                 5, 2, "Ordenador"),
            ("Convocação para Assinatura",            5, 2, "Gestor do Contrato"),
            ("Assinatura do Contrato",                3, 1, "Ordenador"),
        ],
    },
    "Inexigibilidade": {
        "categoria": "Inexigibilidade",
        "modalidade": "Inexigibilidade",
        "peso": 0.05,
        "etapas": [
            ("Análise de Conformidade",              10, 4, "Equipe Técnica"),
            ("Justificativa de Inexigibilidade",      7, 3, "Equipe Técnica"),
            ("Ratificação",                           5, 2, "Ordenador"),
            ("Convocação para Assinatura",            5, 2, "Gestor do Contrato"),
            ("Assinatura do Contrato",                3, 1, "Ordenador"),
        ],
    },
}

TIPOS_SERVICO = {
    "TI - Infraestrutura":           0.15,
    "TI - Desenvolvimento":          0.12,
    "TI - Licenciamento":            0.08,
    "Engenharia - Obras":            0.10,
    "Engenharia - Manutenção":       0.08,
    "Facilities - Limpeza":          0.07,
    "Facilities - Vigilância":       0.06,
    "Facilities - Recepção":         0.03,
    "Logística - Transporte":        0.05,
    "Logística - Armazenagem":       0.03,
    "Segurança Patrimonial":         0.05,
    "Consultoria - Gestão":          0.04,
    "Consultoria - Jurídica":        0.03,
    "Marketing e Comunicação":       0.04,
    "Treinamento e Capacitação":     0.03,
    "Seguros":                       0.02,
    "Material de Escritório":        0.02,
}

UNIDADES_DEMANDANTES = [
    "DITEC", "DILOG", "DIMAC", "DIREO", "DIRES", "DIFIN",
    "DICOM", "DIJUR", "DIPES", "DIRIS", "DISEC", "DIOPE",
    "DIGER", "DICRE", "DIMAP", "SUREF-SP", "SUREF-RJ",
    "SUREF-MG", "SUREF-RS", "SUREF-PR", "SUREF-BA",
    "SUREF-DF", "SUREF-PE", "SUREF-CE", "CENOP-SP",
    "CENOP-RJ", "CENOP-DF", "CENOP-RECIFE",
]

# Intercorrências aplicáveis por categoria
INTERCORRENCIAS_LICITACAO = [
    "Impugnação ao Edital",
    "Recurso Administrativo",
    "Certame Deserto",
    "Certame Fracassado",
    "Suspensão Judicial",
    "Revisão de Edital",
    "Diligência TCU",
    "Questionamento de Preço",
    "Inabilitação de Licitante",
    "Pedido de Esclarecimento",
]

INTERCORRENCIAS_DIRETA = [
    "Complementação de Documentação",
    "Questionamento de Preço",
    "Diligência TCU",
    "Revisão de Justificativa",
]

INTERCORRENCIAS_INEXIGIBILIDADE = [
    "Complementação de Justificativa",
    "Questionamento de Preço",
    "Diligência TCU",
]

STATUS_EAP = {
    "Concluído":     0.80,
    "Em Andamento":  0.12,
    "Cancelado":     0.05,
    "Suspenso":      0.03,
}

UFS = [
    "SP", "RJ", "MG", "RS", "PR", "BA", "DF", "PE", "CE",
    "SC", "GO", "PA", "MA", "AM", "ES", "PB", "RN", "AL",
    "PI", "SE", "MT", "MS", "RO", "TO", "AC", "AP", "RR",
]

PORTES = {
    "ME":      0.25,
    "EPP":     0.30,
    "Médio":   0.25,
    "Grande":  0.20,
}

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def escolher_ponderado(opcoes_dict):
    """Escolhe uma opção com base nos pesos (probabilidades)."""
    opcoes = list(opcoes_dict.keys())
    pesos = list(opcoes_dict.values())
    return np.random.choice(opcoes, p=pesos)


def escolher_eap_padrao():
    """Escolhe um tipo de EAP Padrão com base nos pesos."""
    nomes = list(EAPS_PADRAO.keys())
    pesos = [EAPS_PADRAO[n]["peso"] for n in nomes]
    return np.random.choice(nomes, p=pesos)


def gerar_cnpj_fake():
    """Gera um CNPJ formatado (não válido, apenas para simulação)."""
    nums = [random.randint(0, 9) for _ in range(14)]
    return f"{nums[0]}{nums[1]}.{nums[2]}{nums[3]}{nums[4]}.{nums[5]}{nums[6]}{nums[7]}/{nums[8]}{nums[9]}{nums[10]}{nums[11]}-{nums[12]}{nums[13]}"


def data_aleatoria(inicio, fim):
    """Retorna uma data aleatória entre início e fim."""
    delta = (fim - inicio).days
    dias = random.randint(0, delta)
    return inicio + timedelta(days=dias)


def adicionar_dias(data_base, dias_media, dias_std, minimo=1):
    """Adiciona dias (distribuição normal truncada) a uma data base."""
    dias = max(minimo, int(np.random.normal(dias_media, dias_std)))
    return data_base + timedelta(days=dias)


# ============================================================================
# 1. GERAR FORNECEDORES
# ============================================================================

def gerar_fornecedores():
    """Gera a base de fornecedores com características realistas."""
    print("Gerando fornecedores...")

    prefixos = [
        "Alpha", "Beta", "Delta", "Sigma", "Omega", "Prime", "Tech", "Brasil",
        "Nacional", "Global", "Master", "Smart", "Mega", "Ultra", "Super",
        "Pro", "Max", "Top", "Elite", "Premium", "Express", "Fast", "Net",
        "Sol", "Norte", "Sul", "Leste", "Oeste", "Central", "Inter",
    ]
    sufixos = [
        "Soluções", "Serviços", "Tecnologia", "Engenharia", "Consultoria",
        "Logística", "Facilities", "Segurança", "Sistemas", "Digital",
        "Construções", "Telecomunicações", "Infraestrutura", "Gestão",
        "Administração", "Manutenção", "Limpeza", "Transporte",
    ]
    tipos_empresa = ["Ltda", "S.A.", "Eireli", "ME", "EPP"]

    fornecedores = []
    nomes_usados = set()

    for i in range(NUM_FORNECEDORES):
        while True:
            nome = f"{random.choice(prefixos)} {random.choice(sufixos)} {random.choice(tipos_empresa)}"
            if nome not in nomes_usados:
                nomes_usados.add(nome)
                break

        n_especialidades = random.choices([1, 2, 3], weights=[0.5, 0.35, 0.15])[0]
        especialidades = random.sample(list(TIPOS_SERVICO.keys()), n_especialidades)

        fornecedores.append({
            "fornecedor_id": f"FORN-{i+1:04d}",
            "razao_social": nome,
            "cnpj": gerar_cnpj_fake(),
            "uf": random.choice(UFS),
            "porte": escolher_ponderado(PORTES),
            "especialidade_principal": especialidades[0],
            "especialidades": "|".join(especialidades),
            "nota_desempenho": round(np.clip(np.random.normal(7.5, 1.5), 1, 10), 1),
            "num_contratos_ativos": max(0, int(np.random.poisson(3))),
            "situacao_sicaf": np.random.choice(
                ["Regular", "Regular", "Regular", "Regular", "Irregular", "Vencido"]
            ),
            "dt_cadastro": data_aleatoria(
                datetime(2018, 1, 1), datetime(2023, 12, 31)
            ).strftime("%Y-%m-%d"),
        })

    return pd.DataFrame(fornecedores)


# ============================================================================
# 2. GERAR EAPs (DATASET PRINCIPAL)
# ============================================================================

def gerar_eaps(df_fornecedores):
    """Gera o dataset principal de EAPs de contratação."""
    print("Gerando EAPs...")

    eaps = []
    fornecedor_ids = df_fornecedores["fornecedor_id"].tolist()
    forn_nomes = dict(zip(df_fornecedores["fornecedor_id"], df_fornecedores["razao_social"]))

    forn_especialidades = {}
    for _, row in df_fornecedores.iterrows():
        forn_especialidades[row["fornecedor_id"]] = row["especialidades"].split("|")

    for i in range(NUM_EAPS):
        # Selecionar EAP Padrão (conceito central)
        eap_padrao_nome = escolher_eap_padrao()
        eap_padrao = EAPS_PADRAO[eap_padrao_nome]
        categoria = eap_padrao["categoria"]
        modalidade = eap_padrao["modalidade"]

        tipo_servico = escolher_ponderado(TIPOS_SERVICO)
        unidade = random.choice(UNIDADES_DEMANDANTES)
        status = escolher_ponderado(STATUS_EAP)

        # Valor estimado: log-normal com variação por tipo de serviço
        if "TI" in tipo_servico or "Engenharia" in tipo_servico:
            valor = np.random.lognormal(mean=13, sigma=1.2)
        elif "Consultoria" in tipo_servico:
            valor = np.random.lognormal(mean=12, sigma=1.0)
        else:
            valor = np.random.lognormal(mean=11.5, sigma=1.3)
        valor = round(max(5000, min(valor, 50_000_000)), 2)

        # Data de abertura com sazonalidade (mais processos no Q1 e Q3)
        dt_abertura = data_aleatoria(DATA_INICIO, DATA_FIM)
        mes = dt_abertura.month
        if mes not in [1, 2, 3, 7, 8, 9] and random.random() < 0.3:
            dt_abertura = data_aleatoria(DATA_INICIO, DATA_FIM)

        # Calcular datas-marco percorrendo as etapas da EAP Padrão
        etapas_def = eap_padrao["etapas"]
        dt_atual = dt_abertura
        datas_etapas = []
        for nome_etapa, prazo_media, prazo_std, _ in etapas_def:
            dt_fim_etapa = adicionar_dias(dt_atual, prazo_media, prazo_std, minimo=1)
            datas_etapas.append((nome_etapa, dt_atual, dt_fim_etapa))
            dt_atual = dt_fim_etapa

        dt_ultima_etapa = dt_atual  # data da assinatura se tudo correr bem

        # Intercorrências (mais prováveis em licitações e processos grandes)
        if categoria == "Licitação":
            prob_intercorrencia = 0.22
            if valor > 1_000_000:
                prob_intercorrencia += 0.10
            intercorrencias_possiveis = INTERCORRENCIAS_LICITACAO
        elif categoria == "Contratação Direta":
            prob_intercorrencia = 0.10
            intercorrencias_possiveis = INTERCORRENCIAS_DIRETA
        else:  # Inexigibilidade
            prob_intercorrencia = 0.08
            intercorrencias_possiveis = INTERCORRENCIAS_INEXIGIBILIDADE

        tem_intercorrencia = random.random() < prob_intercorrencia
        tipo_intercorrencia = None
        if tem_intercorrencia:
            tipo_intercorrencia = random.choice(intercorrencias_possiveis)
            atraso = random.randint(10, 60)
            dt_ultima_etapa += timedelta(days=atraso)

        # Participantes do certame
        if categoria == "Licitação":
            num_participantes = max(1, int(np.random.poisson(5)) + 1)
        elif categoria == "Contratação Direta":
            num_participantes = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
        else:  # Inexigibilidade
            num_participantes = 1

        # Selecionar fornecedor vencedor
        categorias_concentradas = [
            "Segurança Patrimonial", "TI - Licenciamento", "Seguros",
            "Consultoria - Jurídica", "Facilities - Vigilância"
        ]
        forn_compativeis = [
            f for f in fornecedor_ids
            if tipo_servico in forn_especialidades.get(f, [])
        ]
        if tipo_servico in categorias_concentradas:
            pool = forn_compativeis[:3] if len(forn_compativeis) >= 3 else fornecedor_ids[:3]
            pesos_pool = [0.60, 0.25, 0.15][:len(pool)]
            pesos_pool = [p/sum(pesos_pool) for p in pesos_pool]
            fornecedor_vencedor = np.random.choice(pool, p=pesos_pool)
        elif forn_compativeis and random.random() < 0.7:
            fornecedor_vencedor = random.choice(forn_compativeis)
        else:
            fornecedor_vencedor = random.choice(fornecedor_ids)

        # Desconto sobre valor estimado
        if num_participantes > 3:
            desconto = np.random.uniform(0.05, 0.30)
        else:
            desconto = np.random.uniform(0.0, 0.15)
        valor_contratado = round(valor * (1 - desconto), 2)

        # Prazo total (dias)
        prazo_total_dias = (dt_ultima_etapa - dt_abertura).days

        # Ajustes por status
        dt_assinatura = dt_ultima_etapa
        if status == "Em Andamento":
            dt_assinatura = None
            prazo_total_dias = None
        elif status == "Cancelado":
            dt_assinatura = None
            valor_contratado = None
            prazo_total_dias = None
        elif status == "Suspenso":
            dt_assinatura = None
            prazo_total_dias = None

        ano = dt_abertura.year

        eaps.append({
            "eap_id": f"EAP-{ano}-{i+1:05d}",
            "eap_padrao": eap_padrao_nome,
            "categoria_contratacao": categoria,
            "modalidade": modalidade,
            "tipo_servico": tipo_servico,
            "objeto_resumido": f"Contratação de {tipo_servico.lower()} para {unidade}",
            "unidade_demandante": unidade,
            "valor_estimado": valor,
            "valor_contratado": valor_contratado,
            "dt_abertura": dt_abertura.strftime("%Y-%m-%d"),
            "dt_assinatura": dt_assinatura.strftime("%Y-%m-%d") if dt_assinatura else None,
            "prazo_total_dias": prazo_total_dias,
            "num_etapas": len(etapas_def),
            "fornecedor_vencedor_id": fornecedor_vencedor if status == "Concluído" else None,
            "fornecedor_vencedor_nome": forn_nomes.get(fornecedor_vencedor, "") if status == "Concluído" else None,
            "num_participantes": num_participantes,
            "tem_intercorrencia": tem_intercorrencia,
            "tipo_intercorrencia": tipo_intercorrencia,
            "status": status,
            "urgencia": random.choices(
                ["Normal", "Urgente", "Emergencial"],
                weights=[0.75, 0.20, 0.05]
            )[0],
            "complexidade": random.choices(
                ["Baixa", "Média", "Alta"],
                weights=[0.30, 0.50, 0.20]
            )[0],
        })

    return pd.DataFrame(eaps)


# ============================================================================
# 3. GERAR ETAPAS DETALHADAS
# ============================================================================

def gerar_etapas(df_eaps):
    """Gera o detalhamento das etapas de cada EAP conforme sua EAP Padrão."""
    print("Gerando etapas detalhadas...")

    etapas = []
    for _, eap in df_eaps.iterrows():
        eap_padrao_nome = eap["eap_padrao"]
        eap_padrao = EAPS_PADRAO[eap_padrao_nome]
        etapas_def = eap_padrao["etapas"]
        num_etapas = len(etapas_def)

        dt_atual = datetime.strptime(eap["dt_abertura"], "%Y-%m-%d")

        # Determinar até qual etapa o processo chegou (baseado no status)
        if eap["status"] == "Concluído":
            etapa_limite = num_etapas  # todas concluídas
        elif eap["status"] == "Em Andamento":
            etapa_limite = random.randint(
                max(1, num_etapas // 3),
                num_etapas - 1
            )
        elif eap["status"] == "Cancelado":
            etapa_limite = random.randint(1, max(1, num_etapas // 2))
        else:  # Suspenso
            etapa_limite = random.randint(
                max(1, num_etapas // 3),
                max(2, num_etapas * 2 // 3)
            )

        for j, (nome_etapa, prazo_media, prazo_std, responsavel) in enumerate(etapas_def):
            if j < etapa_limite:
                dt_fim_etapa = adicionar_dias(dt_atual, prazo_media, prazo_std, minimo=1)
                status_etapa = "Concluída"
                duracao = (dt_fim_etapa - dt_atual).days
                dt_inicio_str = dt_atual.strftime("%Y-%m-%d")
                dt_fim_str = dt_fim_etapa.strftime("%Y-%m-%d")
                dt_atual = dt_fim_etapa
            elif j == etapa_limite and eap["status"] == "Em Andamento":
                dt_inicio_str = dt_atual.strftime("%Y-%m-%d")
                dt_fim_str = None
                duracao = None
                status_etapa = "Em Andamento"
            else:
                dt_inicio_str = None
                dt_fim_str = None
                duracao = None
                if eap["status"] == "Cancelado":
                    status_etapa = "Não Realizada"
                elif eap["status"] == "Suspenso":
                    status_etapa = "Pendente"
                else:
                    status_etapa = "Pendente"

            etapas.append({
                "eap_id": eap["eap_id"],
                "eap_padrao": eap_padrao_nome,
                "etapa_seq": j + 1,
                "etapa_nome": nome_etapa,
                "dt_inicio": dt_inicio_str,
                "dt_fim": dt_fim_str,
                "duracao_dias": duracao,
                "status_etapa": status_etapa,
                "responsavel": responsavel,
            })

    return pd.DataFrame(etapas)


# ============================================================================
# 4. GERAR PARTICIPANTES DOS CERTAMES
# ============================================================================

def gerar_participantes(df_eaps, df_fornecedores):
    """Gera os participantes de cada certame."""
    print("Gerando participantes dos certames...")

    fornecedor_ids = df_fornecedores["fornecedor_id"].tolist()
    participantes = []

    for _, eap in df_eaps.iterrows():
        n_part = eap["num_participantes"]
        vencedor = eap["fornecedor_vencedor_id"]

        participantes_certame = random.sample(
            fornecedor_ids,
            min(n_part, len(fornecedor_ids))
        )

        if vencedor and vencedor not in participantes_certame:
            participantes_certame[0] = vencedor

        for k, forn_id in enumerate(participantes_certame):
            valor_ref = eap["valor_estimado"]
            if forn_id == vencedor:
                fator = np.random.uniform(0.70, 0.95)
            else:
                fator = np.random.uniform(0.75, 1.10)
            valor_proposta = round(valor_ref * fator, 2)

            participantes.append({
                "eap_id": eap["eap_id"],
                "fornecedor_id": forn_id,
                "valor_proposta": valor_proposta,
                "classificacao": k + 1,
                "vencedor": forn_id == vencedor,
                "situacao": "Habilitado" if random.random() < 0.85 else "Inabilitado",
            })

    return pd.DataFrame(participantes)


# ============================================================================
# 5. GERAR CSV DE REFERÊNCIA DAS EAPs PADRÃO
# ============================================================================

def gerar_eaps_padrao_referencia():
    """Gera CSV de referência com as EAPs padrão e suas etapas."""
    print("Gerando referência de EAPs padrão...")

    registros = []
    for nome_eap, config in EAPS_PADRAO.items():
        for j, (nome_etapa, prazo_media, prazo_std, responsavel) in enumerate(config["etapas"]):
            registros.append({
                "eap_padrao": nome_eap,
                "categoria": config["categoria"],
                "modalidade": config["modalidade"],
                "etapa_seq": j + 1,
                "etapa_nome": nome_etapa,
                "prazo_padrao_dias": prazo_media,
                "prazo_desvio_dias": prazo_std,
                "responsavel": responsavel,
            })

    return pd.DataFrame(registros)


# ============================================================================
# 6. GERAR CONTRATOS (CICLO DE VIDA PÓS-ASSINATURA)
# ============================================================================

MOTIVOS_RESCISAO = [
    "Inadimplência do fornecedor",
    "Descumprimento de cláusula contratual",
    "Atraso reiterado na entrega",
    "Falência/recuperação judicial do fornecedor",
    "Interesse público superveniente",
    "Qualidade abaixo do especificado",
]

TIPOS_ADITIVO = [
    "Prorrogação de prazo",
    "Acréscimo de valor (até 25%)",
    "Supressão de valor",
    "Alteração de escopo",
    "Reequilíbrio econômico-financeiro",
]

MOTIVOS_PENALIDADE = [
    "Atraso na entrega",
    "Qualidade insatisfatória",
    "Descumprimento de SLA",
    "Falta de documentação",
    "Irregularidade fiscal",
]


def gerar_contratos(df_eaps, df_fornecedores):
    """Gera o ciclo de vida pós-assinatura dos contratos."""
    print("Gerando contratos (pós-assinatura)...")

    # Criar mapeamentos do fornecedor
    forn_notas = dict(zip(
        df_fornecedores["fornecedor_id"],
        df_fornecedores["nota_desempenho"]
    ))
    forn_portes = dict(zip(
        df_fornecedores["fornecedor_id"],
        df_fornecedores["porte"]
    ))
    forn_nomes = dict(zip(
        df_fornecedores["fornecedor_id"],
        df_fornecedores["razao_social"]
    ))

    contratos = []
    concluidos = df_eaps[df_eaps["status"] == "Concluído"].copy()

    for _, eap in concluidos.iterrows():
        forn_id = eap["fornecedor_vencedor_id"]
        if pd.isna(forn_id):
            continue

        dt_assinatura = datetime.strptime(eap["dt_assinatura"], "%Y-%m-%d")
        valor_contratado = eap["valor_contratado"]
        categoria = eap["categoria_contratacao"]
        tipo_servico = eap["tipo_servico"]

        # Vigência: serviços contínuos = 12 meses, obras = 6-24 meses
        if "Engenharia" in tipo_servico:
            vigencia_meses = random.choices([6, 12, 18, 24], weights=[0.1, 0.3, 0.4, 0.2])[0]
        elif "Facilities" in tipo_servico or "Segurança" in tipo_servico:
            vigencia_meses = random.choices([12, 24, 36], weights=[0.3, 0.5, 0.2])[0]
        else:
            vigencia_meses = random.choices([6, 12, 24], weights=[0.2, 0.5, 0.3])[0]

        dt_vigencia_fim = dt_assinatura + timedelta(days=vigencia_meses * 30)

        # Nota do fornecedor influencia tudo
        nota = forn_notas.get(forn_id, 7.5)
        porte = forn_portes.get(forn_id, "Médio")

        # --- ADITIVOS ---
        # Mais prováveis em contratos longos, grandes, com fornecedor de nota baixa
        prob_aditivo_base = 0.30
        if vigencia_meses >= 18:
            prob_aditivo_base += 0.15
        if valor_contratado and valor_contratado > 1_000_000:
            prob_aditivo_base += 0.10
        if nota < 6.0:
            prob_aditivo_base += 0.10

        num_aditivos = 0
        aditivos_valor_total = 0
        if random.random() < prob_aditivo_base:
            num_aditivos = random.choices([1, 2, 3, 4], weights=[0.50, 0.30, 0.15, 0.05])[0]
            for _ in range(num_aditivos):
                tipo_adit = random.choice(TIPOS_ADITIVO)
                if "Acréscimo" in tipo_adit:
                    aditivos_valor_total += valor_contratado * np.random.uniform(0.05, 0.25)
                elif "Supressão" in tipo_adit:
                    aditivos_valor_total -= valor_contratado * np.random.uniform(0.03, 0.15)

        # --- RESCISÃO ---
        # Mais provável com nota baixa, ME/EPP, valor alto
        prob_rescisao = 0.08
        if nota < 5.0:
            prob_rescisao += 0.25
        elif nota < 6.5:
            prob_rescisao += 0.10
        if porte in ["ME", "EPP"]:
            prob_rescisao += 0.05
        if valor_contratado and valor_contratado > 2_000_000:
            prob_rescisao += 0.05
        if num_aditivos >= 3:
            prob_rescisao += 0.10
        if categoria == "Inexigibilidade":
            prob_rescisao += 0.05

        teve_rescisao = random.random() < prob_rescisao
        motivo_rescisao = None
        dt_rescisao = None
        if teve_rescisao:
            motivo_rescisao = random.choice(MOTIVOS_RESCISAO)
            # Rescisão acontece entre 20% e 80% da vigência
            dias_vigencia = (dt_vigencia_fim - dt_assinatura).days
            dt_rescisao = dt_assinatura + timedelta(
                days=random.randint(int(dias_vigencia * 0.2), int(dias_vigencia * 0.8))
            )

        # --- PENALIDADES ---
        prob_penalidade = 0.12
        if nota < 6.0:
            prob_penalidade += 0.20
        if teve_rescisao:
            prob_penalidade += 0.30
        if num_aditivos >= 2:
            prob_penalidade += 0.10

        num_penalidades = 0
        if random.random() < prob_penalidade:
            num_penalidades = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]

        # --- ATRASOS ---
        prob_atraso = 0.15
        if nota < 6.0:
            prob_atraso += 0.20
        if "Engenharia" in tipo_servico:
            prob_atraso += 0.10

        teve_atraso = random.random() < prob_atraso
        dias_atraso_total = 0
        if teve_atraso:
            dias_atraso_total = random.randint(5, 90)

        # Número do contrato
        ano = dt_assinatura.year
        contrato_id = f"CT-{ano}-{len(contratos)+1:05d}"

        contratos.append({
            "contrato_id": contrato_id,
            "eap_id": eap["eap_id"],
            "fornecedor_id": forn_id,
            "fornecedor_nome": forn_nomes.get(forn_id, ""),
            "tipo_servico": tipo_servico,
            "categoria_contratacao": categoria,
            "eap_padrao": eap["eap_padrao"],
            "valor_contratado": valor_contratado,
            "dt_assinatura": dt_assinatura.strftime("%Y-%m-%d"),
            "dt_vigencia_fim": dt_vigencia_fim.strftime("%Y-%m-%d"),
            "vigencia_meses": vigencia_meses,
            "num_aditivos": num_aditivos,
            "aditivos_valor_total": round(aditivos_valor_total, 2),
            "teve_rescisao": teve_rescisao,
            "motivo_rescisao": motivo_rescisao,
            "dt_rescisao": dt_rescisao.strftime("%Y-%m-%d") if dt_rescisao else None,
            "num_penalidades": num_penalidades,
            "teve_atraso": teve_atraso,
            "dias_atraso_total": dias_atraso_total,
            "nota_fornecedor": nota,
            "porte_fornecedor": porte,
        })

    return pd.DataFrame(contratos)


# ============================================================================
# EXECUÇÃO PRINCIPAL
# ============================================================================

def main():
    print("=" * 60)
    print("HyperCopa DISEC 2026 - Gerador de Dados Sintéticos")
    print("CESUP-Contratações | Banco do Brasil")
    print("=" * 60)
    print()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Gerar datasets
    df_fornecedores = gerar_fornecedores()
    df_eaps = gerar_eaps(df_fornecedores)
    df_etapas = gerar_etapas(df_eaps)
    df_participantes = gerar_participantes(df_eaps, df_fornecedores)
    df_eaps_padrao = gerar_eaps_padrao_referencia()
    df_contratos = gerar_contratos(df_eaps, df_fornecedores)

    # Salvar CSVs
    df_fornecedores.to_csv(f"{OUTPUT_DIR}/fornecedores.csv", index=False, encoding="utf-8-sig")
    df_eaps.to_csv(f"{OUTPUT_DIR}/eaps.csv", index=False, encoding="utf-8-sig")
    df_etapas.to_csv(f"{OUTPUT_DIR}/etapas_eap.csv", index=False, encoding="utf-8-sig")
    df_participantes.to_csv(f"{OUTPUT_DIR}/participantes.csv", index=False, encoding="utf-8-sig")
    df_eaps_padrao.to_csv(f"{OUTPUT_DIR}/eaps_padrao.csv", index=False, encoding="utf-8-sig")
    df_contratos.to_csv(f"{OUTPUT_DIR}/contratos.csv", index=False, encoding="utf-8-sig")

    # Estatísticas
    print()
    print("-" * 60)
    print("DATASETS GERADOS:")
    print("-" * 60)
    print(f"  fornecedores.csv   : {len(df_fornecedores):>6} registros")
    print(f"  eaps.csv           : {len(df_eaps):>6} registros")
    print(f"  etapas_eap.csv     : {len(df_etapas):>6} registros")
    print(f"  participantes.csv  : {len(df_participantes):>6} registros")
    print(f"  eaps_padrao.csv    : {len(df_eaps_padrao):>6} registros")
    print(f"  contratos.csv      : {len(df_contratos):>6} registros")
    print()

    # Resumo analítico
    print("-" * 60)
    print("RESUMO ANALÍTICO (validação dos dados):")
    print("-" * 60)

    print("\nDistribuição por EAP Padrão:")
    for eap, pct in df_eaps["eap_padrao"].value_counts(normalize=True).items():
        cat = EAPS_PADRAO[eap]["categoria"]
        n_etapas = len(EAPS_PADRAO[eap]["etapas"])
        print(f"  {eap:<45} {pct:>5.1%}  ({cat}, {n_etapas} etapas)")

    print("\nDistribuição por categoria:")
    for cat, pct in df_eaps["categoria_contratacao"].value_counts(normalize=True).items():
        print(f"  {cat:<25} {pct:>6.1%}")

    print("\nDistribuição por modalidade:")
    for mod, pct in df_eaps["modalidade"].value_counts(normalize=True).items():
        print(f"  {mod:<25} {pct:>6.1%}")

    print("\nDistribuição por status:")
    for st, pct in df_eaps["status"].value_counts(normalize=True).items():
        print(f"  {st:<20} {pct:>6.1%}")

    print("\nValor estimado (R$):")
    vals = df_eaps["valor_estimado"]
    print(f"  Mínimo:    R$ {vals.min():>15,.2f}")
    print(f"  Mediana:   R$ {vals.median():>15,.2f}")
    print(f"  Média:     R$ {vals.mean():>15,.2f}")
    print(f"  Máximo:    R$ {vals.max():>15,.2f}")

    concluidos = df_eaps[df_eaps["status"] == "Concluído"]
    if len(concluidos) > 0:
        print("\nPrazo total (dias - processos concluídos) por categoria:")
        for cat in concluidos["categoria_contratacao"].unique():
            subset = concluidos[concluidos["categoria_contratacao"] == cat]
            prazos = subset["prazo_total_dias"].dropna()
            if len(prazos) > 0:
                print(f"  {cat}:")
                print(f"    Mínimo: {prazos.min():>5.0f}d | Mediana: {prazos.median():>5.0f}d | Média: {prazos.mean():>5.1f}d | Máximo: {prazos.max():>5.0f}d")

    print(f"\nIntercorrências: {df_eaps['tem_intercorrencia'].mean():.1%} dos processos")
    for cat in df_eaps["categoria_contratacao"].unique():
        subset = df_eaps[df_eaps["categoria_contratacao"] == cat]
        print(f"  {cat:<25} {subset['tem_intercorrencia'].mean():>5.1%}")

    print("\nTop 5 tipos de serviço:")
    for ts, n in df_eaps["tipo_servico"].value_counts().head(5).items():
        print(f"  {ts:<35} {n:>5} processos")

    print("\nPorte dos fornecedores:")
    for p, pct in df_fornecedores["porte"].value_counts(normalize=True).items():
        print(f"  {p:<10} {pct:>6.1%}")

    # Validação de etapas
    print("\nEtapas por EAP Padrão (referência):")
    for nome_eap, config in EAPS_PADRAO.items():
        etapas_nomes = [e[0] for e in config["etapas"]]
        print(f"  {nome_eap} ({len(etapas_nomes)} etapas):")
        for j, nome in enumerate(etapas_nomes, 1):
            prazo = config["etapas"][j-1][1]
            print(f"    {j:>2}. {nome:<45} ~{prazo:>2}d")

    # Resumo de contratos
    if len(df_contratos) > 0:
        print("\n--- CONTRATOS (pós-assinatura) ---")
        print(f"  Total de contratos: {len(df_contratos)}")
        print(f"  Com aditivos:       {(df_contratos['num_aditivos'] > 0).sum()} ({(df_contratos['num_aditivos'] > 0).mean():.1%})")
        print(f"  Com rescisão:       {df_contratos['teve_rescisao'].sum()} ({df_contratos['teve_rescisao'].mean():.1%})")
        print(f"  Com penalidades:    {(df_contratos['num_penalidades'] > 0).sum()} ({(df_contratos['num_penalidades'] > 0).mean():.1%})")
        print(f"  Com atraso:         {df_contratos['teve_atraso'].sum()} ({df_contratos['teve_atraso'].mean():.1%})")
        if df_contratos['teve_rescisao'].sum() > 0:
            print("  Motivos de rescisão:")
            for m, n in df_contratos[df_contratos['teve_rescisao']]['motivo_rescisao'].value_counts().items():
                print(f"    {m:<45} {n}")

    print()
    print("=" * 60)
    print(f"Arquivos salvos em: {os.path.abspath(OUTPUT_DIR)}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
