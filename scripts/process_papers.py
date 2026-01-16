"""
Main pipeline to process all papers: extract text, summarize, and save to CSV.
Supports both Anthropic Claude and OpenAI GPT APIs.
"""

import os
from pathlib import Path
import json
import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import sys
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
import numpy as np

try:
    import boto3
    CLOUDWATCH_AVAILABLE = True
except ImportError:
    CLOUDWATCH_AVAILABLE = False

# Import our other modules
sys.path.append(str(Path(__file__).parent))
from extract_text import extract_text_from_pdf
from summarize import summarize_paper, estimate_cost

def send_cloudwatch_metric(metric_name, value, unit='Count', dimensions=None):
    """Send metrics to CloudWatch if available"""
    if not CLOUDWATCH_AVAILABLE:
        return
    
    try:
        cloudwatch = boto3.client('cloudwatch')
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.utcnow()
        }
        
        if dimensions:
            metric_data['Dimensions'] = dimensions
        
        cloudwatch.put_metric_data(
            Namespace='ResearchPaperProcessing',
            MetricData=[metric_data]
        )
    except Exception as e:
        print(f"Warning: Failed to send CloudWatch metric: {e}")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def process_single_paper(pdf_path, output_dir, api_key, provider):
    """
    Process a single paper: extract text and summarize.
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save results
        api_key: API key for the chosen provider
        provider: 'anthropic' or 'openai'
        
    Returns:
        dict with results
    """
    filename = pdf_path.name
    
    # Extract text
    extraction_result = extract_text_from_pdf(pdf_path)
    
    if not extraction_result['success']:
        return {
            'filename': filename,
            'status': 'extraction_failed',
            'error': extraction_result['error']
        }
    
    # Save extracted text
    text_dir = Path(output_dir) / 'extracted_texts'
    text_dir.mkdir(parents=True, exist_ok=True)
    text_path = text_dir / f"{pdf_path.stem}.txt"
    
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(extraction_result['text'])
    
    # Summarize using chosen API
    summary_result = summarize_paper(
        extraction_result['text'], 
        filename, 
        api_key,
        provider
    )
    
    # Add extraction info
    summary_result['num_pages'] = extraction_result['num_pages']
    summary_result['text_length'] = len(extraction_result['text'])
    
    # Small delay to respect rate limits
    time.sleep(0.5)
    
    return summary_result

def track_metrics(results, start_time, end_time, provider):
    """Calculate and save performance metrics"""
    duration = end_time - start_time
    successful = sum(1 for r in results if r.get('status') == 'success')
    
    # Calculate quality scores
    quality_scores = [r.get('quality_score', 0) for r in results if r.get('status') == 'success' and r.get('quality_score')]
    avg_quality = np.mean(quality_scores) if quality_scores else 0
    
    # Count biomarkers
    total_biomarkers = sum(len(r.get('biomarkers', [])) for r in results if r.get('status') == 'success')
    
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'provider': provider,
        'total_papers': len(results),
        'successful': successful,
        'failed': len(results) - successful,
        'duration_seconds': duration,
        'papers_per_minute': (len(results) / duration) * 60 if duration > 0 else 0,
        'average_quality_score': float(avg_quality),
        'total_biomarkers_extracted': total_biomarkers
    }
    
    # Send to CloudWatch
    send_cloudwatch_metric('TotalPapersProcessed', len(results), dimensions=[{'Name': 'Provider', 'Value': provider}])
    send_cloudwatch_metric('SuccessfulProcessing', successful, dimensions=[{'Name': 'Provider', 'Value': provider}])
    send_cloudwatch_metric('FailedProcessing', len(results) - successful, dimensions=[{'Name': 'Provider', 'Value': provider}])
    send_cloudwatch_metric('AverageQualityScore', avg_quality, unit='None', dimensions=[{'Name': 'Provider', 'Value': provider}])
    send_cloudwatch_metric('TotalBiomarkers', total_biomarkers, dimensions=[{'Name': 'Provider', 'Value': provider}])
    
    return metrics

