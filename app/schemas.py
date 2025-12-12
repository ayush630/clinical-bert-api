"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field
from typing import List, Optional


class PredictionRequest(BaseModel):
    """Request schema for single sentence prediction."""

    sentence: str = Field(
        ..., description="Clinical sentence to classify", min_length=1
    )


class BatchPredictionRequest(BaseModel):
    """Request schema for batch predictions."""

    sentences: List[str] = Field(
        ..., description="List of clinical sentences to classify", min_length=1
    )


class PredictionResponse(BaseModel):
    """Response schema for prediction."""

    label: str = Field(
        ..., description="Predicted label (PRESENT, ABSENT, or CONDITIONAL)"
    )
    score: float = Field(
        ..., description="Confidence score between 0 and 1", ge=0.0, le=1.0
    )


class BatchPredictionResponse(BaseModel):
    """Response schema for batch predictions."""

    predictions: List[PredictionResponse] = Field(
        ..., description="List of predictions"
    )


class HealthResponse(BaseModel):
    """Response schema for health check."""

    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether the model is loaded")

    class Config:
        protected_namespaces = ()
