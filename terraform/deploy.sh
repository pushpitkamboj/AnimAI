#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== AnimAI Cloud Run Deployment ===${NC}"

# Check if PROJECT_ID is set
if [ -z "$1" ]; then
    echo -e "${RED}Usage: ./deploy.sh <PROJECT_ID> [REGION]${NC}"
    echo "Example: ./deploy.sh my-gcp-project us-central1"
    exit 1
fi

PROJECT_ID=$1
REGION=${2:-us-central1}
IMAGE_NAME="animai"
MANIM_IMAGE_NAME="manim-worker"
REPO_NAME="animai-repo"

echo -e "${YELLOW}Project ID: ${PROJECT_ID}${NC}"
echo -e "${YELLOW}Region: ${REGION}${NC}"

# Step 1: Configure gcloud
echo -e "\n${GREEN}Step 1: Configuring gcloud...${NC}"
gcloud config set project $PROJECT_ID

# Step 2: Enable required APIs
echo -e "\n${GREEN}Step 2: Enabling required GCP APIs...${NC}"
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Step 3: Configure Docker for Artifact Registry
echo -e "\n${GREEN}Step 3: Configuring Docker authentication...${NC}"
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Step 4: Check if Artifact Registry repo exists, create if not
echo -e "\n${GREEN}Step 4: Setting up Artifact Registry...${NC}"
if ! gcloud artifacts repositories describe $REPO_NAME --location=$REGION &>/dev/null; then
    echo "Creating Artifact Registry repository..."
    gcloud artifacts repositories create $REPO_NAME \
        --repository-format=docker \
        --location=$REGION \
        --description="Docker repository for AnimAI"
else
    echo "Artifact Registry repository already exists."
fi

# Step 5: Build and push Docker image
echo -e "\n${GREEN}Step 5: Building and pushing Docker images...${NC}"
cd ..

IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest"
MANIM_IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${MANIM_IMAGE_NAME}:latest"

echo "Building image: ${IMAGE_URL}"
docker build -t $IMAGE_URL .

echo "Pushing image to Artifact Registry..."
docker push $IMAGE_URL

echo "Building manim-worker image: ${MANIM_IMAGE_URL}"
docker build -t $MANIM_IMAGE_URL ./manim-worker

echo "Pushing manim-worker image..."
docker push $MANIM_IMAGE_URL

# Step 6: Apply Terraform
echo -e "\n${GREEN}Step 6: Applying Terraform configuration...${NC}"
cd terraform

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo -e "${RED}Error: terraform.tfvars not found!${NC}"
    echo "Please copy terraform.tfvars.example to terraform.tfvars and fill in your values."
    exit 1
fi

terraform init
terraform plan -out=tfplan
terraform apply tfplan

# Get the service URL
SERVICE_URL=$(terraform output -raw service_url)

echo -e "\n${GREEN}=== Deployment Complete ===${NC}"
echo -e "Service URL: ${YELLOW}${SERVICE_URL}${NC}"
echo -e "\nTest your endpoints:"
echo -e "  Health: curl ${SERVICE_URL}/health"
echo -e "  Run: curl -X POST ${SERVICE_URL}/run -H 'Content-Type: application/json' -d '{\"prompt\": \"test\"}'"
