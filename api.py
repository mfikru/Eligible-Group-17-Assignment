"""FastAPI service exposing the same model.   Run: uvicorn api:app --reload"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.predict import ModelNotFoundError, load_bundle, predict_price

app = FastAPI(title="House Price API - Group 17", version="1.0")
_bundle = None


def bundle():
    global _bundle
    if _bundle is None:
        try:
            _bundle = load_bundle()
        except ModelNotFoundError as e:
            raise HTTPException(status_code=503, detail=str(e))
    return _bundle


class House(BaseModel):
    OverallQual: int = Field(ge=1, le=10)
    GrLivArea: float = Field(ge=300, le=6000)
    TotalBsmtSF: float = Field(ge=0, le=6500)
    GarageCars: int = Field(ge=0, le=5)
    FullBath: int = Field(ge=0, le=5)
    BedroomAbvGr: int = Field(ge=0, le=10)
    YearBuilt: int = Field(ge=1870, le=2026)
    YearRemodAdd: int = Field(ge=1870, le=2026)
    LotArea: float = Field(ge=1000, le=250000)
    Neighborhood: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(house: House):
    model, metadata = bundle()
    result = predict_price(house.model_dump(), model, metadata)
    if not result["ok"]:
        raise HTTPException(status_code=422, detail=result["errors"])
    return result
