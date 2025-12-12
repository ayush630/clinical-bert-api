#!/bin/bash

# Deployment script for Google Cloud Run
# Usage: ./deploy.sh PROJECT_ID [REGION] [GAR_LOCATION]
#   PROJECT_ID: Your GCP project ID (required)
#   REGION: Deployment region (default: us-central1)
#   GAR_LOCATION: Artifact Registry location (default: us-central1)

set -e

PROJECT_ID=${1:-${GCP_PROJECT_ID}}
REGION=${2:-us-central1}
GAR_LOCATION=${3:-us-central1}
SERVICE_NAME="clinical-bert-api"
REPOSITORY_NAME="${SERVICE_NAME}"  # Artifact Registry repository name
IMAGE_NAME="${GAR_LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/${SERVICE_NAME}"

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID is required"
    echo "Usage: ./deploy.sh PROJECT_ID [REGION] [GAR_LOCATION]"
    echo "  Example: ./deploy.sh my-project-id us-central1 us-central1"
    exit 1
fi

echo "Deploying to GCP..."
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo "Repository: $REPOSITORY_NAME"
echo "Image: $IMAGE_NAME"

# Authenticate
echo "Authenticating with GCP..."
gcloud auth login
gcloud config set project $PROJECT_ID

# Create Artifact Registry repository if it doesn't exist
echo "Setting up Artifact Registry..."
gcloud artifacts repositories create ${REPOSITORY_NAME} \
    --repository-format=docker \
    --location=${GAR_LOCATION} \
    --description="Docker repository for Clinical BERT API" \
    2>/dev/null || echo "Repository '${REPOSITORY_NAME}' already exists or creation failed"

# Configure Docker
echo "Configuring Docker..."
gcloud auth configure-docker ${GAR_LOCATION}-docker.pkg.dev

# Build Docker image
echo "Building Docker image..."
docker build -t ${IMAGE_NAME}:latest .

# Push image
echo "Pushing image to Artifact Registry..."
docker push ${IMAGE_NAME}:latest

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 2 \
    --set-env-vars TRANSFORMERS_CACHE=/app/.cache

echo "Deployment complete!"
echo "Getting service URL..."
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)'

