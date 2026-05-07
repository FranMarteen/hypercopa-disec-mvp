"""
============================================================================
HyperCopa DISEC 2026 - Gerador de Dados Sintéticos (MODELO POSTGRES / UUIDs)
============================================================================

Versão normalizada do modelo anterior. Gera 12 tabelas relacionais com
chaves UUID v4 e produz também schema.sql com DDL PostgreSQL.

Principais mudanças vs. gerar_dados_sinteticos_eaps.py:
  - IDs string (EAP-2022-00001) → UUIDs v4
  - eap_padrao agora é categoria × objeto (ex: "Licitação de TI - Infraestrutura")
  - Tabelas lookup separadas: tipo_licitacao, objeto_licitacao, unidade, responsavel_tipo
  - Nova tabela etapa_padrao (normaliza o que era desnormalizado em eaps_padrao.csv)
  - Nova tabela fornecedor_especialidade (N:M entre fornecedor e objeto_licitacao)
  - Campo unidade_executante: CESUP-SP (90%) e DISEC (10%); ambos executam todas as modalidades

Saída: pasta ./dados_postgres/
  12 CSVs (um por tabela) + schema.sql
============================================================================
"""
import os
import sys
import random
import time
import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# stdout em UTF-8 (permite caracteres bonitos nos logs mesmo no Windows cp1252)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

SEED = 42
NUM_EAPS = 2500
NUM_FORNECEDORES = 300
DATA_INICIO = datetime(2022, 1, 1)
DATA_FIM = datetime(2025, 12, 31)
OUTPUT_DIR = "./dados_postgres"

random.seed(SEED)
np.random.seed(SEED)


def new_uuid():
    return str(uuid.uuid4())


# ============================================================================
# LOGS DIDÁTICOS
# ============================================================================

W = 74  # largura padrão das caixas

def banner():
    print("╔" + "═" * (W - 2) + "╗")
    print(("║" + "{:^" + str(W - 2) + "}║").format("HyperCopa DISEC 2026 — Gerador de Dados Sintéticos"))
    print(("║" + "{:^" + str(W - 2) + "}║").format("Modelo PostgreSQL com UUIDs — 12 tabelas relacionais"))
    print("╚" + "═" * (W - 2) + "╝")
    print()
    print("  Este gerador cria dados sintéticos realistas de contratações do BB,")
    print("  simulando o ciclo completo: planejamento → licitação → execução → contrato.")
    print()
    print(f"  SEED: {SEED} (determinístico — sempre gera os mesmos dados)")
    print(f"  Volumes alvo: {NUM_EAPS} EAPs, {NUM_FORNECEDORES} fornecedores")
    print(f"  Janela temporal: {DATA_INICIO.date()} a {DATA_FIM.date()}")
    print(f"  Saída: {os.path.abspath(OUTPUT_DIR)}")
    print()


def fase(num, total, titulo, por_que, o_que_gera):
    """Imprime o cabeçalho de uma fase. Retorna o tempo de início."""
    print("┌─ [" + f"{num}/{total}" + "] " + titulo + " " + "─" * max(1, W - 8 - len(titulo) - len(f"{num}/{total}")))
    print(f"│  💡 {por_que}")
    print(f"│  📦 Produz: {o_que_gera}")
    print("│")
    return time.time()


def passo(msg):
    print(f"│  → {msg}")


def stat(label, valor):
    print(f"│     {label:<45} {valor}")


def fase_fim(t0, n_rows=None, extra=None):
    elapsed = time.time() - t0
    resumo = f"✓ concluído em {elapsed:.2f}s"
    if n_rows is not None:
        resumo += f" · {n_rows:,} linhas"
    if extra:
        resumo += f" · {extra}"
    print(f"└─ {resumo}")
    print()


# ============================================================================
# DOMÍNIOS
# ============================================================================

TIPOS_LICITACAO = {
    # nome → modalidade, peso de ocorrência
    "Licitação":            ("Licitação Eletrônica", 0.70),
    "Contratação Direta":   ("Contratação Direta",   0.25),
    "Inexigibilidade":      ("Inexigibilidade",      0.05),
}

OBJETOS_LICITACAO = {
    # nome → (categoria_macro, peso)
    "TI - Infraestrutura":         ("TI", 0.15),
    "TI - Desenvolvimento":        ("TI", 0.12),
    "TI - Licenciamento":          ("TI", 0.08),
    "Engenharia - Obras":          ("Engenharia", 0.10),
    "Engenharia - Manutenção":     ("Engenharia", 0.08),
    "Facilities - Limpeza":        ("Facilities", 0.07),
    "Facilities - Vigilância":     ("Facilities", 0.06),
    "Facilities - Recepção":       ("Facilities", 0.03),
    "Logística - Transporte":      ("Logística", 0.05),
    "Logística - Armazenagem":     ("Logística", 0.03),
    "Segurança Patrimonial":       ("Segurança", 0.05),
    "Consultoria - Gestão":        ("Consultoria", 0.04),
    "Consultoria - Jurídica":      ("Consultoria", 0.03),
    "Marketing e Comunicação":     ("Marketing", 0.04),
    "Treinamento e Capacitação":   ("Treinamento", 0.03),
    "Seguros":                     ("Seguros", 0.02),
    "Material de Escritório":      ("Material", 0.02),
}

UNIDADES = [
    # (prefixo, nome, pode_demandar, pode_executar)
    ("DITEC", "Diretoria de Tecnologia", True, False),
    ("DILOG", "Diretoria de Logística", True, False),
    ("DIMAC", "Diretoria de Macroestratégia", True, False),
    ("DIREO", "Diretoria Operacional", True, False),
    ("DIRES", "Diretoria de Recursos", True, False),
    ("DIFIN", "Diretoria Financeira", True, False),
    ("DICOM", "Diretoria de Comunicação", True, False),
    ("DIJUR", "Diretoria Jurídica", True, False),
    ("DIPES", "Diretoria de Pessoas", True, False),
    ("DIRIS", "Diretoria de Risco", True, False),
    ("DISEC", "Diretoria de Serviços e Contratações", True, True),
    ("DIOPE", "Diretoria de Operações", True, False),
    ("DIGER", "Diretoria Geral", True, False),
    ("DICRE", "Diretoria de Crédito", True, False),
    ("DIMAP", "Diretoria de Mapeamento", True, False),
    ("SUREF-SP", "Superintendência Regional SP", True, False),
    ("SUREF-RJ", "Superintendência Regional RJ", True, False),
    ("SUREF-MG", "Superintendência Regional MG", True, False),
    ("SUREF-RS", "Superintendência Regional RS", True, False),
    ("SUREF-PR", "Superintendência Regional PR", True, False),
    ("SUREF-BA", "Superintendência Regional BA", True, False),
    ("SUREF-DF", "Superintendência Regional DF", True, False),
    ("SUREF-PE", "Superintendência Regional PE", True, False),
    ("SUREF-CE", "Superintendência Regional CE", True, False),
    ("CESUP-SP", "Centro de Suporte Operacional SP", True, True),
]

RESPONSAVEIS = ["Equipe Técnica", "Pregoeiro", "Gestor do Contrato", "Autoridade Competente", "Externo"]

# Etapas base por categoria (antes de "Publicação do Edital" / "Ratificação" entram as extras)
ETAPAS_BASE = {
    "Licitação": [
        ("Análise da Demanda",                    15, 5, "Equipe Técnica"),
        ("Complementação de Informações",         10, 4, "Equipe Técnica"),
        ("Elaboração do Edital",                  25, 8, "Equipe Técnica"),
        ("Publicação do Edital",                   3, 1, "Pregoeiro"),
        ("Prazo de Elaboração das Propostas",     15, 5, "Externo"),
        ("Sessão de Disputa",                      1, 0, "Pregoeiro"),
        ("Habilitação Jurídica",                   4, 2, "Pregoeiro"),
        ("Qualificação Técnica",                   5, 2, "Pregoeiro"),
        ("Qualificação Econômico-Financeira",      4, 2, "Pregoeiro"),
        ("Declaração de Vencedor",                 3, 1, "Pregoeiro"),
        ("Convocação para Assinatura",             8, 3, "Gestor do Contrato"),
        ("Assinatura do Contrato",                 5, 2, "Autoridade Competente"),
    ],
    "Contratação Direta": [
        ("Análise de Conformidade",              10, 4, "Equipe Técnica"),
        ("Complementação de Informações",         5, 2, "Equipe Técnica"),
        ("Verificação de Documentação",           5, 2, "Equipe Técnica"),
        ("Ratificação/Aprovação",                 3, 1, "Autoridade Competente"),
        ("Convocação para Assinatura",            5, 2, "Gestor do Contrato"),
        ("Assinatura do Contrato",                3, 1, "Autoridade Competente"),
    ],
    "Inexigibilidade": [
        ("Análise de Conformidade",              10, 4, "Equipe Técnica"),
        ("Justificativa de Inexigibilidade",      7, 3, "Equipe Técnica"),
        ("Ratificação",                           5, 2, "Autoridade Competente"),
        ("Convocação para Assinatura",            5, 2, "Gestor do Contrato"),
        ("Assinatura do Contrato",                3, 1, "Autoridade Competente"),
    ],
}

# Etapas extras por macro-categoria do objeto (inseridas antes de "Publicação do Edital"
# em licitações, ou antes de "Ratificação" em direta/inexigibilidade)
ETAPAS_EXTRAS_POR_MACRO = {
    "Engenharia": [
        ("Aprovação de Projeto",    7, 3, "Equipe Técnica"),
    ],
    "TI": [
        ("Prova de Conceito",      15, 5, "Equipe Técnica"),
    ],
    "Consultoria": [
        ("Apresentação de Metodologia", 5, 2, "Equipe Técnica"),
    ],
}

INTERCORRENCIAS_LICITACAO = [
    "Impugnação ao Edital", "Recurso Administrativo", "Certame Deserto",
    "Certame Fracassado", "Suspensão Judicial", "Revisão de Edital",
    "Diligência TCU", "Questionamento de Preço", "Inabilitação de Licitante",
    "Pedido de Esclarecimento",
]
INTERCORRENCIAS_DIRETA = [
    "Complementação de Documentação", "Questionamento de Preço",
    "Diligência TCU", "Revisão de Justificativa",
]
INTERCORRENCIAS_INEXIGIBILIDADE = [
    "Complementação de Justificativa", "Questionamento de Preço", "Diligência TCU",
]

