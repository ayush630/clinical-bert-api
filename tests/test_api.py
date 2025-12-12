"""Test cases for the API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data


def test_predict_absent():
    """Test prediction for ABSENT label."""
    response = client.post(
        "/predict", json={"sentence": "The patient denies chest pain."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "ABSENT"
    assert 0.0 <= data["score"] <= 1.0


def test_predict_present():
    """Test prediction for PRESENT label."""
    response = client.post(
        "/predict", json={"sentence": "He has a history of hypertension."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "PRESENT"
    assert 0.0 <= data["score"] <= 1.0


def test_predict_conditional():
    """Test prediction for CONDITIONAL label."""
    response = client.post(
        "/predict",
        json={"sentence": "If the patient experiences dizziness, reduce the dosage."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "CONDITIONAL"
    assert 0.0 <= data["score"] <= 1.0


def test_predict_absent_variant():
    """Test another ABSENT variant."""
    response = client.post(
        "/predict", json={"sentence": "No signs of pneumonia were observed."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "ABSENT"
    assert 0.0 <= data["score"] <= 1.0


def test_predict_batch():
    """Test batch prediction endpoint."""
    response = client.post(
        "/predict/batch",
        json={
            "sentences": [
                "The patient denies chest pain.",
                "He has a history of hypertension.",
                "If the patient experiences dizziness, reduce the dosage.",
            ]
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert len(data["predictions"]) == 3
    for pred in data["predictions"]:
        assert "label" in pred
        assert "score" in pred
        assert 0.0 <= pred["score"] <= 1.0


def test_predict_invalid_input():
    """Test prediction with invalid input."""
    response = client.post("/predict", json={"sentence": ""})
    # Should return validation error
    assert response.status_code == 422


def test_predict_missing_field():
    """Test prediction with missing field."""
    response = client.post("/predict", json={})
    assert response.status_code == 422
