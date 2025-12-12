# Clinical Assertion Negation BERT API

A real-time inference API for clinical text classification using the Hugging Face model `bvanaken/clinical-assertion-negation-bert`. This API classifies clinical sentences with assertion status labels (PRESENT, ABSENT, CONDITIONAL) and confidence scores.

## 📋 Project Overview

Healthcare systems often contain unstructured clinical notes. Understanding the assertion status of medical concepts in text is critical for downstream analytics and diagnostics. This API provides a production-ready service to classify clinical sentences in real-time.

### Features

- **FastAPI-based REST API** with OpenAPI documentation
- **Model caching** - Model loaded once at startup for optimal performance
- **Single and batch prediction** endpoints
- **Health check endpoint** for monitoring
- **Dockerized** for easy deployment
- **CI/CD pipeline** with GitHub Actions
- **Cloud Run deployment** ready

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker (for containerized deployment)
- Google Cloud SDK (for GCP deployment)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd clinical-bert-api
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the API**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/health`

### Using Docker

1. **Build the Docker image**
   ```bash
   docker build -t clinical-bert-api .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 clinical-bert-api
   ```

## 📡 API Usage

### Single Prediction

**Endpoint:** `POST /predict`

**Request:**
```python
import requests

url = "http://localhost:8000/predict"
data = {
    "sentence": "The patient denies chest pain."
}

response = requests.post(url, json=data)
result = response.json()
print(result)
# Output: {"label": "ABSENT", "score": 0.9842}
```

**cURL:**
```bash
curl -X POST "http://localhost:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{"sentence": "The patient denies chest pain."}'
```

### Batch Prediction

**Endpoint:** `POST /predict/batch`

**Request:**
```python
import requests

url = "http://localhost:8000/predict/batch"
data = {
    "sentences": [
        "The patient denies chest pain.",
        "He has a history of hypertension.",
        "If the patient experiences dizziness, reduce the dosage."
    ]
}

response = requests.post(url, json=data)
result = response.json()
print(result)
# Output: {
#   "predictions": [
#     {"label": "ABSENT", "score": 0.9842},
#     {"label": "PRESENT", "score": 0.9234},
#     {"label": "CONDITIONAL", "score": 0.8765}
#   ]
# }
```

### Health Check

**Endpoint:** `GET /health`

```python
import requests

response = requests.get("http://localhost:8000/health")
print(response.json())
# Output: {"status": "healthy", "model_loaded": true}
```

## ☁️ Cloud Deployment (Google Cloud Platform)

### Prerequisites

1. Google Cloud account with billing enabled (free tier: $300 credits)
2. Google Cloud SDK installed and configured
3. Docker installed

### Setup Steps

1. **Create a GCP Project**
   ```bash
   gcloud projects create your-project-id
   gcloud config set project your-project-id
   ```

2. **Enable Required APIs**
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable artifactregistry.googleapis.com
   ```

3. **Create Artifact Registry Repository**
   ```bash
   gcloud artifacts repositories create clinical-bert-api \
       --repository-format=docker \
       --location=us-central1 \
       --description="Docker repository for Clinical BERT API"
   ```

