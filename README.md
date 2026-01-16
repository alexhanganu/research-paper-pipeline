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

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/research-paper-pipeline.git
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
```
ANTHROPIC_API_KEY=your-anthropic-key-here
OPENAI_API_KEY=your-openai-key-here
```

## Quick Start

1. Create the project structure:
```bash
mkdir -p project/papers project/outputs
```

2. Add your PDF research papers to `project/papers/`

3. Run the pipeline:
```bash
python project/scripts/process_papers.py
```

## Usage

### Basic Usage

Process all PDFs using Claude (default):
```bash
python project/scripts/process_papers.py
```

Process all PDFs using OpenAI GPT:
```bash
python project/scripts/process_papers.py --provider openai
```

With LangChain
```bash
python project/scripts/process_papers.py --use-langchain --provider anthropic
```

With custom settings
```bash
python project/scripts/process_papers.py --workers 10 --provider openai --use-langchain
```


### Advanced Options

```bash
python project/scripts/process_papers.py \
  --papers-dir /path/to/your/papers \
  --output-dir /path/to/output \
  --workers 10 \
  --provider anthropic
```

**Arguments:**
- `--papers-dir`: Directory containing PDF files (default: `project/papers`)
- `--output-dir`: Directory to save results (default: `project/outputs`)
- `--workers`: Number of parallel workers for processing (default: 5)
- `--provider`: AI provider to use: `anthropic` or `openai` (default: `anthropic`)

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
├── paper_summaries_anthropic.csv    # CSV results (if using Claude)
├── paper_summaries_openai.csv       # CSV results (if using GPT)
├── paper_summaries_anthropic.json   # Detailed JSON (if using Claude)
├── paper_summaries_openai.json      # Detailed JSON (if using GPT)
├── extraction_summary.json          # Text extraction statistics
└── extracted_texts/                 # Individual text files
    ├── paper1.txt
    ├── paper2.txt
    └── ...
```

## Project Structure

```
research-paper-pipeline/
├── README.md
├── requirements.txt
├── .env                         # API keys (create this)
├── project/
│   ├── papers/                  # Place your PDFs here
│   ├── outputs/                 # Results saved here
│   └── scripts/
│       ├── extract_text.py      # PDF text extraction
│       ├── summarize.py         # AI summarization
│       └── process_papers.py    # Main pipeline orchestrator
```


## Lambda Deployment

Deploy everything
```bash
./deploy_lambda.sh
```

Or use Terraform directly
```bash
terraform init
terraform plan
terraform apply
```

## Monitoring

Start dashboard
```bash
streamlit run monitoring_dashboard.py
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

## Limitations

- Works best with text-based PDFs (not scanned images without OCR)
- Accuracy depends on paper quality and formatting
- API costs scale with the number and length of papers
- Rate limits apply based on your Anthropic API tier

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Uses [Anthropic's Claude API](https://www.anthropic.com/)
- Uses [OpenAI's API](https://openai.com/)
- Uses [pypdf](https://github.com/py-pdf/pypdf) for PDF extraction

## Citation

If you use this tool in your research, please cite:

```bibtex
@software{research_paper_pipeline,
  title = {Research Paper Processing Pipeline},
  author = {Alexandru Hanganu},
  year = {2025},
  url = {https://github.com/alexhanganu/research-paper-pipeline}
}
```

---

**Note**: This tool is designed for research and educational purposes. Always respect copyright and licensing terms of the papers you process.