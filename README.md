# Research Paper Processing Pipeline

An automated pipeline for reading, summarizing, and extracting structured information from large collections of research papers using AI. Supports both **Anthropic Claude** and **OpenAI GPT** APIs.

## Features

- 📄 **Automated PDF Processing**: Extract text from hundreds or thousands of research papers
- 🤖 **AI-Powered Analysis**: Choose between Claude AI or GPT-4 for intelligent summarization
- 🔄 **Flexible API Support**: Switch between Anthropic and OpenAI with a simple flag
- 📊 **Structured Output**: Exports results to CSV for easy analysis and review
- ⚡ **Parallel Processing**: Process multiple papers simultaneously for faster results
- 💰 **Cost Estimation**: Get cost estimates before processing large batches
- 🔄 **Error Handling**: Robust error handling with detailed logging
- 🧬 **Biomarker Aggregation**: Cross-paper analysis and high-confidence association detection
- 🔍 **PubMed Integration**: Automatically discover and track new papers
- 📧 **Email Notifications**: Get alerts when new papers are found
- ☁️ **Multi-Cloud Support**: Deploy locally, on AWS, or on Azure
- 🖥️ **Cross-Platform**: Works on Windows, macOS, and Linux
- 🎨 **GUI Application**: User-friendly interface for non-technical users

## Extracted Information

The pipeline extracts the following information from each paper:

- Title
- Authors
- Year of publication
- Abstract/Summary
- Research question or objective
- Methodology
- Key findings
- Main conclusions
- Limitations
- Future work suggestions
- **Biomarker-disease associations** with evidence levels

## Quick Start

### Prerequisites