STATUS_EAP = {
    "Concluído":     0.80,
    "Em Andamento":  0.12,
    "Cancelado":     0.05,
    "Suspenso":      0.03,
}

UFS = ["SP","RJ","MG","RS","PR","BA","DF","PE","CE","SC","GO","PA","MA","AM",
       "ES","PB","RN","AL","PI","SE","MT","MS","RO","TO","AC","AP","RR"]

PORTES = {"ME": 0.25, "EPP": 0.30, "Médio": 0.25, "Grande": 0.20}

# Regiões brasileiras (+ "Nacional" para abrangência total)
REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul", "Nacional"]

# UF → região (para gerar unidades de negócio por região)
UF_REGIAO = {
    "AC":"Norte","AP":"Norte","AM":"Norte","PA":"Norte","RO":"Norte","RR":"Norte","TO":"Norte",
    "AL":"Nordeste","BA":"Nordeste","CE":"Nordeste","MA":"Nordeste","PB":"Nordeste","PE":"Nordeste","PI":"Nordeste","RN":"Nordeste","SE":"Nordeste",
    "DF":"Centro-Oeste","GO":"Centro-Oeste","MT":"Centro-Oeste","MS":"Centro-Oeste",
    "ES":"Sudeste","MG":"Sudeste","RJ":"Sudeste","SP":"Sudeste",
    "PR":"Sul","RS":"Sul","SC":"Sul",
}

# Volume alvo de unidades de negócio (agências / postos de atendimento)
NUM_UNIDADES_NEGOCIO = 5000

# Tipos de unidade de negócio do BB
TIPOS_UNIDADE_NEGOCIO = {
    "Agência":             0.55,
    "Posto de Atendimento": 0.25,
    "Escritório":          0.12,
    "PAE":                 0.05,  # Posto de Atendimento Eletrônico
    "Unidade Especial":    0.03,
}

MOTIVOS_RESCISAO = [
    "Inadimplência do fornecedor", "Descumprimento de cláusula contratual",
    "Atraso reiterado na entrega", "Falência/recuperação judicial do fornecedor",
    "Interesse público superveniente", "Qualidade abaixo do especificado",
]


# ============================================================================
# HELPERS
# ============================================================================

def escolher_ponderado(opcoes_dict):
    return np.random.choice(list(opcoes_dict.keys()), p=list(opcoes_dict.values()))


def escolher_por_peso(items_pesos):
    """items_pesos: list of (item, peso)."""
    items, pesos = zip(*items_pesos)
    pesos_norm = np.array(pesos) / sum(pesos)
    return items[np.random.choice(len(items), p=pesos_norm)]


def gerar_cnpj():
    n = [random.randint(0, 9) for _ in range(14)]
    return f"{n[0]}{n[1]}.{n[2]}{n[3]}{n[4]}.{n[5]}{n[6]}{n[7]}/{n[8]}{n[9]}{n[10]}{n[11]}-{n[12]}{n[13]}"


def data_aleatoria(inicio, fim):
    delta = (fim - inicio).days
    return inicio + timedelta(days=random.randint(0, delta))


def adicionar_dias(data_base, media, std, minimo=1):
    dias = max(minimo, int(np.random.normal(media, std)))
    return data_base + timedelta(days=dias)


# ============================================================================
# 1. LOOKUPS
# ============================================================================

def gerar_tipo_licitacao():
    rows = []
    for nome, (modalidade, _peso) in TIPOS_LICITACAO.items():
        rows.append({"id": new_uuid(), "nome": nome, "modalidade": modalidade})
    return pd.DataFrame(rows)


def gerar_objeto_licitacao():
    rows = []
    for nome, (macro, _peso) in OBJETOS_LICITACAO.items():
        rows.append({"id": new_uuid(), "nome": nome, "categoria_macro": macro})
    return pd.DataFrame(rows)


def gerar_unidade():
    rows = []
    for prefixo, nome, pode_d, pode_e in UNIDADES:
        rows.append({
            "id": new_uuid(), "prefixo": prefixo, "nome": nome,
            "pode_demandar": pode_d, "pode_executar": pode_e,
        })
    return pd.DataFrame(rows)


def gerar_responsavel_tipo():
    return pd.DataFrame([{"id": new_uuid(), "nome": r} for r in RESPONSAVEIS])


# ============================================================================
# 2. TEMPLATES: eap_padrao × objeto, com etapas base+extras
# ============================================================================

def etapas_para(tipo_nome, macro_objeto):
    """Gera lista de etapas (com extras por macro) para uma combinação."""
    base = list(ETAPAS_BASE[tipo_nome])
    extras = ETAPAS_EXTRAS_POR_MACRO.get(macro_objeto, [])
    if not extras:
        return base

    # Define ponto de inserção: antes de "Publicação do Edital" (Licit) ou "Ratificação..." (Direta/Inexig)
    marcos = {"Licitação": "Publicação do Edital",
              "Contratação Direta": "Ratificação/Aprovação",
              "Inexigibilidade": "Ratificação"}
    marco = marcos[tipo_nome]
    idx = next((i for i, e in enumerate(base) if e[0] == marco), len(base))
    return base[:idx] + extras + base[idx:]


def gerar_eap_padrao_e_etapas(df_tipo, df_objeto, df_resp):
    """Cria um eap_padrao por combinação (tipo × objeto) e as etapa_padrao correspondentes."""
    eap_padrao_rows = []
    etapa_padrao_rows = []
    resp_map = dict(zip(df_resp["nome"], df_resp["id"]))

    for _, tipo in df_tipo.iterrows():
        for _, obj in df_objeto.iterrows():
            macro = OBJETOS_LICITACAO[obj["nome"]][0]
            eap_padrao_id = new_uuid()
            eap_padrao_rows.append({
                "id": eap_padrao_id,
                "tipo_licitacao_id": tipo["id"],
                "objeto_licitacao_id": obj["id"],
                "nome": f"{tipo['nome']} de {obj['nome']}",
            })
            etapas = etapas_para(tipo["nome"], macro)
            for seq, (nome, prazo, desvio, resp) in enumerate(etapas, start=1):
                etapa_padrao_rows.append({
                    "id": new_uuid(),
                    "eap_padrao_id": eap_padrao_id,
                    "sequencia": seq,
                    "nome": nome,
                    "prazo_padrao_dias": prazo,
                    "prazo_desvio_dias": desvio,
                    "responsavel_tipo_id": resp_map[resp],
                })

    return pd.DataFrame(eap_padrao_rows), pd.DataFrame(etapa_padrao_rows)


# ============================================================================
# 3. FORNECEDOR + ESPECIALIDADES
# ============================================================================

def gerar_fornecedor():
    prefixos = ["Alpha","Beta","Delta","Sigma","Omega","Prime","Tech","Brasil",
        "Nacional","Global","Master","Smart","Mega","Ultra","Super","Pro","Max",
        "Top","Elite","Premium","Express","Fast","Net","Sol","Norte","Sul",
        "Leste","Oeste","Central","Inter"]
    sufixos = ["Soluções","Serviços","Tecnologia","Engenharia","Consultoria",
        "Logística","Facilities","Segurança","Sistemas","Digital","Construções",
        "Telecomunicações","Infraestrutura","Gestão","Administração","Manutenção",
        "Limpeza","Transporte"]
    tipos = ["Ltda", "S.A.", "Eireli", "ME", "EPP"]

    # Patrimônio líquido por porte (faixas R$ — patamar BB)
    pl_por_porte = {
        "ME":     (50_000,       500_000),
        "EPP":    (500_000,      5_000_000),
        "Médio":  (5_000_000,    50_000_000),
        "Grande": (50_000_000,   2_000_000_000),
    }

    rows = []
    usados = set()
    for _ in range(NUM_FORNECEDORES):
        while True:
            nome = f"{random.choice(prefixos)} {random.choice(sufixos)} {random.choice(tipos)}"
            if nome not in usados:
                usados.add(nome)
                break
        porte = escolher_ponderado(PORTES)
        pl_min, pl_max = pl_por_porte[porte]
        # Patrimônio líquido: log-uniform dentro da faixa
        patrimonio = round(np.exp(np.random.uniform(np.log(pl_min), np.log(pl_max))), 2)
        # Capital social ~ 30-80% do PL
        capital = round(patrimonio * np.random.uniform(0.30, 0.80), 2)
        # Faturamento anual ~ 1.5-6x PL (empresas saudáveis giram o patrimônio)
        faturamento = round(patrimonio * np.random.uniform(1.5, 6.0), 2)
        # Índices: a maioria das empresas saudáveis tem LC/LG/SG > 1
        # Lei 14.133/21 art. 69: exige índices >= 1 para qualificação econômico-financeira
        liq_corrente = round(np.clip(np.random.lognormal(0.5, 0.35), 0.5, 6.0), 2)
        liq_geral    = round(np.clip(np.random.lognormal(0.4, 0.30), 0.4, 5.0), 2)
        solv_geral   = round(np.clip(np.random.lognormal(0.6, 0.30), 0.5, 8.0), 2)

        rows.append({
            "id": new_uuid(),
            "razao_social": nome,
            "cnpj": gerar_cnpj(),
            "uf": random.choice(UFS),
            "porte": porte,
            "nota_desempenho": round(np.clip(np.random.normal(7.5, 1.5), 1, 10), 1),
            "situacao_sicaf": np.random.choice(
                ["Regular","Regular","Regular","Regular","Irregular","Vencido"]),
            "dt_cadastro": data_aleatoria(
                datetime(2018, 1, 1), datetime(2023, 12, 31)).strftime("%Y-%m-%d"),
            # Qualificação econômico-financeira
            "patrimonio_liquido": patrimonio,
            "capital_social": capital,
            "faturamento_anual": faturamento,
            "indice_liquidez_corrente": liq_corrente,
            "indice_liquidez_geral": liq_geral,
            "indice_solvencia_geral": solv_geral,
        })
    return pd.DataFrame(rows)


