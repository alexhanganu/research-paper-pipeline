"""
PubMed integration for discovering and downloading new research papers.
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import requests
from xml.etree import ElementTree as ET

class PubMedClient:
    """Client for interacting with PubMed API"""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    def __init__(self, email: str = None, api_key: str = None):
        """
        Initialize PubMed client.
        
        Args:
            email: Your email (required by NCBI)
            api_key: NCBI API key (optional, increases rate limit)
        """
        self.email = email or os.environ.get('PUBMED_EMAIL', 'user@example.com')
        self.api_key = api_key or os.environ.get('NCBI_API_KEY', '')
        self.rate_limit = 0.34 if not self.api_key else 0.1  # seconds between requests
    
    def search(self, query: str, max_results: int = 100, 
               min_date: str = None, max_date: str = None) -> List[str]:
        """
        Search PubMed for papers matching query.
        
        Args:
            query: Search query (e.g., "cancer biomarkers")
            max_results: Maximum number of results to return
            min_date: Minimum publication date (YYYY/MM/DD)
            max_date: Maximum publication date (YYYY/MM/DD)
            
        Returns:
            List of PubMed IDs (PMIDs)
        """
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'json',
            'email': self.email
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        if min_date:
            params['mindate'] = min_date
        
        if max_date:
            params['maxdate'] = max_date
        
        try:
            response = requests.get(
                f"{self.BASE_URL}esearch.fcgi",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            pmids = data.get('esearchresult', {}).get('idlist', [])
            
            print(f"Found {len(pmids)} papers matching query: {query}")
            return pmids
            
        except Exception as e:
            print(f"Error searching PubMed: {e}")
            return []
    
    def fetch_details(self, pmids: List[str]) -> List[Dict]:
        """
        Fetch detailed information for a list of PMIDs.
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            List of paper details
        """
        if not pmids:
            return []
        
        papers = []
        
        # Process in batches of 200
        for i in range(0, len(pmids), 200):
            batch = pmids[i:i+200]
            
            params = {
                'db': 'pubmed',
                'id': ','.join(batch),
                'retmode': 'xml',
                'email': self.email
            }
            
            if self.api_key:
                params['api_key'] = self.api_key
            
            try:
                time.sleep(self.rate_limit)
                
                response = requests.get(
                    f"{self.BASE_URL}efetch.fcgi",
                    params=params,
                    timeout=60
                )
                response.raise_for_status()
                
                # Parse XML
                root = ET.fromstring(response.content)
                
                for article in root.findall('.//PubmedArticle'):
                    paper = self._parse_article(article)
                    if paper:
                        papers.append(paper)
                
            except Exception as e:
                print(f"Error fetching details for batch: {e}")
                continue
        
        return papers
    
    def _parse_article(self, article) -> Optional[Dict]:
        """Parse article XML to extract details"""
        try:
            medline = article.find('.//MedlineCitation')
            pmid = medline.find('.//PMID').text
            
            article_data = medline.find('.//Article')
            
            # Title
            title_elem = article_data.find('.//ArticleTitle')
            title = ''.join(title_elem.itertext()) if title_elem is not None else 'Unknown'
            
            # Authors
            authors = []
            for author in article_data.findall('.//Author'):
                last_name = author.find('.//LastName')
                first_name = author.find('.//ForeName')
                if last_name is not None:
                    name = last_name.text
                    if first_name is not None:
                        name = f"{first_name.text} {name}"
                    authors.append(name)
            
            # Abstract
            abstract_elem = article_data.find('.//Abstract')
            abstract = ''
            if abstract_elem is not None:
                abstract = ' '.join(abstract_elem.itertext())
            
            # Publication date
            pub_date = article_data.find('.//PubDate')
            year = pub_date.find('.//Year').text if pub_date.find('.//Year') is not None else 'Unknown'
            
            # Journal
            journal_elem = article_data.find('.//Journal/Title')
            journal = journal_elem.text if journal_elem is not None else 'Unknown'
            
            return {
                'pmid': pmid,
                'title': title,
                'authors': authors,
                'abstract': abstract,
                'year': year,
                'journal': journal,
                'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            }
            
        except Exception as e:
            print(f"Error parsing article: {e}")
            return None

def load_processed_papers(tracking_file: str) -> set:
    """Load set of already processed PMIDs"""
    if not os.path.exists(tracking_file):
        return set()
    
    try:
        with open(tracking_file, 'r') as f:
            data = json.load(f)
            return set(data.get('processed_pmids', []))
    except Exception as e:
        print(f"Error loading tracking file: {e}")
        return set()

def save_processed_papers(tracking_file: str, pmids: set):
    """Save processed PMIDs to tracking file"""
    os.makedirs(os.path.dirname(tracking_file) or '.', exist_ok=True)
    
    data = {
        'processed_pmids': list(pmids),
        'last_updated': datetime.now().isoformat()
    }
    
    with open(tracking_file, 'w') as f:
        json.dump(data, f, indent=2)

def find_new_papers(query: str, tracking_file: str = 'project/outputs/processed_papers.json',
                    max_results: int = 100, days_back: int = 30) -> List[Dict]:
    """
    Find new papers from PubMed that haven't been processed yet.
    
    Args:
        query: PubMed search query
        tracking_file: File tracking processed papers
        max_results: Maximum results to fetch
        days_back: How many days back to search
        
    Returns:
        List of new paper details
    """
    client = PubMedClient()
    
    # Calculate date range
    from datetime import timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Search PubMed
    pmids = client.search(
        query,
        max_results=max_results,
        min_date=start_date.strftime('%Y/%m/%d'),
        max_date=end_date.strftime('%Y/%m/%d')
    )
    
    # Load already processed papers
    processed = load_processed_papers(tracking_file)
    
    # Filter for new papers only
    new_pmids = [pmid for pmid in pmids if pmid not in processed]
    
    if not new_pmids:
        print("No new papers found.")
        return []
    
    print(f"Found {len(new_pmids)} new papers (out of {len(pmids)} total)")
    
    # Fetch details
    new_papers = client.fetch_details(new_pmids)
    
    return new_papers

def download_paper_pdf(pmid: str, output_dir: str) -> Optional[str]:
    """
    Attempt to download PDF for a PMID (if available).
    Note: Not all papers have freely available PDFs.
    
    Args:
        pmid: PubMed ID
        output_dir: Directory to save PDF
        
    Returns:
        Path to downloaded PDF or None
    """
    # This is a placeholder - actual implementation would need:
    # 1. Check PubMed Central for open access
    # 2. Use institutional access if available
    # 3. Respect copyright
    
    print(f"Note: Automatic PDF download not implemented for PMID {pmid}")
    print(f"Please download manually from: https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
    return None

if __name__ == '__main__':
    # Test the integration
    query = "cancer biomarkers"
    new_papers = find_new_papers(query, max_results=10, days_back=7)
    
    print(f"\nNew papers found: {len(new_papers)}")
    for paper in new_papers[:5]:
        print(f"\n{paper['title']}")
        print(f"Authors: {', '.join(paper['authors'][:3])}")
        print(f"PMID: {paper['pmid']}")