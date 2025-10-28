#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "DeepSeek-OCR RunPod Deployment Script"
echo "========================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Get Docker Hub username
if [ -z "$DOCKER_USERNAME" ]; then
    echo -e "${YELLOW}Enter your Docker Hub username:${NC}"
    read DOCKER_USERNAME
    export DOCKER_USERNAME
fi

# Confirm
echo ""
echo -e "${GREEN}Configuration:${NC}"
echo "  Docker Hub username: $DOCKER_USERNAME"
echo "  Image name: ${DOCKER_USERNAME}/deepseek-ocr-runpod:latest"
echo ""

read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 1
fi

# Docker login
echo ""
echo -e "${YELLOW}Step 1: Docker Hub Login${NC}"
echo "Please login to Docker Hub..."
docker login

# Build image
echo ""
echo -e "${YELLOW}Step 2: Building Docker Image${NC}"
echo "This will take 10-15 minutes..."
echo ""

docker build -f Dockerfile.runpod \
    -t ${DOCKER_USERNAME}/deepseek-ocr-runpod:latest \
    -t ${DOCKER_USERNAME}/deepseek-ocr-runpod:v2.0 \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build successful!${NC}"
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi

# Push image
echo ""
echo -e "${YELLOW}Step 3: Pushing to Docker Hub${NC}"
echo "Pushing latest tag..."
docker push ${DOCKER_USERNAME}/deepseek-ocr-runpod:latest

echo "Pushing version tag..."
docker push ${DOCKER_USERNAME}/deepseek-ocr-runpod:v2.0

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Push successful!${NC}"
else
    echo -e "${RED}✗ Push failed${NC}"
    exit 1
fi

# Success message
echo ""
echo -e "${GREEN}========================================"
echo "Deployment Complete!"
echo "========================================${NC}"
echo ""
echo "Your Docker image is ready:"
echo "  ${DOCKER_USERNAME}/deepseek-ocr-runpod:latest"
echo ""
echo "Next steps:"
echo "  1. Go to: https://www.runpod.io/console/serverless"
echo "  2. Update your endpoint to use: ${DOCKER_USERNAME}/deepseek-ocr-runpod:latest"
echo "  3. Wait 2-3 minutes for workers to restart"
echo "  4. Test with: python3 upload_large_pdf_to_runpod.py"
echo ""
echo "See DEPLOYMENT_GUIDE.md for detailed instructions"
echo ""
