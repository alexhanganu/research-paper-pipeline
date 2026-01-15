"""
Summarize and extract information from research papers using Anthropic's Claude API or OpenAI API.
"""

import os
from anthropic import Anthropic
from openai import OpenAI
import time
import json

def chunk_text(text, max_chars=100000):
    """
    Split text into chunks if it's too long.
    Claude can handle ~200k characters, but we'll be conservative.
    
    Args:
        text: The text to chunk
        max_chars: Maximum characters per chunk
        
    Returns:
        List of text chunks
    """
    if len(text) <= max_chars:
        return [text]
    
    # Try to split on page boundaries
    pages = text.split('--- Page')
    chunks = []
    current_chunk = ""
    
    for page in pages:
        if len(current_chunk) + len(page) > max_chars and current_chunk:
            chunks.append(current_chunk)
            current_chunk = page
        else:
            current_chunk += ('--- Page' if current_chunk else '') + page
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def summarize_paper_claude(text, filename, api_key):
    """
    Use Claude to summarize a research paper and extract key information.
    
    Args:
        text: The paper text
        filename: Name of the paper file
        api_key: Anthropic API key
        
    Returns:
        dict with extracted information
    """
    client = Anthropic(api_key=api_key)
    
    # Chunk text if necessary
    chunks = chunk_text(text)
    
    prompt = f"""You are analyzing a research paper. Please extract and provide the following information in a structured format:

1. Title
2. Authors (comma-separated list)
3. Year of publication
4. Abstract/Summary (2-3 sentences)
5. Main research question or objective
6. Methodology (brief description)
7. Key findings (3-5 bullet points)
8. Main conclusions
9. Limitations mentioned
10. Future work suggested

Please respond ONLY with a JSON object in this exact format:
{{
  "title": "paper title",
  "authors": "author1, author2, author3",
  "year": "YYYY",
  "abstract": "brief summary",
  "research_question": "main question",
  "methodology": "methods used",
  "key_findings": ["finding 1", "finding 2", "finding 3"],
  "conclusions": "main conclusions",
  "limitations": "limitations mentioned",
  "future_work": "suggested future research"
}}

If any field cannot be determined from the text, use "Not found" as the value.

Here is the research paper{' (part 1 of ' + str(len(chunks)) + ')' if len(chunks) > 1 else ''}:

{chunks[0]}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text
        
        # Clean up the response (remove markdown code blocks if present)
        response_text = response_text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON response
        result = json.loads(response_text)
        result['filename'] = filename
        result['status'] = 'success'
        result['chunks_processed'] = len(chunks)
        result['api_provider'] = 'anthropic'
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"  ✗ JSON parsing error: {e}")
        print(f"  Response: {response_text[:200]}...")
        return {
            'filename': filename,
            'status': 'json_error',
            'error': str(e),
            'raw_response': response_text[:500],
            'api_provider': 'anthropic'
        }
    except Exception as e:
        print(f"  ✗ API error: {e}")
        return {
            'filename': filename,
            'status': 'api_error',
            'error': str(e),
            'api_provider': 'anthropic'
        }

def summarize_paper_openai(text, filename, api_key):
    """
    Use OpenAI to summarize a research paper and extract key information.
    
    Args:
        text: The paper text
        filename: Name of the paper file
        api_key: OpenAI API key
        
    Returns:
        dict with extracted information
    """
    client = OpenAI(api_key=api_key)
    
    # Chunk text if necessary (OpenAI has smaller context window)
    chunks = chunk_text(text, max_chars=80000)
    
    prompt = f"""You are analyzing a research paper. Please extract and provide the following information in a structured format:

1. Title
2. Authors (comma-separated list)
3. Year of publication
4. Abstract/Summary (2-3 sentences)
5. Main research question or objective
6. Methodology (brief description)
7. Key findings (3-5 bullet points)
8. Main conclusions
9. Limitations mentioned
10. Future work suggested

