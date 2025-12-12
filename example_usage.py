"""Example usage of the Clinical BERT API."""
import requests
import json
from typing import Dict, Any

# Update this URL to your deployed API endpoint
API_URL = "http://localhost:8000"


def predict_single(sentence: str) -> Dict[str, Any]:
    """Predict assertion status for a single sentence."""
    url = f"{API_URL}/predict"
    data = {"sentence": sentence}
    
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()


def predict_batch(sentences: list[str]) -> Dict[str, Any]:
    """Predict assertion status for multiple sentences."""
    url = f"{API_URL}/predict/batch"
    data = {"sentences": sentences}
    
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()


def health_check() -> Dict[str, Any]:
    """Check API health status."""
    url = f"{API_URL}/health"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    print("Clinical BERT API - Example Usage\n")
    print("=" * 50)
    
    # Health check
    print("\n1. Health Check:")
    try:
        health = health_check()
        print(json.dumps(health, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the API is running at", API_URL)
        exit(1)
    
    # Test cases from requirements
    test_cases = [
        ("The patient denies chest pain.", "ABSENT"),
        ("He has a history of hypertension.", "PRESENT"),
        ("If the patient experiences dizziness, reduce the dosage.", "CONDITIONAL"),
        ("No signs of pneumonia were observed.", "ABSENT"),
    ]
    
    print("\n2. Single Predictions:")
    print("-" * 50)
    for sentence, expected in test_cases:
        try:
            result = predict_single(sentence)
            status = "✓" if result["label"] == expected else "✗"
            print(f"{status} Sentence: {sentence}")
            print(f"  Label: {result['label']} (expected: {expected})")
            print(f"  Score: {result['score']:.4f}\n")
        except Exception as e:
            print(f"✗ Error: {e}\n")
    
    # Batch prediction
    print("\n3. Batch Prediction:")
    print("-" * 50)
    sentences = [sentence for sentence, _ in test_cases]
    try:
        result = predict_batch(sentences)
        print(f"Processed {len(result['predictions'])} sentences:")
        for i, pred in enumerate(result['predictions']):
            print(f"  {i+1}. {pred['label']} (score: {pred['score']:.4f})")
    except Exception as e:
        print(f"Error: {e}")