def gerar_fornecedor_especialidade(df_forn, df_obj):
    """Cada fornecedor tem 1-3 especialidades; a primeira é principal."""
    objetos = df_obj[["id", "nome"]].values.tolist()
    rows = []
    for _, f in df_forn.iterrows():
        n = random.choices([1, 2, 3], weights=[0.5, 0.35, 0.15])[0]
        chosen = random.sample(objetos, n)
        for i, (obj_id, _) in enumerate(chosen):
            rows.append({
                "fornecedor_id": f["id"],
                "objeto_licitacao_id": obj_id,
                "principal": i == 0,
            })
    return pd.DataFrame(rows)


# ============================================================================
# REGIÕES (lookup) + fornecedor_regiao (N:M)
# ============================================================================

def gerar_regiao():
    return pd.DataFrame([{"id": new_uuid(), "nome": r} for r in REGIOES])


def gerar_fornecedor_regiao(df_forn, df_regiao):
    """Cada fornecedor atende 1 ou mais regiões. Porte Grande tem viés para Nacional."""
    reg_map = dict(zip(df_regiao["nome"], df_regiao["id"]))
    rows = []
    for _, f in df_forn.iterrows():
        porte = f["porte"]
        # Grande: 40% Nacional, senão 2-4 regiões; Médio: 30% Nacional, 1-3 regiões
        # EPP/ME: geralmente 1 região (local)
        if porte == "Grande":
            if random.random() < 0.40:
                atendidas = ["Nacional"]
            else:
                atendidas = random.sample([r for r in REGIOES if r != "Nacional"],
                                          random.randint(2, 4))
        elif porte == "Médio":
            if random.random() < 0.30:
                atendidas = ["Nacional"]
            else:
                atendidas = random.sample([r for r in REGIOES if r != "Nacional"],
                                          random.randint(1, 3))
        else:  # ME, EPP
            # Região do HQ (uf→região) + chance pequena de atender vizinha
            reg_hq = UF_REGIAO.get(f["uf"], "Sudeste")
            atendidas = [reg_hq]
            if random.random() < 0.15:
                outras = [r for r in REGIOES if r not in (reg_hq, "Nacional")]
                atendidas.append(random.choice(outras))
        for r in atendidas:
            rows.append({
                "fornecedor_id": f["id"],
                "regiao_id": reg_map[r],
            })
    return pd.DataFrame(rows)


# ============================================================================
# UNIDADES DE NEGÓCIO (agências, postos) + regiões/UF
# ============================================================================

def gerar_unidade_negocio(df_regiao):
    """Gera ~5000 unidades de negócio (agências, postos etc.) com prefixo numérico BB-like."""
    reg_map = dict(zip(df_regiao["nome"], df_regiao["id"]))

    # Distribuição por UF proporcional à população/agências reais (estimativa)
    peso_uf = {
        "SP": 0.22, "RJ": 0.10, "MG": 0.11, "RS": 0.07, "PR": 0.06, "BA": 0.06,
        "SC": 0.04, "PE": 0.04, "CE": 0.04, "GO": 0.03, "PA": 0.03, "DF": 0.03,
        "ES": 0.02, "MA": 0.02, "MT": 0.02, "MS": 0.02, "AM": 0.02, "PB": 0.02,
        "RN": 0.02, "AL": 0.01, "PI": 0.01, "SE": 0.01, "RO": 0.01, "TO": 0.005,
        "AC": 0.003, "AP": 0.002, "RR": 0.002,
    }
    # normaliza
    s = sum(peso_uf.values())
    peso_uf = {k: v/s for k, v in peso_uf.items()}

    rows = []
    # prefixos tipo "0001-SP", "0002-RJ" — no BB real são 4-5 dígitos
    prefixo_seq = 1
    cidades_por_uf = {
        "SP":["São Paulo","Campinas","Guarulhos","Santos","Ribeirão Preto","Sorocaba"],
        "RJ":["Rio de Janeiro","Niterói","Nova Iguaçu","Duque de Caxias"],
        "MG":["Belo Horizonte","Uberlândia","Contagem","Juiz de Fora"],
        "RS":["Porto Alegre","Canoas","Caxias do Sul","Pelotas"],
        "PR":["Curitiba","Londrina","Maringá","Ponta Grossa"],
        "SC":["Florianópolis","Joinville","Blumenau"],
        "BA":["Salvador","Feira de Santana","Ilhéus"],
        "PE":["Recife","Olinda","Caruaru"],
        "CE":["Fortaleza","Caucaia","Sobral"],
        "GO":["Goiânia","Anápolis"],
        "DF":["Brasília","Taguatinga","Ceilândia"],
        "ES":["Vitória","Vila Velha","Serra"],
        "PA":["Belém","Ananindeua","Santarém"],
        "AM":["Manaus","Parintins"],
        "MA":["São Luís","Imperatriz"],
        "MT":["Cuiabá","Várzea Grande"],
        "MS":["Campo Grande","Dourados"],
        "PB":["João Pessoa","Campina Grande"],
        "RN":["Natal","Mossoró"],
        "AL":["Maceió","Arapiraca"],
        "PI":["Teresina","Parnaíba"],
        "SE":["Aracaju","Lagarto"],
        "RO":["Porto Velho","Ji-Paraná"],
        "TO":["Palmas","Araguaína"],
        "AC":["Rio Branco","Cruzeiro do Sul"],
        "AP":["Macapá"],
        "RR":["Boa Vista"],
    }

    for _ in range(NUM_UNIDADES_NEGOCIO):
        uf = escolher_ponderado(peso_uf)
        regiao_nome = UF_REGIAO[uf]
        tipo = escolher_ponderado(TIPOS_UNIDADE_NEGOCIO)
        cidade = random.choice(cidades_por_uf.get(uf, [uf]))
        nome = f"{tipo} {cidade} - {prefixo_seq:04d}"
        prefixo = f"{prefixo_seq:04d}-{uf}"
        rows.append({
            "id": new_uuid(),
            "prefixo": prefixo,
            "nome": nome,
            "tipo": tipo,
            "uf": uf,
            "regiao_id": reg_map[regiao_nome],
        })
        prefixo_seq += 1
    return pd.DataFrame(rows)


# ============================================================================
# 4. EAPs (eventos)
# ============================================================================

def gerar_eap(df_tipo, df_objeto, df_eap_padrao, df_unidade, df_fornecedor, df_forn_esp):
    # Índices auxiliares
    tipo_map = dict(zip(df_tipo["nome"], df_tipo["id"]))
    tipo_inv = dict(zip(df_tipo["id"], df_tipo["nome"]))
    obj_map = dict(zip(df_objeto["nome"], df_objeto["id"]))
    obj_inv = dict(zip(df_objeto["id"], df_objeto["nome"]))

    # (tipo_id, objeto_id) → eap_padrao_id
    ep_map = {
        (r["tipo_licitacao_id"], r["objeto_licitacao_id"]): r["id"]
        for _, r in df_eap_padrao.iterrows()
    }

    demandantes = df_unidade[df_unidade["pode_demandar"]]["id"].tolist()
    disec_id = df_unidade[df_unidade["prefixo"] == "DISEC"]["id"].iloc[0]
    cesup_sp_id = df_unidade[df_unidade["prefixo"] == "CESUP-SP"]["id"].iloc[0]

    # Especialidades → lista de fornecedores por objeto
    forn_por_obj = df_forn_esp.groupby("objeto_licitacao_id")["fornecedor_id"].apply(list).to_dict()

    pesos_tipo = {n: p for n, (_m, p) in TIPOS_LICITACAO.items()}
    pesos_obj = {n: p for n, (_m, p) in OBJETOS_LICITACAO.items()}

    rows = []
    counter_por_ano = {}

    for _ in range(NUM_EAPS):
        tipo_nome = escolher_ponderado(pesos_tipo)
        obj_nome = escolher_ponderado(pesos_obj)
        tipo_id = tipo_map[tipo_nome]
        obj_id = obj_map[obj_nome]
        eap_padrao_id = ep_map[(tipo_id, obj_id)]

        unidade_dem = random.choice(demandantes)
        # Ambos executam todas as modalidades; CESUP-SP concentra 90% das contratações.
        unidade_exec = cesup_sp_id if random.random() < 0.90 else disec_id

        status = escolher_ponderado(STATUS_EAP)

        # Valor estimado: log-normal por macro — patamar BB (milhões)
        # mediana ≈ e^mu ; alguns contratos grandes passam de R$ 100M
        macro = OBJETOS_LICITACAO[obj_nome][0]
        if macro in ("TI", "Engenharia"):
            val = np.random.lognormal(15.0, 1.3)   # mediana ~R$ 3.3M, cauda até centenas de M
        elif macro == "Consultoria":
            val = np.random.lognormal(13.8, 1.1)   # mediana ~R$ 980k
        elif macro in ("Facilities", "Segurança"):
            val = np.random.lognormal(14.2, 1.2)   # mediana ~R$ 1.5M (contratos plurianuais)
        elif macro == "Material":
            val = np.random.lognormal(11.5, 0.9)   # mediana ~R$ 100k (compras menores)
        else:
            val = np.random.lognormal(13.5, 1.2)   # mediana ~R$ 730k
        valor_estimado = round(max(10_000, min(val, 300_000_000)), 2)

        # Data de abertura com sazonalidade
        dt_abertura = data_aleatoria(DATA_INICIO, DATA_FIM)
        if dt_abertura.month not in (1, 2, 3, 7, 8, 9) and random.random() < 0.3:
            dt_abertura = data_aleatoria(DATA_INICIO, DATA_FIM)

        # Percorrer etapas: planejado (só prazos padrão) vs realizado (com desvio)
        etapas_def = etapas_para(tipo_nome, macro)
        prazo_planejado = sum(prazo for _n, prazo, _d, _r in etapas_def)
        dt_atual = dt_abertura
        for nome, prazo, desvio, _resp in etapas_def:
            dt_atual = adicionar_dias(dt_atual, prazo, desvio, minimo=1)
        dt_ultima = dt_atual

        # Intercorrência (se houver, atrasa só o realizado)
        if tipo_nome == "Licitação":
            prob = 0.22 + (0.10 if valor_estimado > 1_000_000 else 0)
            tipos_int = INTERCORRENCIAS_LICITACAO
        elif tipo_nome == "Contratação Direta":
            prob = 0.10
            tipos_int = INTERCORRENCIAS_DIRETA
        else:
            prob = 0.08
            tipos_int = INTERCORRENCIAS_INEXIGIBILIDADE

        tem_int = random.random() < prob
        tipo_int = random.choice(tipos_int) if tem_int else None
        if tem_int:
            dt_ultima += timedelta(days=random.randint(10, 60))

        prazo_total = (dt_ultima - dt_abertura).days  # realizado
        dias_atraso_eap = prazo_total - prazo_planejado
        atrasou = dias_atraso_eap > 0
        dt_assinatura = dt_ultima
        if status != "Concluído":
            dt_assinatura = None
            prazo_total = None
            dias_atraso_eap = None
            atrasou = None

        ano = dt_abertura.year
        counter_por_ano[ano] = counter_por_ano.get(ano, 0) + 1
        numero = f"EAP-{ano}-{counter_por_ano[ano]:05d}"

        rows.append({
            "id": new_uuid(),
            "numero": numero,
            "eap_padrao_id": eap_padrao_id,
            "unidade_demandante_id": unidade_dem,
            "unidade_executante_id": unidade_exec,
            "objeto_resumido": f"Contratação de {obj_nome.lower()} para {df_unidade[df_unidade['id']==unidade_dem]['prefixo'].iloc[0]}",
            "dt_abertura": dt_abertura.strftime("%Y-%m-%d"),
            "dt_assinatura": dt_assinatura.strftime("%Y-%m-%d") if dt_assinatura else None,
            "valor_estimado": valor_estimado,
            "prazo_total_dias": prazo_total,
            "prazo_planejado_dias": prazo_planejado,
            "dias_atraso_eap": dias_atraso_eap,
            "atrasou": atrasou,
            "status": status,
            "urgencia": random.choices(["Normal","Urgente","Emergencial"],
                                       weights=[0.75,0.20,0.05])[0],
            "complexidade": random.choices(["Baixa","Média","Alta"],
                                           weights=[0.30,0.50,0.20])[0],
            "tem_intercorrencia": tem_int,
            "tipo_intercorrencia": tipo_int,
            # guardamos para próximos passos (não vão ao CSV final):
            "_tipo_nome": tipo_nome,
            "_objeto_nome": obj_nome,
            "_macro": macro,
            "_dt_abertura_dt": dt_abertura,
            "_etapas_def": etapas_def,
        })

    return pd.DataFrame(rows)


