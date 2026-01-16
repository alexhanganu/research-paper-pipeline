#!/bin/bash
# Script to deploy the Lambda function to AWS

set -e

echo "=========================================="
echo "Research Paper Pipeline Lambda Deployment"
echo "=========================================="

# Configuration
LAMBDA_FUNCTION_NAME="research-paper-processor-prod"
LAMBDA_LAYER_NAME="research-paper-dependencies-prod"
REGION="${AWS_REGION:-us-east-1}"

# Check for required tools
command -v aws >/dev/null 2>&1 || { echo "AWS CLI not found. Please install it first." >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3 not found. Please install it first." >&2; exit 1; }
command -v zip >/dev/null 2>&1 || { echo "zip not found. Please install it first." >&2; exit 1; }

# Create temporary directories
echo "Creating build directories..."
mkdir -p build/lambda
mkdir -p build/layer/python

# Step 1: Create Lambda Layer with dependencies
echo ""
echo "Step 1: Building Lambda Layer with dependencies..."
pip install -r requirements.txt -t build/layer/python --upgrade

cd build/layer
zip -r ../lambda_layer.zip python
cd ../..
echo "Lambda layer package created: build/lambda_layer.zip"

# Step 2: Create Lambda deployment package
echo ""
echo "Step 2: Building Lambda deployment package..."
cp project/scripts/*.py build/lambda/
cd build/lambda
zip -r ../lambda_deployment.zip .
cd ../..
echo "Lambda deployment package created: build/lambda_deployment.zip"

# Step 3: Deploy using Terraform (optional)
if command -v terraform >/dev/null 2>&1; then
    echo ""
    echo "Step 3: Deploying with Terraform..."
    read -p "Do you want to deploy using Terraform? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Copy files for Terraform
        cp build/lambda_layer.zip .
        cp build/lambda_deployment.zip .
        
        # Initialize and apply Terraform
        terraform init
        terraform plan
        read -p "Apply Terraform changes? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            terraform apply
        fi
    fi
else
    echo ""
    echo "Terraform not found. Skipping Terraform deployment."
    echo "You can manually upload:"
    echo "  - build/lambda_layer.zip as a Lambda Layer"
    echo "  - build/lambda_deployment.zip as the Lambda function code"
fi

# Step 4: Manual deployment instructions
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Manual deployment option:"
echo "1. Create Lambda Layer:"
echo "   aws lambda publish-layer-version \\"
echo "     --layer-name $LAMBDA_LAYER_NAME \\"
echo "     --zip-file fileb://build/lambda_layer.zip \\"
echo "     --compatible-runtimes python3.11 \\"
echo "     --region $REGION"
echo ""
echo "2. Create/Update Lambda Function:"
echo "   aws lambda update-function-code \\"
echo "     --function-name $LAMBDA_FUNCTION_NAME \\"
echo "     --zip-file fileb://build/lambda_deployment.zip \\"
echo "     --region $REGION"
echo ""
echo "Don't forget to:"
echo "  - Set environment variables (ANTHROPIC_API_KEY or OPENAI_API_KEY)"
echo "  - Configure S3 triggers"
echo "  - Set up CloudWatch alarms"
echo "=========================================="