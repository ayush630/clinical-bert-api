"""FastAPI application for clinical text classification."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.model import load_model, predict, predict_batch, is_model_loaded
from app.schemas import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    HealthResponse
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup."""
    logger.info("Starting up: Loading model...")
    try:
        load_model()
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise
    yield
    logger.info("Shutting down")


# Create FastAPI app
app = FastAPI(
    title="Clinical Assertion Negation BERT API",
    description="Real-time inference API for clinical text classification",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
async def root():
    """Root endpoint."""
    return {
        "message": "Clinical Assertion Negation BERT API",
        "version": "1.0.0",
        "endpoints": {
            "predict": "/predict",
            "predict_batch": "/predict/batch",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy" if is_model_loaded() else "unhealthy",
        model_loaded=is_model_loaded()
    )


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict_sentence(request: PredictionRequest):
    """
    Predict assertion status for a single clinical sentence.
    
    Expected labels:
    - PRESENT: The condition is present
    - ABSENT: The condition is absent/denied
    - CONDITIONAL: The condition is conditional/hypothetical
    """
    if not is_model_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        label, score = predict(request.sentence)
        return PredictionResponse(label=label, score=score)
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/predict/batch", response_model=BatchPredictionResponse, tags=["Prediction"])
async def predict_batch_sentences(request: BatchPredictionRequest):
    """
    Predict assertion status for multiple clinical sentences in batch.
    
    This endpoint is more efficient for processing multiple sentences at once.
    """
    if not is_model_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        results = predict_batch(request.sentences)
        predictions = [
            PredictionResponse(label=label, score=score)
            for label, score in results
        ]
        return BatchPredictionResponse(predictions=predictions)
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