4. **Deploy Using Script**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh your-project-id us-central1
   ```

   Or manually:

   ```bash
   # Build and tag image
   docker build -t us-central1-docker.pkg.dev/your-project-id/clinical-bert-api/clinical-bert-api:latest .
   
   # Push to Artifact Registry
   docker push us-central1-docker.pkg.dev/your-project-id/clinical-bert-api/clinical-bert-api:latest
   
   # Deploy to Cloud Run
   gcloud run deploy clinical-bert-api \
       --image us-central1-docker.pkg.dev/your-project-id/clinical-bert-api/clinical-bert-api:latest \
       --platform managed \
       --region us-central1 \
       --allow-unauthenticated \
       --memory 2Gi \
       --cpu 2 \
       --timeout 300 \
       --max-instances 10
   ```

### CI/CD Deployment

The project includes GitHub Actions workflows for automated CI/CD:

1. **Set up GitHub Secrets:**
   - `GCP_SA_KEY`: Service account key JSON (as plain text, not base64 encoded)

2. **Create Service Account:**
   ```bash
   gcloud iam service-accounts create github-actions \
       --display-name="GitHub Actions Service Account"
   
   gcloud projects add-iam-policy-binding your-project-id \
       --member="serviceAccount:github-actions@your-project-id.iam.gserviceaccount.com" \
       --role="roles/run.admin"
   
   gcloud projects add-iam-policy-binding your-project-id \
       --member="serviceAccount:github-actions@your-project-id.iam.gserviceaccount.com" \
       --role="roles/artifactregistry.writer"
   
   gcloud iam service-accounts keys create key.json \
       --iam-account=github-actions@your-project-id.iam.gserviceaccount.com
   ```

3. **Add to GitHub Secrets:**
   - Copy the entire contents of `key.json` (the JSON file)
   - Add as `GCP_SA_KEY` secret in GitHub repository settings (paste the JSON directly, no base64 encoding needed)

4. **Update Workflow Configuration:**
   
   Edit `.github/workflows/cd.yml` and update the environment variables in the `env:` section:
   ```yaml
   env:
     PROJECT_ID: your-project-id          # Replace with your GCP project ID
     SERVICE_NAME: clinical-bert-api       # Your Cloud Run service name
     REGION: us-central1                   # Your deployment region
     DOCKER_IMAGE_URL: us-central1-docker.pkg.dev/your-project-id/dev-bert-api/dev-bert-api
     # Format: {region}-docker.pkg.dev/{project-id}/{repository-name}/{image-name}
   ```

5. **Create Artifact Registry Repository:**
   
   The workflow uses `dev-bert-api` as the repository name. Create it with:
   ```bash
   gcloud artifacts repositories create dev-bert-api \
       --repository-format=docker \
       --location=us-central1 \
       --description="Docker repository for Clinical BERT API"
   ```
   
   **Note:** If you prefer a different repository name, update both the repository creation command and the `DOCKER_IMAGE_URL` in `cd.yml`.

6. **Workflows:**
   - **CI** (`ci.yml`): Runs on PRs and pushes to main - linting and testing
   - **CD** (`cd.yml` - "Deploy to Cloud Run"): 
     - **Triggers:**
       - Pushes to `main` branch
       - Tag creation (tags starting with `v*`, e.g., `v1.0.0`) - enables version-based deployments
     - **Steps:**
       - Authenticates with GCP using service account
       - Builds Docker image
       - Pushes to Artifact Registry (`dev-bert-api` repository)
       - Deploys to Cloud Run with default settings (public access enabled)
     
   **Note:** The CD workflow uses Cloud Run default resource settings. To customize memory, CPU, timeout, or max instances, add these flags to the `gcloud run deploy` command in `cd.yml`:
   ```bash
   --memory 2Gi \
   --cpu 2 \
   --timeout 300 \
   --max-instances 10
   ```

## 🧪 Testing

### Run Unit Tests

```bash
pytest tests/ -v
```

### Test API with Example Script

```bash
# Make sure the API is running first
python example_usage.py
```

### Test Cases

The API is tested against the following cases:

| Sentence | Expected Label |
|----------|---------------|
| "The patient denies chest pain." | ABSENT |
| "He has a history of hypertension." | PRESENT |
| "If the patient experiences dizziness, reduce the dosage." | CONDITIONAL |
| "No signs of pneumonia were observed." | ABSENT |

## 📁 Project Structure

```
clinical-bert-api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── model.py         # Model loading & prediction logic
│   └── schemas.py       # Pydantic schemas
├── tests/
│   ├── __init__.py
│   └── test_api.py      # Unit tests
├── .github/
│   └── workflows/
│       ├── ci.yml       # CI workflow
│       └── cd.yml       # CD workflow
├── Dockerfile
├── requirements.txt
├── deploy.sh
├── .dockerignore
├── .gitignore
└── README.md
```

## ⚡ Performance

- **API Response Time:** < 500ms for short clinical sentences (on CPU)
- **Model Loading:** ~10-30 seconds on first startup (cached thereafter)
- **Batch Processing:** More efficient for multiple sentences

## 🔧 Configuration

### Environment Variables

- `TRANSFORMERS_CACHE`: Cache directory for transformers models (default: `/app/.cache`)
- `PYTHONUNBUFFERED`: Set to 1 for real-time logging in containers

### Cloud Run Settings

- **Memory:** 2Gi (recommended for model loading)
- **CPU:** 2 vCPU
- **Timeout:** 300 seconds
- **Max Instances:** 10 (adjust based on traffic)

## 📝 Known Issues & Tradeoffs

1. **Cold Start:** First request after deployment may take longer due to model loading (~10-30s)
   - **Mitigation:** Use Cloud Run min instances > 0 to keep containers warm

2. **Memory Requirements:** Model requires ~1.5GB RAM
   - **Mitigation:** Cloud Run configured with 2Gi memory

3. **GPU Not Used:** Currently runs on CPU for cost efficiency
   - **Tradeoff:** Slightly slower inference but no GPU costs
   - **Future:** Can enable GPU for faster inference if needed

4. **Model Download:** First deployment downloads model from Hugging Face (~500MB)
   - **Mitigation:** Model is cached in container filesystem

## 🔐 Security Considerations

- API is currently unauthenticated (for demo purposes)
- For production, consider:
  - Adding authentication (API keys, OAuth)
  - Enabling Cloud Run authentication
  - Using Cloud IAM for access control
  - Implementing rate limiting

## 📄 License

This project uses the `bvanaken/clinical-assertion-negation-bert` model from Hugging Face. Please review the model's license before commercial use.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📧 Support

For issues or questions, please open an issue on GitHub.
