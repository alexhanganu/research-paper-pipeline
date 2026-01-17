"""
Extract text from PDF files in the papers directory.
"""

import os
from pathlib import Path
import json
import pypdf

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        dict with 'text', 'num_pages', and 'metadata'
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text.strip():
                    text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
            
            full_text = "\n\n".join(text_parts)
            
            # Extract metadata if available
            metadata = {}
            if pdf_reader.metadata:
                metadata = {
                    'title': pdf_reader.metadata.get('/Title', ''),
                    'author': pdf_reader.metadata.get('/Author', ''),
                    'subject': pdf_reader.metadata.get('/Subject', ''),
                    'creator': pdf_reader.metadata.get('/Creator', '')
                }
            
            return {
                'text': full_text,
                'num_pages': num_pages,
                'metadata': metadata,
                'success': True,
                'error': None
            }
            
    except Exception as e:
        return {
            'text': '',
            'num_pages': 0,
            'metadata': {},
            'success': False,
            'error': str(e)
        }

def process_all_pdfs(papers_dir='project/papers', output_dir='project/outputs'):
    """
    Process all PDFs in the papers directory and save extracted text.
    
    Args:
        papers_dir: Directory containing PDF files
        output_dir: Directory to save extracted text
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Get all PDF files
    papers_path = Path(papers_dir)
    pdf_files = list(papers_path.glob('*.pdf'))
    
    print(f"Found {len(pdf_files)} PDF files in {papers_dir}")
    
    results = []
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"Processing {i}/{len(pdf_files)}: {pdf_path.name}")
        
        result = extract_text_from_pdf(pdf_path)
        
        if result['success']:
            # Save extracted text to a file
            text_filename = pdf_path.stem + '.txt'
            text_path = Path(output_dir) / 'extracted_texts' / text_filename
            text_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(result['text'])
            
            results.append({
                'filename': pdf_path.name,
                'num_pages': result['num_pages'],
                'text_length': len(result['text']),
                'status': 'success',
                'text_file': str(text_path)
            })
            print(f"  ✓ Extracted {result['num_pages']} pages, {len(result['text'])} characters")
        else:
            results.append({
                'filename': pdf_path.name,
                'num_pages': 0,
                'text_length': 0,
                'status': 'failed',
                'error': result['error']
            })
            print(f"  ✗ Failed: {result['error']}")
    
    # Save summary
    summary_path = Path(output_dir) / 'extraction_summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    successful = sum(1 for r in results if r['status'] == 'success')
    print(f"\n{'='*60}")
    print(f"Extraction complete: {successful}/{len(results)} PDFs processed successfully")
    print(f"Summary saved to: {summary_path}")
    
    return results

if __name__ == '__main__':
    results = process_all_pdfs()