Please respond ONLY with a JSON object in this exact format:
{{
  "title": "paper title",
  "authors": "author1, author2, author3",
  "year": "YYYY",
  "abstract": "brief summary",
  "research_question": "main question",
  "methodology": "methods used",
  "key_findings": ["finding 1", "finding 2", "finding 3"],
  "conclusions": "main conclusions",
  "limitations": "limitations mentioned",
  "future_work": "suggested future research"
}}

If any field cannot be determined from the text, use "Not found" as the value.

Here is the research paper{' (part 1 of ' + str(len(chunks)) + ')' if len(chunks) > 1 else ''}:

{chunks[0]}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a research paper analysis assistant. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        response_text = response.choices[0].message.content
        
        # Clean up the response (remove markdown code blocks if present)
        response_text = response_text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON response
        result = json.loads(response_text)
        result['filename'] = filename
        result['status'] = 'success'
        result['chunks_processed'] = len(chunks)
        result['api_provider'] = 'openai'
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"  ✗ JSON parsing error: {e}")
        print(f"  Response: {response_text[:200]}...")
        return {
            'filename': filename,
            'status': 'json_error',
            'error': str(e),
            'raw_response': response_text[:500],
            'api_provider': 'openai'
        }
    except Exception as e:
        print(f"  ✗ API error: {e}")
        return {
            'filename': filename,
            'status': 'api_error',
            'error': str(e),
            'api_provider': 'openai'
        }

def summarize_paper(text, filename, api_key=None, provider='anthropic'):
    """
    Summarize a paper using the specified API provider.
    
    Args:
        text: The paper text
        filename: Name of the paper file
        api_key: API key (if None, reads from environment variable)
        provider: 'anthropic' or 'openai'
        
    Returns:
        dict with extracted information
    """
    if provider.lower() == 'anthropic':
        if api_key is None:
            api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable.")
        return summarize_paper_claude(text, filename, api_key)
    
    elif provider.lower() == 'openai':
        if api_key is None:
            api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        return summarize_paper_openai(text, filename, api_key)
    
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'anthropic' or 'openai'.")

def estimate_cost(num_papers, avg_chars_per_paper=50000, provider='anthropic'):
    """
    Estimate API costs for processing papers.
    
    Anthropic Claude Sonnet 4: ~$3 per million input tokens, ~$15 per million output tokens
    OpenAI GPT-4o: ~$2.50 per million input tokens, ~$10 per million output tokens
    Roughly 4 chars per token.
    """
    input_tokens = (num_papers * avg_chars_per_paper) / 4
    output_tokens = num_papers * 500  # ~500 tokens output per paper
    
    if provider.lower() == 'anthropic':
        input_cost = (input_tokens / 1_000_000) * 3
        output_cost = (output_tokens / 1_000_000) * 15
    elif provider.lower() == 'openai':
        input_cost = (input_tokens / 1_000_000) * 2.5
        output_cost = (output_tokens / 1_000_000) * 10
    else:
        return {'error': 'Unknown provider'}
    
    total_cost = input_cost + output_cost
    
    return {
        'provider': provider,
        'estimated_total': f"${total_cost:.2f}",
        'input_cost': f"${input_cost:.2f}",
        'output_cost': f"${output_cost:.2f}",
        'input_tokens': f"{input_tokens:,.0f}",
        'output_tokens': f"{output_tokens:,.0f}"
    }

if __name__ == '__main__':
    # Test with a sample text
    sample_text = """
    Title: Deep Learning for Natural Language Processing
    Authors: John Smith, Jane Doe
    
    Abstract: This paper presents a novel approach to natural language processing using deep learning...
    
    Introduction: Natural language processing has evolved...
    """
    
    print("Testing summarization...")
    result = summarize_paper(sample_text, "test.pdf", provider='anthropic')
    print(json.dumps(result, indent=2))