def save_results_to_csv(results, output_path):
    """
    Save results to a CSV file.
    
    Args:
        results: List of result dictionaries
        output_path: Path to save CSV file
    """
    if not results:
        print("No results to save.")
        return
    
    # Define CSV columns
    fieldnames = [
        'filename',
        'status',
        'api_provider',
        'processing_method',
        'title',
        'authors',
        'year',
        'abstract',
        'research_question',
        'methodology',
        'key_findings',
        'conclusions',
        'limitations',
        'future_work',
        'num_biomarkers',
        'biomarkers',
        'quality_score',
        'num_pages',
        'text_length',
        'chunks_processed',
        'error'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for result in results:
            # Convert list to string for key_findings
            if 'key_findings' in result and isinstance(result['key_findings'], list):
                result['key_findings'] = ' | '.join(result['key_findings'])
            
            # Process biomarkers
            if 'biomarkers' in result and isinstance(result['biomarkers'], list):
                result['num_biomarkers'] = len(result['biomarkers'])
                # Convert biomarkers to JSON string for CSV
                result['biomarkers'] = json.dumps(result['biomarkers'])
            else:
                result['num_biomarkers'] = 0
            
            # Fill in missing fields
            row = {field: result.get(field, '') for field in fieldnames}
            writer.writerow(row)
    
    print(f"\nResults saved to: {output_path}")

def main(papers_dir='project/papers', output_dir='project/outputs', max_workers=5, provider='anthropic', use_langchain=False):
    """
    Main pipeline to process all papers.
    
    Args:
        papers_dir: Directory containing PDF files
        output_dir: Directory to save results
        max_workers: Number of parallel workers for API calls
        provider: 'anthropic' or 'openai'
        use_langchain: Whether to use LangChain pipeline
    """
    start_time = time.time()
    # Validate provider
    provider = provider.lower()
    if provider not in ['anthropic', 'openai']:
        print(f"ERROR: Invalid provider '{provider}'. Use 'anthropic' or 'openai'.")
        return
    
    # Get API key based on provider
    if provider == 'anthropic':
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
            print("Please set it with: export ANTHROPIC_API_KEY='your-api-key'")
            return
    else:  # openai
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("ERROR: OPENAI_API_KEY environment variable not set.")
            print("Please set it with: export OPENAI_API_KEY='your-api-key'")
            return
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Get all PDF files
    papers_path = Path(papers_dir)
    if not papers_path.exists():
        print(f"ERROR: Papers directory not found: {papers_dir}")
        print("Please create it and add PDF files.")
        return
    
    pdf_files = list(papers_path.glob('*.pdf'))
    
    if not pdf_files:
        print(f"No PDF files found in {papers_dir}")
        return
    
    print(f"{'='*60}")
    print(f"Research Paper Processing Pipeline")
    print(f"{'='*60}")
    print(f"API Provider: {provider.upper()}")
    print(f"Processing Method: {'LangChain' if use_langchain else 'Direct API'}")
    print(f"Found {len(pdf_files)} PDF files")
    
    # Estimate costs
    cost_estimate = estimate_cost(len(pdf_files), provider=provider)
    print(f"\nEstimated API costs ({cost_estimate['provider']}):")
    print(f"  Input tokens: {cost_estimate['input_tokens']}")
    print(f"  Output tokens: {cost_estimate['output_tokens']}")
    print(f"  Input cost: {cost_estimate['input_cost']}")
    print(f"  Output cost: {cost_estimate['output_cost']}")
    print(f"  Total estimated cost: {cost_estimate['estimated_total']}")
    
    # Ask for confirmation
    response = input(f"\nProceed with processing {len(pdf_files)} papers using {provider.upper()}? (y/n): ")
    if response.lower() != 'y':
        print("Processing cancelled.")
        return
    
    print(f"\nProcessing papers with {max_workers} parallel workers...")
    print("(This may take a while...)\n")
    
    results = []
    
    # Process papers in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_pdf = {
            executor.submit(process_single_paper, pdf_path, output_dir, api_key, provider): pdf_path
            for pdf_path in pdf_files
        }
        
        # Process completed tasks with progress bar
        with tqdm(total=len(pdf_files), desc="Processing papers") as pbar:
            for future in as_completed(future_to_pdf):
                pdf_path = future_to_pdf[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Show status
                    status_icon = "✓" if result.get('status') == 'success' else "✗"
                    pbar.set_postfix_str(f"{status_icon} {pdf_path.name[:30]}")
                    
                except Exception as e:
                    results.append({
                        'filename': pdf_path.name,
                        'status': 'processing_error',
                        'error': str(e),
                        'api_provider': provider
                    })
                    pbar.set_postfix_str(f"✗ {pdf_path.name[:30]}")
                
                pbar.update(1)
    
    # Save results to CSV
    csv_path = Path(output_dir) / f'paper_summaries_{provider}.csv'
    save_results_to_csv(results, csv_path)
    
    # Save detailed JSON results
    json_path = Path(output_dir) / f'paper_summaries_{provider}.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"Detailed results saved to: {json_path}")
    
    # Calculate and save metrics
    end_time = time.time()
    metrics = track_metrics(results, start_time, end_time, provider)
    
    metrics_path = Path(output_dir) / f'metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{provider}.json'
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrics saved to: {metrics_path}")
    
    # Print summary statistics
    successful = sum(1 for r in results if r.get('status') == 'success')
    failed = len(results) - successful
    
    print(f"\n{'='*60}")
    print(f"Processing Complete!")
    print(f"{'='*60}")
    print(f"API Provider: {provider.upper()}")
    print(f"Total papers: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Processing time: {metrics['duration_seconds']:.2f} seconds")
    print(f"Papers per minute: {metrics['papers_per_minute']:.2f}")
    print(f"Average quality score: {metrics['average_quality_score']:.3f}")
    print(f"Total biomarkers extracted: {metrics['total_biomarkers_extracted']}")
    
    if failed > 0:
        print(f"\nFailed papers:")
        for result in results:
            if result.get('status') != 'success':
                print(f"  - {result['filename']}: {result.get('error', 'Unknown error')}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Process research papers with AI (Claude or GPT)')
    parser.add_argument('--papers-dir', default='project/papers', 
                        help='Directory containing PDF files')
    parser.add_argument('--output-dir', default='project/outputs', 
                        help='Directory to save results')
    parser.add_argument('--workers', type=int, default=5, 
                        help='Number of parallel workers (default: 5)')
    parser.add_argument('--provider', choices=['anthropic', 'openai'], default='anthropic',
                        help='API provider to use: anthropic (Claude) or openai (GPT-4) (default: anthropic)')
    parser.add_argument('--use-langchain', action='store_true',
                        help='Use LangChain pipeline for structured extraction (default: False)')
    
    args = parser.parse_args()
    
    main(args.papers_dir, args.output_dir, args.workers, args.provider, args.use_langchain)