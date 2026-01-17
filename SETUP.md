# Setup Guide - Research Paper Processing Pipeline

Complete setup instructions for all platforms and deployment options.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Platform-Specific Setup](#platform-specific-setup)
3. [Configuration](#configuration)
4. [Cloud Deployment](#cloud-deployment)
5. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- Python 3.8 or higher
- API key from Anthropic or OpenAI
- Internet connection

### Installation (All Platforms)

```bash
# Clone the repository
git clone https://github.com/alexhanganu/research-paper-pipeline.git
cd research-paper-pipeline

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p project/papers project/outputs

# Configure API keys (see Configuration section below)
```

---

## Platform-Specific Setup

### Linux

```bash
# Make launch script executable
chmod +x run_pipeline.sh

# Run command-line interface
./run_pipeline.sh

# Run GUI application
./run_pipeline.sh gui

# Run monitoring dashboard
./run_pipeline.sh dashboard
```

### macOS

```bash
# Make launch script executable
chmod +x run_pipeline.sh

# Run command-line interface
./run_pipeline.sh

# Run GUI application
./run_pipeline.sh gui

# Run monitoring dashboard
./run_pipeline.sh dashboard
```

### Windows (Command Prompt)

```batch
REM Run command-line interface
run_pipeline.bat

REM Run GUI application
run_pipeline.bat gui

REM Run monitoring dashboard
run_pipeline.bat dashboard
```

### Windows (PowerShell)

```powershell
# Run command-line interface
.\run_pipeline.bat

# Run GUI application
.\run_pipeline.bat gui

# Run monitoring dashboard
.\run_pipeline.bat dashboard
```

### Windows (GUI App)

Double-click `run_pipeline.bat gui` or run:

```batch
python project\scripts\windows_app.py
```

---

## Configuration

### 1. Create `.env` File

Create a `.env` file in the project root:

```bash
# API Keys (Required)
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-proj-your-key-here

# Default Provider
DEFAULT_PROVIDER=anthropic

# PubMed Configuration (Optional)
PUBMED_EMAIL=your.email@example.com
NCBI_API_KEY=your-ncbi-api-key  # Optional, increases rate limits

# Email Notifications (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your.email@gmail.com

# Cloud Storage (Optional)
CLOUD_PROVIDER=local  # Options: local, aws, azure

# AWS Configuration (if using AWS)
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket-name

# Azure Configuration (if using Azure)
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
AZURE_CONTAINER_NAME=research-papers
AZURE_COMMUNICATION_CONNECTION_STRING=your-communication-string

# Processing Configuration
MAX_WORKERS=5
USE_LANGCHAIN=false
```

### 2. Gmail App Password Setup (For Email Notifications)

1. Go to Google Account settings
2. Enable 2-Step Verification
3. Generate App Password:
   - Go to Security → App passwords
   - Select "Mail" and your device
   - Copy the 16-character password
4. Use this password in `SMTP_PASSWORD`

---

## Usage Examples

### Command Line

#### Basic Usage

```bash
# Process papers with default settings
python project/scripts/process_papers.py

# Specify directories
python project/scripts/process_papers.py \
  --papers-dir /path/to/papers \
  --output-dir /path/to/output

# Use OpenAI instead of Anthropic
python project/scripts/process_papers.py --provider openai

# Use LangChain for structured extraction
python project/scripts/process_papers.py --use-langchain
```

#### Check PubMed for New Papers

```bash
python project/scripts/process_papers.py \
  --check-pubmed \
  --pubmed-query "cancer biomarkers" \
  --email your.email@example.com
```

#### Process with Cloud Storage

```bash
# AWS
python project/scripts/process_papers.py --cloud aws

# Azure
python project/scripts/process_papers.py --cloud azure
```

#### Full Example

```bash
python project/scripts/process_papers.py \
  --papers-dir project/papers \
  --output-dir project/outputs \
  --provider anthropic \
  --use-langchain \
  --workers 10 \
  --check-pubmed \
  --pubmed-query "BRCA1 breast cancer" \
  --email your.email@example.com \
  --cloud aws
```

### GUI Application

1. Launch the GUI:
   ```bash
   python project/scripts/windows_app.py
   ```

2. Configure settings in the GUI:
   - **Configuration Tab**: Set directories, API keys, cloud provider
   - **PubMed Check Tab**: Enable PubMed search and set query
   - **Processing Log Tab**: View real-time processing logs

3. Click "Start Processing"

### Monitoring Dashboard

```bash
streamlit run monitoring_dashboard.py
```

Access at: http://localhost:8501

---

## Cloud Deployment

### AWS Deployment

#### Prerequisites

- AWS CLI installed and configured
- Terraform installed (optional)
- AWS account with appropriate permissions

#### Using Terraform

```bash
# Set variables
export TF_VAR_anthropic_api_key="your-key"
export TF_VAR_openai_api_key="your-key"
export TF_VAR_provider_choice="anthropic"

# Deploy
terraform init
terraform plan
terraform apply
```

#### Manual Deployment

```bash
# Run deployment script
./deploy_lambda.sh

# Or manually upload
aws lambda publish-layer-version \
  --layer-name research-paper-dependencies \
  --zip-file fileb://build/lambda_layer.zip \
  --compatible-runtimes python3.11

aws lambda update-function-code \
  --function-name research-paper-processor \
  --zip-file fileb://build/lambda_deployment.zip
```

### Azure Deployment

#### Prerequisites

- Azure CLI installed
- Azure subscription
- Azure Storage Account
- Azure Communication Services (for email)

#### Setup

```bash
# Login to Azure
az login

# Create resource group
az group create --name research-papers-rg --location eastus

# Create storage account
az storage account create \
  --name researchpapersstorage \
  --resource-group research-papers-rg \
  --location eastus \
  --sku Standard_LRS

# Get connection string
az storage account show-connection-string \
  --name researchpapersstorage \
  --resource-group research-papers-rg
```

#### Configure `.env`

```bash
CLOUD_PROVIDER=azure
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
AZURE_CONTAINER_NAME=research-papers
```

---

## Troubleshooting

### Common Issues

#### 1. API Key Not Found

**Error**: `ANTHROPIC_API_KEY environment variable not set`

**Solution**:
- Create `.env` file with your API keys
- Or set environment variable:
  ```bash
  export ANTHROPIC_API_KEY="your-key"  # Linux/macOS
  set ANTHROPIC_API_KEY=your-key       # Windows
  ```

#### 2. Module Not Found

**Error**: `ModuleNotFoundError: No module named 'anthropic'`

**Solution**:
```bash
pip install -r requirements.txt
```

#### 3. PDF Extraction Fails

**Error**: `Text extraction failed`

**Solution**:
- Ensure PDFs are text-based (not scanned images)
- For scanned PDFs, use OCR preprocessing
- Check PDF file permissions

#### 4. Email Sending Fails

**Error**: `SMTP authentication error`

**Solution**:
- Use App Password (not regular password) for Gmail
- Check SMTP settings in `.env`
- Verify 2-Step Verification is enabled

#### 5. PubMed API Rate Limiting

**Error**: `Too many requests`

**Solution**:
- Get NCBI API key: https://www.ncbi.nlm.nih.gov/account/
- Add to `.env`: `NCBI_API_KEY=your-key`
- This increases rate limit from 3 to 10 requests/second

#### 6. Cloud Upload Fails

**AWS Error**: `NoCredentialsError`

**Solution**:
```bash
aws configure
# Enter Access Key ID, Secret Access Key, Region
```

**Azure Error**: `Connection string invalid`

**Solution**:
- Verify connection string in `.env`
- Check Azure Storage Account exists
- Ensure correct permissions

### Platform-Specific Issues

#### Linux/macOS

**Permission Denied**:
```bash
chmod +x run_pipeline.sh
```

#### Windows

**Script Execution Policy**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Path Issues**:
- Use backslashes in paths: `project\papers`
- Or use forward slashes with quotes: `"project/papers"`

---

## Performance Tuning

### Optimize Processing Speed

```bash
# Increase parallel workers (more memory usage)
python project/scripts/process_papers.py --workers 20

# Use direct API (faster than LangChain)
python project/scripts/process_papers.py --use-langchain=false
```

### Reduce API Costs

```bash
# Use OpenAI (slightly cheaper)
python project/scripts/process_papers.py --provider openai

# Process in smaller batches
# Split papers into multiple directories
```

### Memory Management

For large batches (1000+ papers):
- Process in chunks of 100-200
- Use cloud storage to offload results
- Increase system swap space

---

## Additional Resources

- **Anthropic API Docs**: https://docs.anthropic.com/
- **OpenAI API Docs**: https://platform.openai.com/docs
- **PubMed API Guide**: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- **AWS Lambda Docs**: https://docs.aws.amazon.com/lambda/
- **Azure Storage Docs**: https://docs.microsoft.com/azure/storage/

---

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review error logs in `project/outputs/`

---

## Next Steps

1. ✅ Complete setup following this guide
2. ✅ Test with a few sample papers
3. ✅ Configure PubMed integration
4. ✅ Set up cloud storage (optional)
5. ✅ Deploy to cloud (optional)
6. ✅ Set up monitoring dashboard
