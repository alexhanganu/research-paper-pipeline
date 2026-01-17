"""
Configuration file for the research paper processing pipeline.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# API Configuration
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
DEFAULT_PROVIDER = os.environ.get('DEFAULT_PROVIDER', 'anthropic')

# PubMed Configuration
PUBMED_EMAIL = os.environ.get('PUBMED_EMAIL', 'user@example.com')
NCBI_API_KEY = os.environ.get('NCBI_API_KEY', '')  # Optional, increases rate limit

# Email Configuration
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
FROM_EMAIL = os.environ.get('FROM_EMAIL', SMTP_USER)

# Processing Configuration
DEFAULT_PAPERS_DIR = os.environ.get('PAPERS_DIR', 'project/papers')
DEFAULT_OUTPUT_DIR = os.environ.get('OUTPUT_DIR', 'project/outputs')
DEFAULT_WORKERS = int(os.environ.get('MAX_WORKERS', '5'))
USE_LANGCHAIN = os.environ.get('USE_LANGCHAIN', 'false').lower() == 'true'

# Model Configuration
CLAUDE_MODEL = os.environ.get('CLAUDE_MODEL', 'claude-sonnet-4-20250514')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o')
MAX_TOKENS = int(os.environ.get('MAX_TOKENS', '4000'))
TEMPERATURE = float(os.environ.get('TEMPERATURE', '0.3'))

# Text Processing Configuration
MAX_CHARS_PER_CHUNK = int(os.environ.get('MAX_CHARS_PER_CHUNK', '100000'))
OPENAI_MAX_CHARS_PER_CHUNK = int(os.environ.get('OPENAI_MAX_CHARS_PER_CHUNK', '80000'))

# Cloud Configuration
CLOUD_PROVIDER = os.environ.get('CLOUD_PROVIDER', 'local')  # local, aws, azure

# AWS Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_S3_BUCKET = os.environ.get('AWS_S3_BUCKET', '')
RESULTS_BUCKET = os.environ.get('RESULTS_BUCKET', AWS_S3_BUCKET)
DLQ_URL = os.environ.get('DLQ_URL', '')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'prod')

# Azure Configuration
AZURE_STORAGE_CONNECTION_STRING = os.environ.get('AZURE_STORAGE_CONNECTION_STRING', '')
AZURE_CONTAINER_NAME = os.environ.get('AZURE_CONTAINER_NAME', 'research-papers')
AZURE_COMMUNICATION_CONNECTION_STRING = os.environ.get('AZURE_COMMUNICATION_CONNECTION_STRING', '')

# CloudWatch Configuration
CLOUDWATCH_NAMESPACE = os.environ.get('CLOUDWATCH_NAMESPACE', 'ResearchPaperProcessing')
ENABLE_CLOUDWATCH = os.environ.get('ENABLE_CLOUDWATCH', 'true').lower() == 'true'

# Retry Configuration
MAX_RETRIES = int(os.environ.get('MAX_RETRIES', '3'))
RETRY_MIN_WAIT = int(os.environ.get('RETRY_MIN_WAIT', '4'))
RETRY_MAX_WAIT = int(os.environ.get('RETRY_MAX_WAIT', '10'))

# Quality Check Configuration
MIN_QUALITY_SCORE = float(os.environ.get('MIN_QUALITY_SCORE', '0.5'))
ENABLE_QUALITY_CHECKS = os.environ.get('ENABLE_QUALITY_CHECKS', 'true').lower() == 'true'

# Biomarker Aggregation Configuration
MIN_PAPERS_FOR_HIGH_CONFIDENCE = int(os.environ.get('MIN_PAPERS_FOR_HIGH_CONFIDENCE', '2'))

# Cost Estimation (per million tokens)
CLAUDE_INPUT_COST = float(os.environ.get('CLAUDE_INPUT_COST', '3.0'))
CLAUDE_OUTPUT_COST = float(os.environ.get('CLAUDE_OUTPUT_COST', '15.0'))
OPENAI_INPUT_COST = float(os.environ.get('OPENAI_INPUT_COST', '2.5'))
OPENAI_OUTPUT_COST = float(os.environ.get('OPENAI_OUTPUT_COST', '10.0'))

# Logging Configuration
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FILE = os.environ.get('LOG_FILE', '')

def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Check API keys
    if DEFAULT_PROVIDER == 'anthropic' and not ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY not set but provider is 'anthropic'")
    if DEFAULT_PROVIDER == 'openai' and not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY not set but provider is 'openai'")
    
    # Check directories
    if not Path(DEFAULT_PAPERS_DIR).exists():
        errors.append(f"Papers directory does not exist: {DEFAULT_PAPERS_DIR}")
    
    # Check worker count
    if DEFAULT_WORKERS < 1 or DEFAULT_WORKERS > 20:
        errors.append(f"MAX_WORKERS must be between 1 and 20, got {DEFAULT_WORKERS}")
    
    # Check temperature
    if not 0 <= TEMPERATURE <= 1:
        errors.append(f"TEMPERATURE must be between 0 and 1, got {TEMPERATURE}")
    
    # Check cloud configuration
    if CLOUD_PROVIDER == 'aws' and not AWS_S3_BUCKET:
        errors.append("AWS_S3_BUCKET not set but cloud provider is 'aws'")
    
    if CLOUD_PROVIDER == 'azure' and not AZURE_STORAGE_CONNECTION_STRING:
        errors.append("AZURE_STORAGE_CONNECTION_STRING not set but cloud provider is 'azure'")
    
    return errors

def get_config_summary():
    """Get a summary of current configuration"""
    return {
        'platform': os.name,
        'provider': DEFAULT_PROVIDER,
        'cloud_provider': CLOUD_PROVIDER,
        'model': CLAUDE_MODEL if DEFAULT_PROVIDER == 'anthropic' else OPENAI_MODEL,
        'workers': DEFAULT_WORKERS,
        'use_langchain': USE_LANGCHAIN,
        'papers_dir': DEFAULT_PAPERS_DIR,
        'output_dir': DEFAULT_OUTPUT_DIR,
        'cloudwatch_enabled': ENABLE_CLOUDWATCH,
        'quality_checks_enabled': ENABLE_QUALITY_CHECKS,
        'max_retries': MAX_RETRIES,
        'pubmed_email': PUBMED_EMAIL
    }

if __name__ == '__main__':
    # Validate and print configuration
    print("Current Configuration:")
    print("=" * 60)
    for key, value in get_config_summary().items():
        print(f"  {key}: {value}")
    print("=" * 60)
    
    errors = validate_config()
    if errors:
        print("\nConfiguration Errors:")
        for error in errors:
            print(f"  ❌ {error}")
    else:
        print("\n✅ Configuration is valid")