# ============================================================================
# 5. ETAPAS REAIS (etapa_eap)
# ============================================================================

def gerar_etapa_eap(df_eap, df_etapa_padrao, df_resp):
    resp_map = dict(zip(df_resp["nome"], df_resp["id"]))

    # (eap_padrao_id, sequencia) → etapa_padrao_id
    ep_etapas = {
        (r["eap_padrao_id"], r["sequencia"]): r["id"]
        for _, r in df_etapa_padrao.iterrows()
    }

    rows = []
    for _, eap in df_eap.iterrows():
        etapas_def = eap["_etapas_def"]
        num = len(etapas_def)

        if eap["status"] == "Concluído":
            limite = num
        elif eap["status"] == "Em Andamento":
            limite = random.randint(max(1, num // 3), num - 1)
        elif eap["status"] == "Cancelado":
            limite = random.randint(1, max(1, num // 2))
        else:  # Suspenso
            limite = random.randint(max(1, num // 3), max(2, num * 2 // 3))

        dt_atual = eap["_dt_abertura_dt"]
        for j, (nome, prazo, desvio, resp) in enumerate(etapas_def, start=1):
            etapa_padrao_id = ep_etapas.get((eap["eap_padrao_id"], j))

            if j <= limite:
                dt_fim = adicionar_dias(dt_atual, prazo, desvio, minimo=1)
                duracao = (dt_fim - dt_atual).days
                status_et = "Concluída"
                dt_i = dt_atual.strftime("%Y-%m-%d")
                dt_f = dt_fim.strftime("%Y-%m-%d")
                dt_atual = dt_fim
            elif j == limite + 1 and eap["status"] == "Em Andamento":
                dt_i = dt_atual.strftime("%Y-%m-%d")
                dt_f = None
                duracao = None
                status_et = "Em Andamento"
            else:
                dt_i = None
                dt_f = None
                duracao = None
                status_et = "Não Realizada" if eap["status"] == "Cancelado" else "Pendente"

            rows.append({
                "id": new_uuid(),
                "eap_id": eap["id"],
                "etapa_padrao_id": etapa_padrao_id,
                "sequencia": j,
                "nome": nome,
                "dt_inicio": dt_i,
                "dt_fim": dt_f,
                "duracao_dias": duracao,
                "status_etapa": status_et,
                "responsavel_tipo_id": resp_map[resp],
            })
    return pd.DataFrame(rows)


# ============================================================================
# 6. PARTICIPANTES
# ============================================================================

def gerar_participante(df_eap, df_fornecedor, df_forn_esp):
    forn_ids = df_fornecedor["id"].tolist()
    forn_por_obj = df_forn_esp.groupby("objeto_licitacao_id")["fornecedor_id"].apply(list).to_dict()
    forn_especialidade_por_forn = df_forn_esp.groupby("fornecedor_id")["objeto_licitacao_id"].apply(set).to_dict()

    # categoria_macro concentrado → poucos fornecedores dominantes
    concentrados = {"Segurança Patrimonial", "TI - Licenciamento", "Seguros",
                    "Consultoria - Jurídica", "Facilities - Vigilância"}

    rows = []
    ganhadores = {}  # eap_id → fornecedor_id vencedor

    for _, eap in df_eap.iterrows():
        tipo_nome = eap["_tipo_nome"]
        obj_nome = eap["_objeto_nome"]

        if tipo_nome == "Licitação":
            n_part = max(1, int(np.random.poisson(5)) + 1)
        elif tipo_nome == "Contratação Direta":
            n_part = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
        else:
            n_part = 1

        # fornecedores elegíveis
        elegiveis = forn_por_obj.get(
            next((oid for oid, _ in []), None), []
        )
        # (acima retorna vazio; buscamos por obj_nome → id via df_eap não expõe, fazemos no df_forn_esp)
        # Mais simples: usar todos, priorizando os compatíveis com o objeto
        compat = [f for f in forn_ids
                  if any(o == eap.get("_objeto_nome_id") for o in forn_especialidade_por_forn.get(f, set()))]

        pool = compat if compat else forn_ids
        pool = random.sample(pool, min(n_part, len(pool)))

        # vencedor (com concentração em certas categorias)
        if obj_nome in concentrados and len(pool) >= 2:
            vencedor = pool[0]  # o primeiro é privilegiado
        else:
            vencedor = pool[0] if pool else None
        if eap["status"] == "Concluído" and vencedor:
            ganhadores[eap["id"]] = vencedor

        for k, f_id in enumerate(pool):
            if f_id == vencedor:
                fator = np.random.uniform(0.70, 0.95)
            else:
                fator = np.random.uniform(0.75, 1.10)
            rows.append({
                "id": new_uuid(),
                "eap_id": eap["id"],
                "fornecedor_id": f_id,
                "valor_proposta": round(eap["valor_estimado"] * fator, 2),
                "classificacao": k + 1,
                "vencedor": (f_id == vencedor),
                "situacao": "Habilitado" if random.random() < 0.85 else "Inabilitado",
            })

    return pd.DataFrame(rows), ganhadores


# ============================================================================
# 7. CONTRATOS
# ============================================================================

def gerar_contrato(df_eap, df_fornecedor, ganhadores):
    forn_notas = dict(zip(df_fornecedor["id"], df_fornecedor["nota_desempenho"]))
    forn_portes = dict(zip(df_fornecedor["id"], df_fornecedor["porte"]))

    rows = []
    counter_por_ano = {}

    for _, eap in df_eap.iterrows():
        if eap["status"] != "Concluído":
            continue
        forn_id = ganhadores.get(eap["id"])
        if not forn_id:
            continue

        dt_ass = datetime.strptime(eap["dt_assinatura"], "%Y-%m-%d")
        valor_est = eap["valor_estimado"]
        macro = eap["_macro"]

        # Desconto
        desconto = np.random.uniform(0.05, 0.30) if random.random() < 0.5 else np.random.uniform(0, 0.15)
        valor_contratado = round(valor_est * (1 - desconto), 2)

        # Vigência: pode ser expressa em dias, meses ou anos (mais realista)
        #   Engenharia/Facilities: normalmente em meses/anos
        #   TI/Consultoria: meses/anos
        #   Eventos pontuais (compras, material): dias
        if macro == "Material":
            # Compras de material: alguns dias (entrega)
            vig_unidade = "dias"
            vig_valor = random.choices([15, 30, 60, 90], weights=[0.2, 0.4, 0.3, 0.1])[0]
            vig_meses_equiv = vig_valor / 30
        elif macro == "Engenharia":
            if random.random() < 0.2:
                vig_unidade = "dias"
                vig_valor = random.choices([90, 180, 270], weights=[0.3, 0.4, 0.3])[0]
                vig_meses_equiv = vig_valor / 30
            else:
                vig_unidade = "meses"
                vig_valor = random.choices([6, 12, 18, 24], weights=[0.1, 0.3, 0.4, 0.2])[0]
                vig_meses_equiv = vig_valor
        elif macro in ("Facilities", "Segurança"):
            # Contratos plurianuais — comum expressar em anos
            if random.random() < 0.4:
                vig_unidade = "anos"
                vig_valor = random.choices([1, 2, 3, 5], weights=[0.3, 0.4, 0.2, 0.1])[0]
                vig_meses_equiv = vig_valor * 12
            else:
                vig_unidade = "meses"
                vig_valor = random.choices([12, 24, 36, 60], weights=[0.3, 0.4, 0.2, 0.1])[0]
                vig_meses_equiv = vig_valor
        else:  # TI, Consultoria, Logística, Seguros...
            if random.random() < 0.25:
                vig_unidade = "anos"
                vig_valor = random.choices([1, 2, 3], weights=[0.5, 0.3, 0.2])[0]
                vig_meses_equiv = vig_valor * 12
            else:
                vig_unidade = "meses"
                vig_valor = random.choices([6, 12, 24, 36], weights=[0.2, 0.4, 0.3, 0.1])[0]
                vig_meses_equiv = vig_valor
        dt_vig_fim = dt_ass + timedelta(days=int(vig_meses_equiv * 30))
        # vig_meses mantido p/ compatibilidade com as regras de aditivo/rescisão
        vig = int(vig_meses_equiv)

        nota = forn_notas.get(forn_id, 7.5)
        porte = forn_portes.get(forn_id, "Médio")

        # Aditivos
        prob_adit = 0.30 + (0.15 if vig >= 18 else 0) + \
                    (0.10 if valor_contratado > 1_000_000 else 0) + \
                    (0.10 if nota < 6.0 else 0)
        num_adit, val_adit = 0, 0.0
        if random.random() < prob_adit:
            num_adit = random.choices([1, 2, 3, 4], weights=[0.5, 0.3, 0.15, 0.05])[0]
            for _ in range(num_adit):
                if random.random() < 0.4:  # Acréscimo
                    val_adit += valor_contratado * np.random.uniform(0.05, 0.25)
                elif random.random() < 0.3:  # Supressão
                    val_adit -= valor_contratado * np.random.uniform(0.03, 0.15)

        # Rescisão
        prob_res = 0.08 + (0.25 if nota < 5 else 0.10 if nota < 6.5 else 0) + \
                   (0.05 if porte in ("ME", "EPP") else 0) + \
                   (0.05 if valor_contratado > 2_000_000 else 0) + \
                   (0.10 if num_adit >= 3 else 0) + \
                   (0.05 if eap["_tipo_nome"] == "Inexigibilidade" else 0)
        teve_res = random.random() < prob_res
        motivo_res, dt_res = None, None
        if teve_res:
            motivo_res = random.choice(MOTIVOS_RESCISAO)
            dias_vig = (dt_vig_fim - dt_ass).days
            dt_res = dt_ass + timedelta(days=random.randint(int(dias_vig * 0.2), int(dias_vig * 0.8)))

        # Penalidades
        prob_pen = 0.12 + (0.20 if nota < 6 else 0) + \
                   (0.30 if teve_res else 0) + (0.10 if num_adit >= 2 else 0)
        num_pen = 0
        if random.random() < prob_pen:
            num_pen = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]

        # Atrasos
        prob_atr = 0.15 + (0.20 if nota < 6 else 0) + (0.10 if macro == "Engenharia" else 0)
        teve_atr = random.random() < prob_atr
        dias_atr = random.randint(5, 90) if teve_atr else 0

        ano = dt_ass.year
        counter_por_ano[ano] = counter_por_ano.get(ano, 0) + 1
        numero = f"CT-{ano}-{counter_por_ano[ano]:05d}"

        rows.append({
            "id": new_uuid(),
            "numero": numero,
            "eap_id": eap["id"],
            "fornecedor_id": forn_id,
            "valor_contratado": valor_contratado,
            "dt_assinatura": eap["dt_assinatura"],
            "dt_vigencia_fim": dt_vig_fim.strftime("%Y-%m-%d"),
            "vigencia_valor": vig_valor,
            "vigencia_unidade": vig_unidade,
            "vigencia_meses_equiv": vig,
            "num_aditivos": num_adit,
            "aditivos_valor_total": round(val_adit, 2),
            "teve_rescisao": teve_res,
            "motivo_rescisao": motivo_res,
            "dt_rescisao": dt_res.strftime("%Y-%m-%d") if dt_res else None,
            "num_penalidades": num_pen,
            "teve_atraso": teve_atr,
            "dias_atraso_total": dias_atr,
            "nota_fornecedor": nota,
        })
    return pd.DataFrame(rows)


# ============================================================================
# 8. CONTRATO × UNIDADE_NEGOCIO ATENDIDA (N:M)
# ============================================================================

def gerar_contrato_unidade_atendida(df_contrato, df_eap, df_un_neg, df_forn_regiao, df_regiao):
    """
    Cada contrato atende 1+ unidades de negócio. Distribuição:
      - 70%: 1-3 unidades (local)
      - 20%: 10-100 unidades (regional)
      - 8%:  200-1000 (multi-regional)
      - 2%:  todas (~5000, nacional)

    Respeita as regiões que o fornecedor atende.
    """
    reg_nome = dict(zip(df_regiao["id"], df_regiao["nome"]))
    un_por_regiao_nome = df_un_neg.copy()
    un_por_regiao_nome["regiao_nome"] = un_por_regiao_nome["regiao_id"].map(reg_nome)
    un_por_reg = un_por_regiao_nome.groupby("regiao_nome")["id"].apply(list).to_dict()
    todas_unidades = df_un_neg["id"].tolist()

    forn_regioes = df_forn_regiao.groupby("fornecedor_id")["regiao_id"].apply(set).to_dict()
    regiao_id_to_nome = reg_nome

    eap_dict = df_eap.set_index("id").to_dict("index")

    rows = []
    for _, ct in df_contrato.iterrows():
        forn_id = ct["fornecedor_id"]
        regs_forn = forn_regioes.get(forn_id, set())
        regs_forn_nomes = {regiao_id_to_nome[r] for r in regs_forn}

        # Pool de unidades elegíveis (regiões que o fornecedor atende)
        if "Nacional" in regs_forn_nomes:
            pool = todas_unidades
        else:
            pool = []
            for reg in regs_forn_nomes:
                pool.extend(un_por_reg.get(reg, []))
            if not pool:
                pool = todas_unidades  # fallback

        # Determinar quantidade por bucket de abrangência
        r = random.random()
        if r < 0.70:
            qtd = random.randint(1, min(3, len(pool)))
        elif r < 0.90:
            qtd = random.randint(10, min(100, len(pool)))
        elif r < 0.98:
            qtd = random.randint(200, min(1000, len(pool)))
        else:
            qtd = len(pool)  # nacional / cobertura total do pool

        if qtd >= len(pool):
            escolhidas = pool
        else:
            escolhidas = random.sample(pool, qtd)

        for un_id in escolhidas:
            rows.append({
                "contrato_id": ct["id"],
                "unidade_negocio_id": un_id,
            })
    return pd.DataFrame(rows)


# ============================================================================
# DENORMALIZAÇÃO: adiciona colunas-texto ao lado dos UUIDs
# ============================================================================

def _reorder(df, ordered_cols):
    """Coloca ordered_cols primeiro; resto vem depois na ordem original."""
    rest = [c for c in df.columns if c not in ordered_cols]
    return df[[c for c in ordered_cols if c in df.columns] + rest]


def denormalizar(tabelas):
    """Adiciona colunas snapshot (nome/prefixo/razão) ao lado de cada UUID FK."""
    tl   = tabelas["tipo_licitacao"].set_index("id")
    ol   = tabelas["objeto_licitacao"].set_index("id")
    un   = tabelas["unidade"].set_index("id")
    rt   = tabelas["responsavel_tipo"].set_index("id")
    forn = tabelas["fornecedor"].set_index("id")

    # eap_padrao
    ep = tabelas["eap_padrao"]
    ep["tipo_licitacao_nome"]   = ep["tipo_licitacao_id"].map(tl["nome"])
    ep["modalidade"]            = ep["tipo_licitacao_id"].map(tl["modalidade"])
    ep["objeto_licitacao_nome"] = ep["objeto_licitacao_id"].map(ol["nome"])
    tabelas["eap_padrao"] = _reorder(ep, [
        "id", "nome",
        "tipo_licitacao_id", "tipo_licitacao_nome", "modalidade",
        "objeto_licitacao_id", "objeto_licitacao_nome",
    ])

    ep_lookup = tabelas["eap_padrao"].set_index("id")

    # etapa_padrao
    etp = tabelas["etapa_padrao"]
    etp["eap_padrao_nome"] = etp["eap_padrao_id"].map(ep_lookup["nome"])
    etp["responsavel"]     = etp["responsavel_tipo_id"].map(rt["nome"])
    tabelas["etapa_padrao"] = _reorder(etp, [
        "id", "eap_padrao_id", "eap_padrao_nome", "sequencia", "nome",
        "prazo_padrao_dias", "prazo_desvio_dias",
        "responsavel_tipo_id", "responsavel",
    ])

    # fornecedor_especialidade
    fe = tabelas["fornecedor_especialidade"]
    fe["fornecedor_razao_social"] = fe["fornecedor_id"].map(forn["razao_social"])
    fe["objeto_licitacao_nome"]   = fe["objeto_licitacao_id"].map(ol["nome"])
    tabelas["fornecedor_especialidade"] = _reorder(fe, [
        "fornecedor_id", "fornecedor_razao_social",
        "objeto_licitacao_id", "objeto_licitacao_nome", "principal",
    ])

    # eap
    eap = tabelas["eap"]
    eap["eap_padrao_nome"]            = eap["eap_padrao_id"].map(ep_lookup["nome"])
    eap["tipo_licitacao_nome"]        = eap["eap_padrao_id"].map(ep_lookup["tipo_licitacao_nome"])
    eap["objeto_licitacao_nome"]      = eap["eap_padrao_id"].map(ep_lookup["objeto_licitacao_nome"])
    eap["modalidade"]                 = eap["eap_padrao_id"].map(ep_lookup["modalidade"])
    eap["unidade_demandante_prefixo"] = eap["unidade_demandante_id"].map(un["prefixo"])
    eap["unidade_executante_prefixo"] = eap["unidade_executante_id"].map(un["prefixo"])
    tabelas["eap"] = _reorder(eap, [
        "id", "numero",
        "eap_padrao_id", "eap_padrao_nome",
        "tipo_licitacao_nome", "objeto_licitacao_nome", "modalidade",
        "unidade_demandante_id", "unidade_demandante_prefixo",
        "unidade_executante_id", "unidade_executante_prefixo",
        "objeto_resumido", "dt_abertura", "dt_assinatura",
        "valor_estimado",
        "prazo_total_dias", "prazo_planejado_dias", "dias_atraso_eap", "atrasou",
        "status", "urgencia", "complexidade",
        "tem_intercorrencia", "tipo_intercorrencia",
    ])

    eap_lookup = tabelas["eap"].set_index("id")

    # etapa_eap
    ee = tabelas["etapa_eap"]
    ee["eap_numero"]  = ee["eap_id"].map(eap_lookup["numero"])
    ee["responsavel"] = ee["responsavel_tipo_id"].map(rt["nome"])
    tabelas["etapa_eap"] = _reorder(ee, [
        "id",
        "eap_id", "eap_numero",
        "etapa_padrao_id", "sequencia", "nome",
        "dt_inicio", "dt_fim", "duracao_dias", "status_etapa",
        "responsavel_tipo_id", "responsavel",
    ])

    # participante
    p = tabelas["participante"]
    p["eap_numero"]              = p["eap_id"].map(eap_lookup["numero"])
    p["fornecedor_razao_social"] = p["fornecedor_id"].map(forn["razao_social"])
    tabelas["participante"] = _reorder(p, [
        "id",
        "eap_id", "eap_numero",
        "fornecedor_id", "fornecedor_razao_social",
        "valor_proposta", "classificacao", "vencedor", "situacao",
    ])

    # contrato
    c = tabelas["contrato"]
    c["eap_numero"]              = c["eap_id"].map(eap_lookup["numero"])
    c["fornecedor_razao_social"] = c["fornecedor_id"].map(forn["razao_social"])
    c["porte_fornecedor"]        = c["fornecedor_id"].map(forn["porte"])
    tabelas["contrato"] = _reorder(c, [
        "id", "numero",
        "eap_id", "eap_numero",
        "fornecedor_id", "fornecedor_razao_social", "porte_fornecedor",
        "valor_contratado", "dt_assinatura", "dt_vigencia_fim",
        "vigencia_valor", "vigencia_unidade", "vigencia_meses_equiv",
        "num_aditivos", "aditivos_valor_total",
        "teve_rescisao", "motivo_rescisao", "dt_rescisao",
        "num_penalidades", "teve_atraso", "dias_atraso_total",
        "nota_fornecedor",
    ])

    # regiao (lookup — já tem só id+nome, nada a fazer)

    # fornecedor_regiao
    if "fornecedor_regiao" in tabelas:
        reg = tabelas["regiao"].set_index("id")
        fr = tabelas["fornecedor_regiao"]
        fr["fornecedor_razao_social"] = fr["fornecedor_id"].map(forn["razao_social"])
        fr["regiao_nome"]             = fr["regiao_id"].map(reg["nome"])
        tabelas["fornecedor_regiao"] = _reorder(fr, [
            "fornecedor_id", "fornecedor_razao_social",
            "regiao_id", "regiao_nome",
        ])

    # unidade_negocio
    if "unidade_negocio" in tabelas:
        reg = tabelas["regiao"].set_index("id")
        un_neg = tabelas["unidade_negocio"]
        un_neg["regiao_nome"] = un_neg["regiao_id"].map(reg["nome"])
        tabelas["unidade_negocio"] = _reorder(un_neg, [
            "id", "prefixo", "nome", "tipo", "uf",
            "regiao_id", "regiao_nome",
        ])

    # contrato_unidade_atendida
    if "contrato_unidade_atendida" in tabelas:
        un_neg_lookup = tabelas["unidade_negocio"].set_index("id")
        ct_lookup = tabelas["contrato"].set_index("id")
        cua = tabelas["contrato_unidade_atendida"]
        cua["contrato_numero"]        = cua["contrato_id"].map(ct_lookup["numero"])
        cua["unidade_negocio_prefixo"] = cua["unidade_negocio_id"].map(un_neg_lookup["prefixo"])
        tabelas["contrato_unidade_atendida"] = _reorder(cua, [
            "contrato_id", "contrato_numero",
            "unidade_negocio_id", "unidade_negocio_prefixo",
        ])

    return tabelas


# ============================================================================
# schema.sql
# ============================================================================

SCHEMA_SQL = """-- ============================================================
-- HyperCopa DISEC 2026 — Schema PostgreSQL (dados sintéticos)
-- Gerado por gerar_dados_postgres.py
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -------- LOOKUPS --------

CREATE TABLE tipo_licitacao (
    id          UUID PRIMARY KEY,
    nome        TEXT NOT NULL UNIQUE,
    modalidade  TEXT NOT NULL
);

CREATE TABLE objeto_licitacao (
    id               UUID PRIMARY KEY,
    nome             TEXT NOT NULL UNIQUE,
    categoria_macro  TEXT NOT NULL
);

CREATE TABLE unidade (
    id             UUID PRIMARY KEY,
    prefixo        TEXT NOT NULL UNIQUE,
    nome           TEXT NOT NULL,
    pode_demandar  BOOLEAN NOT NULL DEFAULT TRUE,
    pode_executar  BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE responsavel_tipo (
    id   UUID PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE regiao (
    id   UUID PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE
);

-- -------- TEMPLATES --------

CREATE TABLE eap_padrao (
    id                      UUID PRIMARY KEY,
    nome                    TEXT NOT NULL,
    tipo_licitacao_id       UUID NOT NULL REFERENCES tipo_licitacao(id),
    tipo_licitacao_nome     TEXT,  -- snapshot
    modalidade              TEXT,  -- snapshot
    objeto_licitacao_id     UUID NOT NULL REFERENCES objeto_licitacao(id),
    objeto_licitacao_nome   TEXT,  -- snapshot
    UNIQUE (tipo_licitacao_id, objeto_licitacao_id)
);

CREATE TABLE etapa_padrao (
    id                    UUID PRIMARY KEY,
    eap_padrao_id         UUID NOT NULL REFERENCES eap_padrao(id) ON DELETE CASCADE,
    eap_padrao_nome       TEXT,  -- snapshot
    sequencia             INT  NOT NULL,
    nome                  TEXT NOT NULL,
    prazo_padrao_dias     INT  NOT NULL,
    prazo_desvio_dias     INT  NOT NULL,
    responsavel_tipo_id   UUID NOT NULL REFERENCES responsavel_tipo(id),
    responsavel           TEXT,  -- snapshot
    UNIQUE (eap_padrao_id, sequencia)
);

-- -------- FORNECEDOR --------

CREATE TABLE fornecedor (
    id                         UUID PRIMARY KEY,
    razao_social               TEXT NOT NULL,
    cnpj                       TEXT NOT NULL UNIQUE,
    uf                         CHAR(2) NOT NULL,
    porte                      TEXT NOT NULL,
    nota_desempenho            NUMERIC(3,1),
    situacao_sicaf             TEXT,
    dt_cadastro                DATE,
    -- Qualificação econômico-financeira (Lei 14.133/21 art. 69)
    patrimonio_liquido         NUMERIC(16,2),
    capital_social             NUMERIC(16,2),
    faturamento_anual          NUMERIC(16,2),
    indice_liquidez_corrente   NUMERIC(5,2),
    indice_liquidez_geral      NUMERIC(5,2),
    indice_solvencia_geral     NUMERIC(5,2)
);

CREATE TABLE fornecedor_especialidade (
    fornecedor_id             UUID NOT NULL REFERENCES fornecedor(id) ON DELETE CASCADE,
    fornecedor_razao_social   TEXT,  -- snapshot
    objeto_licitacao_id       UUID NOT NULL REFERENCES objeto_licitacao(id),
    objeto_licitacao_nome     TEXT,  -- snapshot
    principal                 BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (fornecedor_id, objeto_licitacao_id)
);

CREATE TABLE fornecedor_regiao (
    fornecedor_id             UUID NOT NULL REFERENCES fornecedor(id) ON DELETE CASCADE,
    fornecedor_razao_social   TEXT,  -- snapshot
    regiao_id                 UUID NOT NULL REFERENCES regiao(id),
    regiao_nome               TEXT,  -- snapshot
    PRIMARY KEY (fornecedor_id, regiao_id)
);

-- -------- UNIDADES DE NEGÓCIO (agências, postos, ~5000 unidades) --------

CREATE TABLE unidade_negocio (
    id           UUID PRIMARY KEY,
    prefixo      TEXT NOT NULL UNIQUE,
    nome         TEXT NOT NULL,
    tipo         TEXT NOT NULL,
    uf           CHAR(2) NOT NULL,
    regiao_id    UUID NOT NULL REFERENCES regiao(id),
    regiao_nome  TEXT  -- snapshot
);

-- -------- EVENTOS --------

CREATE TABLE eap (
    id                          UUID PRIMARY KEY,
    numero                      TEXT NOT NULL UNIQUE,
    eap_padrao_id               UUID NOT NULL REFERENCES eap_padrao(id),
    eap_padrao_nome             TEXT,  -- snapshot
    tipo_licitacao_nome         TEXT,  -- snapshot
    objeto_licitacao_nome       TEXT,  -- snapshot
    modalidade                  TEXT,  -- snapshot
    unidade_demandante_id       UUID NOT NULL REFERENCES unidade(id),
    unidade_demandante_prefixo  TEXT,  -- snapshot
    unidade_executante_id       UUID NOT NULL REFERENCES unidade(id),
    unidade_executante_prefixo  TEXT,  -- snapshot
    objeto_resumido             TEXT,
    dt_abertura                 DATE NOT NULL,
    dt_assinatura               DATE,
    valor_estimado              NUMERIC(14,2) NOT NULL,
    prazo_total_dias            INT,
    prazo_planejado_dias        INT,
    dias_atraso_eap             INT,
    atrasou                     BOOLEAN,
    status                      TEXT NOT NULL,
    urgencia                    TEXT NOT NULL,
    complexidade                TEXT NOT NULL,
    tem_intercorrencia          BOOLEAN NOT NULL DEFAULT FALSE,
    tipo_intercorrencia         TEXT
);

CREATE TABLE etapa_eap (
    id                   UUID PRIMARY KEY,
    eap_id               UUID NOT NULL REFERENCES eap(id) ON DELETE CASCADE,
    eap_numero           TEXT,  -- snapshot
    etapa_padrao_id      UUID REFERENCES etapa_padrao(id),
    sequencia            INT  NOT NULL,
    nome                 TEXT NOT NULL,
    dt_inicio            DATE,
    dt_fim               DATE,
    duracao_dias         INT,
    status_etapa         TEXT NOT NULL,
    responsavel_tipo_id  UUID NOT NULL REFERENCES responsavel_tipo(id),
    responsavel          TEXT,  -- snapshot
    UNIQUE (eap_id, sequencia)
);

CREATE TABLE participante (
    id                      UUID PRIMARY KEY,
    eap_id                  UUID NOT NULL REFERENCES eap(id) ON DELETE CASCADE,
    eap_numero              TEXT,  -- snapshot
    fornecedor_id           UUID NOT NULL REFERENCES fornecedor(id),
    fornecedor_razao_social TEXT,  -- snapshot
    valor_proposta          NUMERIC(14,2) NOT NULL,
    classificacao           INT NOT NULL,
    vencedor                BOOLEAN NOT NULL DEFAULT FALSE,
    situacao                TEXT NOT NULL,
    UNIQUE (eap_id, fornecedor_id)
);

CREATE TABLE contrato (
    id                        UUID PRIMARY KEY,
    numero                    TEXT NOT NULL UNIQUE,
    eap_id                    UUID NOT NULL UNIQUE REFERENCES eap(id),
    eap_numero                TEXT,  -- snapshot
    fornecedor_id             UUID NOT NULL REFERENCES fornecedor(id),
    fornecedor_razao_social   TEXT,  -- snapshot
    porte_fornecedor          TEXT,  -- snapshot
    valor_contratado          NUMERIC(16,2) NOT NULL,
    dt_assinatura             DATE NOT NULL,
    dt_vigencia_fim           DATE NOT NULL,
    -- Vigência pode ser expressa em dias, meses ou anos
    vigencia_valor            INT  NOT NULL,
    vigencia_unidade          TEXT NOT NULL CHECK (vigencia_unidade IN ('dias','meses','anos')),
    vigencia_meses_equiv      INT  NOT NULL,  -- normalização p/ cálculos
    num_aditivos              INT  NOT NULL DEFAULT 0,
    aditivos_valor_total      NUMERIC(16,2) NOT NULL DEFAULT 0,
    teve_rescisao             BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_rescisao           TEXT,
    dt_rescisao               DATE,
    num_penalidades           INT  NOT NULL DEFAULT 0,
    teve_atraso               BOOLEAN NOT NULL DEFAULT FALSE,
    dias_atraso_total         INT  NOT NULL DEFAULT 0,
    nota_fornecedor           NUMERIC(3,1)
);

CREATE TABLE contrato_unidade_atendida (
    contrato_id             UUID NOT NULL REFERENCES contrato(id) ON DELETE CASCADE,
    contrato_numero         TEXT,  -- snapshot
    unidade_negocio_id      UUID NOT NULL REFERENCES unidade_negocio(id),
    unidade_negocio_prefixo TEXT,  -- snapshot
    PRIMARY KEY (contrato_id, unidade_negocio_id)
);

-- -------- ÍNDICES --------

CREATE INDEX idx_eap_padrao_tipo       ON eap_padrao(tipo_licitacao_id);
CREATE INDEX idx_eap_padrao_objeto     ON eap_padrao(objeto_licitacao_id);
CREATE INDEX idx_etapa_padrao_ep       ON etapa_padrao(eap_padrao_id);
CREATE INDEX idx_forn_esp_obj          ON fornecedor_especialidade(objeto_licitacao_id);
CREATE INDEX idx_eap_padrao            ON eap(eap_padrao_id);
CREATE INDEX idx_eap_unidade_dem       ON eap(unidade_demandante_id);
CREATE INDEX idx_eap_unidade_exec      ON eap(unidade_executante_id);
CREATE INDEX idx_eap_dt_abertura       ON eap(dt_abertura);
CREATE INDEX idx_eap_status            ON eap(status);
CREATE INDEX idx_etapa_eap_eap         ON etapa_eap(eap_id);
CREATE INDEX idx_etapa_eap_padrao      ON etapa_eap(etapa_padrao_id);
CREATE INDEX idx_participante_eap      ON participante(eap_id);
CREATE INDEX idx_participante_forn     ON participante(fornecedor_id);
CREATE INDEX idx_contrato_forn         ON contrato(fornecedor_id);
CREATE INDEX idx_contrato_dt_ass       ON contrato(dt_assinatura);
CREATE INDEX idx_forn_regiao_reg       ON fornecedor_regiao(regiao_id);
CREATE INDEX idx_un_neg_regiao         ON unidade_negocio(regiao_id);
CREATE INDEX idx_un_neg_uf             ON unidade_negocio(uf);
CREATE INDEX idx_ct_un_contrato        ON contrato_unidade_atendida(contrato_id);
CREATE INDEX idx_ct_un_unidade         ON contrato_unidade_atendida(unidade_negocio_id);

-- -------- CARGA (uso típico — respeita dependências de FK) --------
-- \\copy tipo_licitacao              FROM 'tipo_licitacao.csv'              CSV HEADER;
-- \\copy objeto_licitacao            FROM 'objeto_licitacao.csv'            CSV HEADER;
-- \\copy unidade                     FROM 'unidade.csv'                     CSV HEADER;
-- \\copy responsavel_tipo            FROM 'responsavel_tipo.csv'            CSV HEADER;
-- \\copy regiao                      FROM 'regiao.csv'                      CSV HEADER;
-- \\copy eap_padrao                  FROM 'eap_padrao.csv'                  CSV HEADER;
-- \\copy etapa_padrao                FROM 'etapa_padrao.csv'                CSV HEADER;
-- \\copy fornecedor                  FROM 'fornecedor.csv'                  CSV HEADER;
-- \\copy fornecedor_especialidade    FROM 'fornecedor_especialidade.csv'    CSV HEADER;
-- \\copy fornecedor_regiao           FROM 'fornecedor_regiao.csv'           CSV HEADER;
-- \\copy unidade_negocio             FROM 'unidade_negocio.csv'             CSV HEADER;
-- \\copy eap                         FROM 'eap.csv'                         CSV HEADER;
-- \\copy etapa_eap                   FROM 'etapa_eap.csv'                   CSV HEADER;
-- \\copy participante                FROM 'participante.csv'                CSV HEADER;
-- \\copy contrato                    FROM 'contrato.csv'                    CSV HEADER;
-- \\copy contrato_unidade_atendida   FROM 'contrato_unidade_atendida.csv'   CSV HEADER;
"""


# ============================================================================
# MAIN
# ============================================================================

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    t_total = time.time()
    banner()

    TOTAL = 10

    # ------------------------------------------------------------------
    t0 = fase(1, TOTAL, "LOOKUPS",
              "Tabelas de referência (enums normalizados). Evita repetir strings "
              "e garante consistência referencial.",
              "tipo_licitacao, objeto_licitacao, unidade, responsavel_tipo, regiao")
    passo("Gerando tipos de licitação (Licitação / Contratação Direta / Inexigibilidade)...")
    df_tipo = gerar_tipo_licitacao()
    passo("Gerando objetos (17 tipos de suprimento: TI, Engenharia, Facilities, ...)...")
    df_obj = gerar_objeto_licitacao()
    passo("Gerando unidades organizacionais (demandantes e executantes)...")
    df_uni = gerar_unidade()
    executantes = df_uni[df_uni["pode_executar"]]["prefixo"].tolist()
    stat("Executantes cadastradas:", ", ".join(executantes))
    passo("Gerando papéis (Equipe Técnica, Pregoeiro, Gestor, Autoridade Competente)...")
    df_resp = gerar_responsavel_tipo()
    passo("Gerando regiões brasileiras (+ Nacional)...")
    df_regiao = gerar_regiao()
    stat("Regiões:", ", ".join(df_regiao["nome"].tolist()))
    n_lookup = len(df_tipo) + len(df_obj) + len(df_uni) + len(df_resp) + len(df_regiao)
    fase_fim(t0, n_lookup, "5 tabelas")

    # ------------------------------------------------------------------
    t0 = fase(2, TOTAL, "TEMPLATES (EAP Padrão + Etapas Padrão)",
              "Para cada combinação tipo×objeto criamos uma EAP Padrão com suas etapas. "
              "Engenharia ganha 'Aprovação de Projeto', TI ganha 'Prova de Conceito'. "
              "Licitação usa 3 etapas reais da Lei 14.133/21: Habilitação Jurídica, "
              "Qualificação Técnica, Qualificação Econômico-Financeira.",
              "eap_padrao (templates) + etapa_padrao (etapas do template)")
    passo(f"Cruzando {len(df_tipo)} tipos × {len(df_obj)} objetos = {len(df_tipo)*len(df_obj)} templates...")
    df_ep, df_etp = gerar_eap_padrao_e_etapas(df_tipo, df_obj, df_resp)
    stat("Templates gerados:", f"{len(df_ep)}")
    stat("Etapas padrão totais:", f"{len(df_etp)}")
    stat("Etapas por template (min/média/máx):",
         f"{df_etp.groupby('eap_padrao_id').size().min()} / "
         f"{df_etp.groupby('eap_padrao_id').size().mean():.1f} / "
         f"{df_etp.groupby('eap_padrao_id').size().max()}")
    fase_fim(t0, len(df_ep) + len(df_etp), "2 tabelas")

    # ------------------------------------------------------------------
    t0 = fase(3, TOTAL, "FORNECEDORES (cadastro + especialidades + regiões)",
              "Empresas sintéticas com dados econômico-financeiros (PL, capital, "
              "índices de liquidez/solvência — requisitos de qualificação da Lei 14.133/21). "
              "N:M com objetos (especialidades) e regiões atendidas.",
              "fornecedor + fornecedor_especialidade + fornecedor_regiao")
    passo(f"Gerando {NUM_FORNECEDORES} empresas (CNPJ, porte, nota, PL, faturamento, índices)...")
    df_forn = gerar_fornecedor()
    stat("Distribuição por porte:", df_forn["porte"].value_counts().to_dict())
    stat("Nota desempenho (média):", f"{df_forn['nota_desempenho'].mean():.2f}")
    stat("Patrimônio líquido (mediana):", f"R$ {df_forn['patrimonio_liquido'].median():,.0f}")
    stat("Faturamento anual (mediana):", f"R$ {df_forn['faturamento_anual'].median():,.0f}")
    stat("Liquidez corrente (média):", f"{df_forn['indice_liquidez_corrente'].mean():.2f}")
    passo("Atribuindo 1-3 especialidades por fornecedor...")
    df_forn_esp = gerar_fornecedor_especialidade(df_forn, df_obj)
    stat("Pares fornecedor×objeto:", len(df_forn_esp))
    passo("Atribuindo regiões atendidas (Grandes → Nacional; MEs → local)...")
    df_forn_reg = gerar_fornecedor_regiao(df_forn, df_regiao)
    stat("Pares fornecedor×região:", len(df_forn_reg))
    fase_fim(t0, len(df_forn) + len(df_forn_esp) + len(df_forn_reg), "3 tabelas")

    # ------------------------------------------------------------------
    t0 = fase(4, TOTAL, "UNIDADES DE NEGÓCIO (Agências & Postos)",
              f"{NUM_UNIDADES_NEGOCIO} unidades de atendimento do BB espalhadas pelo "
              "país, com prefixo numérico (tipo 0001-SP). Serão atendidas pelos contratos.",
              "unidade_negocio")
    passo("Gerando agências, postos de atendimento, escritórios (distribuição por UF/região)...")
    df_un_neg = gerar_unidade_negocio(df_regiao)
    stat("Distribuição por tipo:", df_un_neg["tipo"].value_counts().head(5).to_dict())
    stat("Top 5 UFs por nº de unidades:",
         df_un_neg["uf"].value_counts().head(5).to_dict())
    fase_fim(t0, len(df_un_neg))

    # ------------------------------------------------------------------
    t0 = fase(5, TOTAL, "EAPs (Eventos de Contratação)",
              "O coração dos dados: processos reais. Cada um escolhe tipo×objeto, "
              "unidade, valor (log-normal em patamar BB), datas (sazonalidade Q1/Q3), "
              "intercorrências e status.",
              "eap (2.500 processos de contratação)")
    passo(f"Simulando {NUM_EAPS} processos completos (planejamento → assinatura)...")
    df_eap = gerar_eap(df_tipo, df_obj, df_ep, df_uni, df_forn, df_forn_esp)
    stat("Por tipo de licitação:", df_eap["_tipo_nome"].value_counts().to_dict())
    stat("Por status:", df_eap["status"].value_counts().to_dict())
    stat("Valor (min/mediana/máx):",
         f"R$ {df_eap['valor_estimado'].min():>13,.0f} / "
         f"R$ {df_eap['valor_estimado'].median():>13,.0f} / "
         f"R$ {df_eap['valor_estimado'].max():>13,.0f}")
    stat("Valor total da carteira:", f"R$ {df_eap['valor_estimado'].sum()/1e9:.2f} bi")
    stat("Intercorrências:",
         f"{df_eap['tem_intercorrencia'].sum()} ({df_eap['tem_intercorrencia'].mean()*100:.1f}%)")
    _atr = df_eap["atrasou"].dropna()
    _atraso_dias = df_eap["dias_atraso_eap"].dropna()
    if len(_atr) > 0:
        stat("Atrasaram (EAPs concluídas):",
             f"{int(_atr.sum())} ({_atr.mean()*100:.1f}%)")
        stat("Dias de atraso (mín/mediana/máx):",
             f"{int(_atraso_dias.min())} / {int(_atraso_dias.median())} / {int(_atraso_dias.max())}")
    fase_fim(t0, len(df_eap))

    # ------------------------------------------------------------------
    t0 = fase(6, TOTAL, "ETAPAS REAIS (Execução dos Processos)",
              "Cada EAP percorre as etapas do seu template. Concluídos fazem todas; "
              "Em Andamento param no meio; Cancelados mal iniciam.",
              "etapa_eap")
    df_etapa_eap = gerar_etapa_eap(df_eap, df_etp, df_resp)
    stat("Status das etapas:", df_etapa_eap["status_etapa"].value_counts().to_dict())
    stat("Duração média (etapas concluídas):", f"{df_etapa_eap['duracao_dias'].mean():.1f} dias")
    fase_fim(t0, len(df_etapa_eap))

    # ------------------------------------------------------------------
    t0 = fase(7, TOTAL, "PARTICIPANTES (Licitantes dos Certames)",
              "Licitação: 5±2 participantes; Direta: 1-3; Inexigibilidade: 1.",
              "participante")
    df_part, ganhadores = gerar_participante(df_eap, df_forn, df_forn_esp)
    stat("Participantes por EAP (média):", f"{len(df_part)/len(df_eap):.1f}")
    stat("Habilitados vs Inabilitados:", df_part["situacao"].value_counts().to_dict())
    fase_fim(t0, len(df_part))

    # ------------------------------------------------------------------
    t0 = fase(8, TOTAL, "CONTRATOS (Pós-Assinatura)",
              "Só existem para EAPs Concluídos. Vigência pode ser em DIAS, MESES ou ANOS. "
              "Inclui aditivos, rescisão (ligada à nota do fornecedor) e atrasos.",
              "contrato")
    df_contrato = gerar_contrato(df_eap, df_forn, ganhadores)
    stat("Valor total contratado:", f"R$ {df_contrato['valor_contratado'].sum()/1e9:.2f} bi")
    stat("Ticket médio:", f"R$ {df_contrato['valor_contratado'].mean():,.0f}")
    stat("Vigência (unidades usadas):", df_contrato["vigencia_unidade"].value_counts().to_dict())
    stat("Taxa de rescisão:", f"{df_contrato['teve_rescisao'].mean()*100:.1f}%")
    stat("Taxa de atraso:", f"{df_contrato['teve_atraso'].mean()*100:.1f}%")
    stat("Média de aditivos:", f"{df_contrato['num_aditivos'].mean():.2f}")
    fase_fim(t0, len(df_contrato))

    # ------------------------------------------------------------------
    t0 = fase(9, TOTAL, "CONTRATO × UNIDADE_NEGOCIO (abrangência de atendimento)",
              "Cada contrato atende 1+ unidades de negócio. Distribuição: 70% local "
              "(1-3 agências), 20% regional (10-100), 8% multi-regional (200-1000), "
              "2% nacional (todas). Respeita as regiões que o fornecedor atende.",
              "contrato_unidade_atendida (N:M)")
    df_ct_un = gerar_contrato_unidade_atendida(df_contrato, df_eap, df_un_neg, df_forn_reg, df_regiao)
    stat("Total de pares contrato×unidade:", f"{len(df_ct_un):,}")
    stat("Unidades por contrato (mín/mediana/máx):",
         f"{df_ct_un.groupby('contrato_id').size().min()} / "
         f"{int(df_ct_un.groupby('contrato_id').size().median())} / "
         f"{df_ct_un.groupby('contrato_id').size().max()}")
    fase_fim(t0, len(df_ct_un))

    # ------------------------------------------------------------------
    t0 = fase(10, TOTAL, "FINALIZAÇÃO (Denormalização + Exportação + Schema)",
              "Adiciona colunas-texto ao lado dos UUIDs (snapshots) e salva tudo.",
              "16 CSVs + schema.sql")
    eap_cols_final = [
        "id", "numero", "eap_padrao_id", "unidade_demandante_id", "unidade_executante_id",
        "objeto_resumido", "dt_abertura", "dt_assinatura", "valor_estimado",
        "prazo_total_dias", "prazo_planejado_dias", "dias_atraso_eap", "atrasou",
        "status", "urgencia", "complexidade", "tem_intercorrencia", "tipo_intercorrencia",
    ]
    df_eap_out = df_eap[eap_cols_final].copy()

    tabelas = {
        "tipo_licitacao":             df_tipo,
        "objeto_licitacao":           df_obj,
        "unidade":                    df_uni,
        "responsavel_tipo":           df_resp,
        "regiao":                     df_regiao,
        "eap_padrao":                 df_ep,
        "etapa_padrao":               df_etp,
        "fornecedor":                 df_forn,
        "fornecedor_especialidade":   df_forn_esp,
        "fornecedor_regiao":          df_forn_reg,
        "unidade_negocio":            df_un_neg,
        "eap":                        df_eap_out,
        "etapa_eap":                  df_etapa_eap,
        "participante":               df_part,
        "contrato":                   df_contrato,
        "contrato_unidade_atendida":  df_ct_un,
    }

    passo("Enriquecendo cada tabela com colunas snapshot (_nome, _prefixo, _razao_social)...")
    tabelas = denormalizar(tabelas)

    passo("Salvando CSVs em UTF-8...")
    total_linhas = 0
    for name, df in tabelas.items():
        path = f"{OUTPUT_DIR}/{name}.csv"
        df.to_csv(path, index=False, encoding="utf-8")
        total_linhas += len(df)
        stat(f"{name}.csv", f"{len(df):>7,} linhas × {df.shape[1]:>2} colunas")

    passo("Gerando schema.sql (DDL PostgreSQL)...")
    with open(f"{OUTPUT_DIR}/schema.sql", "w", encoding="utf-8") as f:
        f.write(SCHEMA_SQL)
    stat("schema.sql", f"{len(SCHEMA_SQL.splitlines())} linhas de DDL")
    fase_fim(t0, total_linhas, f"{len(tabelas)} CSVs + 1 SQL")

    # ------------------------------------------------------------------
    elapsed = time.time() - t_total
    print("╔" + "═" * (W - 2) + "╗")
    msg = f"✓ PRONTO em {elapsed:.1f}s — {total_linhas:,} linhas no total"
    print(("║" + "{:^" + str(W - 2) + "}║").format(msg))
    print("╚" + "═" * (W - 2) + "╝")
    print()
    print(f"  📁 Arquivos: {os.path.abspath(OUTPUT_DIR)}")
    print()
    print("  🚀 Como usar:")
    print("     - App Streamlit: streamlit run app_h2o_guiado.py")
    print("       (upload múltiplo dos CSVs → UI de join ensina o modelo relacional)")
    print("     - PostgreSQL local:")
    print(f"       psql -d workshop -f {OUTPUT_DIR}/schema.sql")
    print(f"       Depois \\copy cada CSV (ordem no final do schema.sql).")
    print()


if __name__ == "__main__":
    main()