- Python 3.8 or higher
- API key from either:
  - Anthropic ([Get Claude API key](https://console.anthropic.com/))
  - OpenAI ([Get OpenAI API key](https://platform.openai.com/api-keys))
- PDF research papers

### Installation

1. Clone the repository:
```bash
git clone https://github.com/alexhanganu/research-paper-pipeline.git
cd research-paper-pipeline
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your API key(s):

**For Anthropic Claude:**
```bash
export ANTHROPIC_API_KEY='your-anthropic-api-key'
```

**For OpenAI GPT:**
```bash
export OPENAI_API_KEY='your-openai-api-key'
```

Or create a `.env` file:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

4. Create the project structure:
```bash
mkdir -p project/papers project/outputs
```

5. Add your PDF research papers to `project/papers/`

## Usage

### Command Line Interface

#### Basic Usage

Process all PDFs using Claude (default):
```bash
python project/scripts/process_papers.py
```

Process all PDFs using OpenAI GPT:
```bash
python project/scripts/process_papers.py --provider openai
```

#### Check PubMed for New Papers

```bash
python project/scripts/process_papers.py \
  --check-pubmed \
  --pubmed-query "cancer biomarkers" \
  --email your@email.com
```

#### Advanced Options

```bash
python project/scripts/process_papers.py \
  --papers-dir /path/to/your/papers \
  --output-dir /path/to/output \
  --workers 10 \
  --provider anthropic \
  --use-langchain \
  --check-pubmed \
  --pubmed-query "BRCA1 breast cancer" \
  --email your@email.com \
  --cloud aws
```

**Arguments:**
- `--papers-dir`: Directory containing PDF files (default: `project/papers`)
- `--output-dir`: Directory to save results (default: `project/outputs`)
- `--workers`: Number of parallel workers for processing (default: 5)
- `--provider`: AI provider to use: `anthropic` or `openai` (default: `anthropic`)
- `--use-langchain`: Use LangChain for structured extraction (default: False)
- `--check-pubmed`: Check PubMed for new papers before processing
- `--pubmed-query`: PubMed search query (e.g., "cancer biomarkers")
- `--email`: Email address for new paper notifications
- `--cloud`: Cloud storage provider: `local`, `aws`, or `azure` (default: `local`)

### Platform-Specific Launchers

#### Linux/macOS

```bash
# Make script executable
chmod +x run_pipeline.sh

# Run CLI
./run_pipeline.sh

# Run GUI
./run_pipeline.sh gui

# Run monitoring dashboard
./run_pipeline.sh dashboard
```

#### Windows

```batch
REM Run CLI
run_pipeline.bat

REM Run GUI
run_pipeline.bat gui

REM Run monitoring dashboard
run_pipeline.bat dashboard
```

### GUI Application

Launch the cross-platform GUI:

```bash
python project/scripts/windows_app.py
```

Or use the launcher:
```bash
./run_pipeline.sh gui        # Linux/macOS
run_pipeline.bat gui         # Windows
```

The GUI provides:
- **Configuration Tab**: Set directories, API keys, cloud provider
- **PubMed Check Tab**: Configure automatic paper discovery
- **Processing Log Tab**: Real-time processing status and logs

### Using Individual Scripts

**Extract text only:**
```bash
python project/scripts/extract_text.py
```

**Test summarization on a single paper:**
```bash
python project/scripts/summarize.py
```

## Output Files

The pipeline generates several output files:

```
project/outputs/
├── paper_summaries_anthropic.csv        # Main results (CSV format)
├── paper_summaries_anthropic.json       # Detailed results (JSON)
├── paper_summaries_openai.csv           # Results if using OpenAI
├── paper_summaries_openai.json          # OpenAI detailed results
├── biomarkers_aggregated_anthropic.json # Biomarker knowledge base
├── biomarkers_aggregated_anthropic.csv  # Biomarker associations
├── high_confidence_associations_*.json  # High-evidence associations (2+ papers)
├── metrics_YYYYMMDD_HHMMSS_*.json      # Performance metrics
├── processed_papers.json                # PubMed tracking file
├── new_papers_YYYYMMDD_HHMMSS.json     # Newly discovered papers
├── extraction_summary.json              # Text extraction statistics
└── extracted_texts/                     # Individual text files
    ├── paper1.txt
    ├── paper2.txt
    └── ...
```

## Project Structure

```
research-paper-pipeline/
├── README.md                              # Main documentation
├── SETUP.md                               # Complete setup guide
├── requirements.txt                       # Python dependencies
├── .env                                   # Your configuration (create from .env.example)
├── .env.example                          # Template for environment variables
│
├── run_pipeline.sh                        # Linux/macOS launcher
├── run_pipeline.bat                       # Windows launcher
├── deploy_lambda.sh                       # AWS Lambda deployment script
│
├── lambda.tf                              # Terraform infrastructure for AWS
├── lambda_handler.py                      # AWS Lambda entry point
│
├── config.py                              # Centralized configuration
├── monitoring_dashboard.py                # Streamlit monitoring dashboard
│
└── project/
    ├── papers/                            # INPUT: Place PDF files here
    ├── outputs/                           # OUTPUT: All results saved here
    └── scripts/                           # Core processing scripts
        ├── extract_text.py                # PDF text extraction
        ├── summarize.py                   # Direct API summarization
        ├── langchain_pipeline.py          # LangChain structured extraction
        ├── process_papers.py              # Main orchestration pipeline
        ├── pubmed_integration.py          # PubMed API integration
        ├── email_notification.py          # Email notifications
        ├── biomarker_aggregator.py        # Cross-paper biomarker analysis
        ├── cloud_storage.py               # Cloud storage abstraction
        └── windows_app.py                 # Cross-platform GUI
```

## Cost Estimation

The pipeline provides cost estimates before processing. Approximate costs:

### Anthropic Claude Sonnet 4
- **Input**: ~$3 per million tokens
- **Output**: ~$15 per million tokens
- **Average per paper**: $0.10 - $0.50

### OpenAI GPT-4o
- **Input**: ~$2.50 per million tokens
- **Output**: ~$10 per million tokens
- **Average per paper**: $0.08 - $0.40

For 1000 papers:
- **Claude**: ~$100 - $500
- **GPT-4o**: ~$80 - $400

## Performance

- **Processing speed**: ~5-10 papers per minute (with 5 parallel workers)
- **Time for 1000 papers**: 2-3 hours
- **Recommended batch size**: Up to 1000 papers per run

## Cloud Deployment

### AWS

```bash
# Set environment variables
export TF_VAR_anthropic_api_key="your-key"
export TF_VAR_provider_choice="anthropic"

# Deploy with Terraform
terraform init
terraform plan
terraform apply

# Or use deployment script
./deploy_lambda.sh
```

### Azure

```bash
# Configure Azure
az login
az storage account create --name researchpapers --resource-group rg

# Set environment variables
export CLOUD_PROVIDER=azure
export AZURE_STORAGE_CONNECTION_STRING="your-connection-string"

# Run pipeline
python project/scripts/process_papers.py --cloud azure
```

### Local Only

```bash
# Process and save everything locally (default)
python project/scripts/process_papers.py --cloud local
```

## Monitoring Dashboard

Launch the interactive monitoring dashboard:

```bash
streamlit run monitoring_dashboard.py
```

Features:
- Real-time processing metrics
- Success/failure rates
- Quality score trends
- Biomarker extraction statistics
- CloudWatch integration (if using AWS)

Access at: http://localhost:8501

## PubMed Integration

The pipeline can automatically discover new papers from PubMed:

### Setup

1. Configure in `.env`:
```bash
PUBMED_EMAIL=your.email@example.com
NCBI_API_KEY=your-ncbi-key  # Optional, increases rate limit
```

2. Run with PubMed check:
```bash
python project/scripts/process_papers.py \
  --check-pubmed \
  --pubmed-query "cancer biomarkers" \
  --email your@email.com
```

### Features

- Searches PubMed for papers matching your query
- Compares against already-processed papers
- Sends email notification with new paper summaries
- Tracks processed papers to avoid duplicates
- Saves new paper metadata to JSON

## Biomarker Aggregation

The pipeline automatically aggregates biomarker data across all papers:

### Features

- **Name Normalization**: BRCA1 = BRCA-1 = brca1
- **Cross-Paper Analysis**: Combines findings from multiple papers
- **Evidence Scoring**: More papers = higher confidence
- **High-Confidence Associations**: Flags associations found in 2+ papers
- **Disease Mapping**: Links biomarkers to associated diseases

### Output

- `biomarkers_aggregated_{provider}.json`: Complete knowledge base
- `biomarkers_aggregated_{provider}.csv`: Easy-to-analyze table format
- `high_confidence_associations_{provider}.json`: Validated associations

## Requirements

- Python 3.8+
- API key from either:
  - Anthropic ([Get Claude API key](https://console.anthropic.com/))
  - OpenAI ([Get OpenAI API key](https://platform.openai.com/api-keys))
- PDF research papers

## Troubleshooting

### "API KEY environment variable not set"
Make sure you've exported your API key(s) or created a `.env` file. You need either `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` depending on which provider you're using.

### "No PDF files found"
Ensure your PDF files are in the `project/papers/` directory or specify the correct path with `--papers-dir`.

### Rate limiting errors
Reduce the number of workers with `--workers 3` or add delays between requests.

### PDF extraction issues
Some PDFs (especially scanned documents) may not extract text properly. Consider using OCR preprocessing for scanned papers.

### Email sending fails
- Use App Password (not regular password) for Gmail
- Enable 2-Step Verification in Google Account
- Check SMTP settings in `.env`

### PubMed API rate limiting
Get an NCBI API key from https://www.ncbi.nlm.nih.gov/account/ to increase rate limits from 3 to 10 requests/second.

## Limitations

- Works best with text-based PDFs (not scanned images without OCR)
- Accuracy depends on paper quality and formatting
- API costs scale with the number and length of papers
- Rate limits apply based on your API tier

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [Anthropic's Claude API](https://www.anthropic.com/) and [OpenAI's API](https://openai.com/)
- Uses [pypdf](https://github.com/py-pdf/pypdf) for PDF extraction
- PubMed integration via [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/)

## Citation

If you use this tool in your research, please cite:

```bibtex
@software{research_paper_pipeline,
  title = {Research Paper Processing Pipeline},
  author = {Your Name},
  year = {2025},
  url = {https://github.com/alexhanganu/research-paper-pipeline}
}
```

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review [Anthropic's API docs](https://docs.anthropic.com/) or [OpenAI's API docs](https://platform.openai.com/docs)
- See [SETUP.md](SETUP.md) for detailed setup instructions

## Roadmap

- [ ] Support for additional file formats (DOCX, TXT)
- [ ] OCR integration for scanned PDFs
- [ ] Neo4j/graph database integration for biomarker networks
- [ ] Clinical trial phase extraction
- [ ] Drug development competitive intelligence
- [ ] Real-time alerting system
- [ ] Web-based dashboard
- [ ] Docker containerization

---

**Note**: This tool is designed for research and educational purposes. Always respect copyright and licensing terms of the papers you process.

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│  QUICK START                                                     │
├─────────────────────────────────────────────────────────────────┤
│  1. Install: pip install -r requirements.txt                    │
│  2. Setup: cp .env.example .env (add your API keys)             │
│  3. Add PDFs to: project/papers/                                │
│  4. Run: python project/scripts/process_papers.py               │
│                                                                  │
│  GUI MODE                                                        │
│  • Linux/Mac: ./run_pipeline.sh gui                             │
│  • Windows:   run_pipeline.bat gui                              │
│                                                                  │
│  PUBMED CHECK                                                    │
│  python project/scripts/process_papers.py \                     │
│    --check-pubmed \                                              │
│    --pubmed-query "your search terms" \                         │
│    --email your@email.com                                       │
│                                                                  │
│  CLOUD DEPLOYMENT                                                │
│  --cloud local   # Save locally (default)                       │
│  --cloud aws     # Upload to S3                                 │
│  --cloud azure   # Upload to Azure Blob Storage                 │
│                                                                  │
│  OUTPUTS                                                         │
│  • project/outputs/paper_summaries_*.csv                        │
│  • project/outputs/biomarkers_aggregated_*.csv                  │
│  • project/outputs/high_confidence_associations_*.json          │
└─────────────────────────────────────────────────────────────────┘
```