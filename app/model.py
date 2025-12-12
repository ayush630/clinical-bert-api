"""Model loading and prediction logic."""

import logging
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

logger = logging.getLogger(__name__)

# Model configuration
MODEL_NAME = "bvanaken/clinical-assertion-negation-bert"

# Global variables to cache model and tokenizer
_model = None
_tokenizer = None
_device = None
_label_mapping = None


def load_model():
    """Load the model and tokenizer once at startup."""
    global _model, _tokenizer, _device, _label_mapping

    if _model is not None:
        logger.info("Model already loaded, skipping reload")
        return

    try:
        logger.info(f"Loading model: {MODEL_NAME}")

        # Determine device
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {_device}")

        # Load tokenizer and model
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        _model.to(_device)
        _model.eval()  # Set to evaluation mode

        # Get label mapping from model config
        if hasattr(_model.config, "id2label") and _model.config.id2label:
            _label_mapping = _model.config.id2label
            logger.info(f"Using model label mapping: {_label_mapping}")
        else:
            # Fallback to default mapping if not in config
            _label_mapping = {0: "PRESENT", 1: "ABSENT", 2: "CONDITIONAL"}
            logger.warning("Model config doesn't have id2label, using default mapping")

        logger.info("Model loaded successfully")

    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise


def predict(sentence: str) -> tuple[str, float]:
    """
    Predict the assertion status for a single sentence.

    Args:
        sentence: Clinical sentence to classify

    Returns:
        Tuple of (label, confidence_score)
    """
    global _model, _tokenizer, _device, _label_mapping

    if _model is None or _tokenizer is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")

    try:
        # Tokenize input
        inputs = _tokenizer(
            sentence, return_tensors="pt", truncation=True, max_length=512, padding=True
        )
        inputs = {k: v.to(_device) for k, v in inputs.items()}

        # Get prediction
        with torch.no_grad():
            outputs = _model(**inputs)
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=-1)
            predicted_class = torch.argmax(probabilities, dim=-1).item()
            confidence = probabilities[0][predicted_class].item()

        # Map to label
        label = _label_mapping.get(predicted_class, f"UNKNOWN_{predicted_class}")

        return label, confidence

    except Exception as e:
        logger.error(f"Error during prediction: {str(e)}")
        raise


def predict_batch(sentences: list[str]) -> list[tuple[str, float]]:
    """
    Predict assertion status for multiple sentences.

    Args:
        sentences: List of clinical sentences to classify

    Returns:
        List of tuples (label, confidence_score)
    """
    global _model, _tokenizer, _device, _label_mapping

    if _model is None or _tokenizer is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")

    try:
        # Tokenize all inputs
        inputs = _tokenizer(
            sentences,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )
        inputs = {k: v.to(_device) for k, v in inputs.items()}

        # Get predictions
        with torch.no_grad():
            outputs = _model(**inputs)
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=-1)
            predicted_classes = torch.argmax(probabilities, dim=-1)
            confidences = torch.max(probabilities, dim=-1)[0]

        # Map to labels
        results = []
        for i, (pred_class, conf) in enumerate(zip(predicted_classes, confidences)):
            pred_class_id = pred_class.item()
            label = _label_mapping.get(pred_class_id, f"UNKNOWN_{pred_class_id}")
            results.append((label, conf.item()))

        return results

    except Exception as e:
        logger.error(f"Error during batch prediction: {str(e)}")
        raise


def is_model_loaded() -> bool:
    """Check if model is loaded."""
    return _model is not None
