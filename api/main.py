"""
API REST para expor o modelo H2O treinado ao Teams Copilot (ou qualquer outro cliente).

Endpoints:
  POST /predict/prazo           — prevê prazo_total_dias de uma licitação
  POST /predict/intercorrencia  — prevê probabilidade de intercorrência
  POST /cluster                 — atribui cluster a uma licitação
  GET  /model/info              — métricas e feature importance
  GET  /health                  — health check

Uso:
  cd api && uvicorn main:app --host 0.0.0.0 --port 8000

Para expor à internet (workshop/demo):
  cloudflared tunnel --url http://localhost:8000
"""
from typing import Any, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
import joblib
import os

app = FastAPI(
    title="H2O Guiado — Consultor de Contratações BB",
    version="1.0.0",
    description="API de predição de prazo e risco para licitações do Banco do Brasil.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restringir para domínios BB
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Modelos H2O pré-carregados (cache_resource simples)
# ============================================================
_MODELS: dict[str, Any] = {}


def _ensure_h2o():
    import h2o
    if not getattr(_ensure_h2o, "_init", False):
        h2o.init(max_mem_size="2G", nthreads=-1)
        _ensure_h2o._init = True
    return h2o


def load_model(kind: str):
    """
    Carrega modelo H2O salvo. Espera que o modelo esteja em models/{kind}/
    (MOJO .zip ou H2O binary). Substituir pela lógica real de persistência.
    """
    if kind in _MODELS:
        return _MODELS[kind]
    path = Path(f"models/{kind}")
    if not path.exists():
        raise FileNotFoundError(f"Modelo {kind} não encontrado em {path}")
    h2o = _ensure_h2o()
    model = h2o.load_model(str(next(path.glob("*"))))
    _MODELS[kind] = model
    return model


# ============================================================
# Schemas (Pydantic)
# ============================================================
class LicitacaoFeatures(BaseModel):
    """Features necessárias para predição (fase de planejamento)."""
    tipo_licitacao_nome: str = Field(..., description="Licitação / Contratação Direta / Inexigibilidade")
    objeto_licitacao_nome: str = Field(..., description="TI - Desenvolvimento, Engenharia - Obras, etc.")
    modalidade: Optional[str] = Field(None, description="Licitação Eletrônica, Contratação Direta, Inexigibilidade")
    unidade_demandante_prefixo: Optional[str] = Field(None, description="DISEC, SUREF-SP, DITEC, etc.")
    valor_estimado: float = Field(..., ge=0, description="Valor estimado em R$")
    urgencia: str = Field("Normal", description="Normal, Urgente ou Emergencial")
    complexidade: str = Field("Média", description="Baixa, Média ou Alta")
    eap_padrao_nome: Optional[str] = Field(None, description="Ex: 'Licitação de Engenharia - Obras'")
    tem_intercorrencia: Optional[bool] = Field(None, description="Só usar se conhecido — senão deixe null")


class PrazoResponse(BaseModel):
    prazo_previsto_dias: float
    erro_medio_historico: Optional[float] = None
    intervalo_min: Optional[float] = None
    intervalo_max: Optional[float] = None
    percentil_na_base: Optional[float] = None
    interpretacao: str


class IntercorrenciaResponse(BaseModel):
    probabilidade: float = Field(..., ge=0, le=1)
    classe_prevista: str
    nivel_risco: str  # Baixo / Moderado / Alto
    acao_sugerida: str
    interpretacao: str


class ClusterResponse(BaseModel):
    cluster_id: int
    perfil: str
    licitacoes_no_grupo: int


class ModelInfo(BaseModel):
    tarefa: str
    algoritmo: str
    target: str
    features: list[str]
    metricas: dict
    top_features: list[dict]


# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/health")
def health():
    return {"status": "ok", "service": "h2o-guiado-api", "version": "1.0.0"}


@app.post("/predict/prazo", response_model=PrazoResponse, tags=["Predição"])
def prever_prazo(features: LicitacaoFeatures):
    """
    Prevê o prazo total (em dias) desde a abertura da EAP até a assinatura.
    Responde à pergunta: "Quantos dias essa licitação vai levar?"
    """
    try:
        import h2o
        model = load_model("prazo")
        df = pd.DataFrame([features.model_dump(exclude_none=True)])
        hf = h2o.H2OFrame(df)
        pred = model.predict(hf).as_data_frame()
        val = float(pred["predict"].iloc[0])

        # Carregar estatísticas do treino (se disponíveis em models/prazo/stats.json)
        stats_path = Path("models/prazo/stats.json")
        mae = percentil = None
        if stats_path.exists():
            import json
            stats = json.loads(stats_path.read_text())
            mae = stats.get("mae")
            dist = stats.get("distribuicao_target", [])
            if dist:
                percentil = float(np.mean(np.array(dist) < val) * 100)

        interp = (
            f"Prazo previsto: {val:.0f} dias. "
            + (f"Na base histórica, o erro médio foi de ±{mae:.0f} dias. " if mae else "")
            + (f"Esta licitação está no percentil {percentil:.0f}% (dos mais "
               f"{'demorados' if percentil > 50 else 'rápidos'}). " if percentil is not None else "")
        )
        return PrazoResponse(
            prazo_previsto_dias=val,
            erro_medio_historico=mae,
            intervalo_min=val - mae if mae else None,
            intervalo_max=val + mae if mae else None,
            percentil_na_base=percentil,
            interpretacao=interp,
        )
    except FileNotFoundError as e:
        raise HTTPException(503, detail=f"Modelo não disponível: {e}")
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.post("/predict/intercorrencia", response_model=IntercorrenciaResponse, tags=["Predição"])
def prever_intercorrencia(features: LicitacaoFeatures):
    """
    Prevê probabilidade de intercorrência (impugnação, recurso, certame deserto)
    na fase de planejamento — ANTES de publicar o edital.
    """
    try:
        import h2o
        model = load_model("intercorrencia")
        df = pd.DataFrame([features.model_dump(exclude_none=True)])
        hf = h2o.H2OFrame(df)
        pred = model.predict(hf).as_data_frame()
        prob_cols = [c for c in pred.columns if c != "predict"]
        prob = float(pred[prob_cols[-1]].iloc[0])
        classe = str(pred["predict"].iloc[0])

        if prob < 0.30:
            nivel, acao = "Baixo", "Publicar edital no fluxo normal. Nenhuma ação extra."
        elif prob < 0.60:
            nivel, acao = "Moderado", ("Revisão jurídica rápida antes de publicar. "
                                       "Parecer da DIJUR em até 2 dias úteis.")
        else:
            nivel, acao = "Alto", ("Revisão jurídica OBRIGATÓRIA antes de publicar. "
                                   "Considerar reunião técnica de alinhamento.")

        interp = (f"Probabilidade de intercorrência: {prob*100:.1f}% — Risco {nivel}. "
                  f"A classe prevista é '{classe}'.")
        return IntercorrenciaResponse(
            probabilidade=prob, classe_prevista=classe,
            nivel_risco=nivel, acao_sugerida=acao, interpretacao=interp,
        )
    except FileNotFoundError as e:
        raise HTTPException(503, detail=f"Modelo não disponível: {e}")
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/model/info/{kind}", response_model=ModelInfo, tags=["Modelo"])
def model_info(kind: str):
    """Retorna metadados do modelo — métricas, features, top fatores."""
    info_path = Path(f"models/{kind}/info.json")
    if not info_path.exists():
        raise HTTPException(404, f"Info do modelo {kind} não disponível.")
    import json
    return ModelInfo(**json.loads(info_path.read_text()))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
