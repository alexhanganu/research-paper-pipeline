"""
LangChain-based pipeline for research paper processing with structured output.
"""

import os
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from tenacity import retry, stop_after_attempt, wait_exponential

class BiomarkerAssociation(BaseModel):
    """Model for biomarker-disease associations"""
    name: str = Field(description="Biomarker name (gene, protein, or metabolite)")
    diseases: List[str] = Field(description="Associated diseases or conditions")
    association_type: str = Field(description="Type of association: causal, correlative, predictive, etc.")
    evidence_level: str = Field(description="Evidence level: clinical_trial, observational, meta_analysis, in_vitro, etc.")

class PaperExtraction(BaseModel):
    """Structured output model for paper extraction"""
    title: str = Field(description="Paper title")
    authors: str = Field(description="Comma-separated list of authors")
    year: str = Field(description="Publication year (YYYY format)")
    abstract: str = Field(description="Brief 2-3 sentence summary of the paper")
    research_question: str = Field(description="Main research question or objective")
    methodology: str = Field(description="Brief description of methodology used")
    key_findings: List[str] = Field(description="List of 3-5 key findings")
    conclusions: str = Field(description="Main conclusions of the study")
    limitations: str = Field(description="Study limitations mentioned by authors")
    future_work: str = Field(description="Suggested future research directions")
    biomarkers: List[BiomarkerAssociation] = Field(
        description="List of biomarker-disease associations found in the paper",
        default_factory=list
    )

class LangChainPaperProcessor:
    """LangChain-based paper processor with structured output"""
    
    def __init__(self, provider='anthropic', api_key=None):
        """
        Initialize the LangChain processor.
        
        Args:
            provider: 'anthropic' or 'openai'
            api_key: API key (if None, reads from environment)
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self.parser = PydanticOutputParser(pydantic_object=PaperExtraction)
        self.chain = self._create_chain()
    
    def _create_chain(self):
        """Create the LangChain extraction chain"""
        
        prompt = PromptTemplate(
            template="""You are an expert research paper analyst. Extract comprehensive information from the following research paper.

Pay special attention to:
1. Biomarker-disease associations (genes, proteins, metabolites linked to diseases)
2. Clinical relevance and evidence quality
3. Methodological rigor

{format_instructions}

Research Paper:
{paper_text}

Provide a complete and accurate extraction. If information is not available, use "Not found" for string fields or empty lists for list fields.""",
            input_variables=["paper_text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        # Initialize appropriate LLM
        if self.provider == 'anthropic':
            if self.api_key is None:
                self.api_key = os.environ.get('ANTHROPIC_API_KEY')
            llm = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                api_key=self.api_key,
                temperature=0.3,
                max_tokens=4000
            )
        elif self.provider == 'openai':
            if self.api_key is None:
                self.api_key = os.environ.get('OPENAI_API_KEY')
            llm = ChatOpenAI(
                model="gpt-4o",
                api_key=self.api_key,
                temperature=0.3,
                max_tokens=4000
            )
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
        
        return LLMChain(llm=llm, prompt=prompt, output_parser=self.parser)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def process_paper(self, text: str, filename: str) -> dict:
        """
        Process a paper with retry logic.
        
        Args:
            text: The paper text
            filename: Name of the paper file
            
        Returns:
            dict with extracted information
        """
        try:
            # Chunk text if necessary
            chunks = self._chunk_text(text)
            
            # Process first chunk (or combine if needed)
            result = self.chain.invoke({"paper_text": chunks[0]})
            
            # Convert Pydantic model to dict
            if hasattr(result, 'dict'):
                extraction = result.dict()
            elif isinstance(result, dict):
                extraction = result
            else:
                extraction = json.loads(str(result))
            
            # Add metadata
            extraction['filename'] = filename
            extraction['status'] = 'success'
            extraction['chunks_processed'] = len(chunks)
            extraction['api_provider'] = self.provider
            extraction['processing_method'] = 'langchain'
            
            # Calculate quality score
            extraction = self._validate_extraction(extraction)
            
            return extraction
            
        except Exception as e:
            return {
                'filename': filename,
                'status': 'error',
                'error': str(e),
                'api_provider': self.provider,
                'processing_method': 'langchain'
            }
    
    def _chunk_text(self, text: str, max_chars: int = 100000) -> List[str]:
        """Split text into chunks if necessary"""
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
    
    def _validate_extraction(self, result: dict) -> dict:
        """Validate extracted information and calculate quality score"""
        checks = {
            'has_title': bool(result.get('title') and result['title'] != 'Not found' and len(result['title']) > 5),
            'has_authors': bool(result.get('authors') and result['authors'] != 'Not found'),
            'has_findings': bool(result.get('key_findings') and len(result.get('key_findings', [])) > 0),
            'has_year': self._validate_year(result.get('year')),
            'sufficient_abstract': len(result.get('abstract', '')) > 50,
            'has_methodology': bool(result.get('methodology') and result['methodology'] != 'Not found' and len(result['methodology']) > 20),
            'has_biomarkers': len(result.get('biomarkers', [])) > 0
        }
        
        result['quality_score'] = sum(checks.values()) / len(checks)
        result['quality_checks'] = checks
        
        return result
    
    def _validate_year(self, year_str: str) -> bool:
        """Validate publication year"""
        if not year_str or year_str == 'Not found':
            return False
        try:
            year = int(year_str)
            return 1900 <= year <= 2026
        except (ValueError, TypeError):
            return False

def process_paper_with_langchain(text: str, filename: str, api_key: str = None, provider: str = 'anthropic') -> dict:
    """
    Convenience function to process a paper using LangChain.
    
    Args:
        text: The paper text
        filename: Name of the paper file
        api_key: API key (optional)
        provider: 'anthropic' or 'openai'
        
    Returns:
        dict with extracted information
    """
    processor = LangChainPaperProcessor(provider=provider, api_key=api_key)
    return processor.process_paper(text, filename)

if __name__ == '__main__':
    # Test with sample text
    sample_text = """
    Title: BRCA1 Mutations and Breast Cancer Risk
    Authors: Smith J, Doe J, Johnson M
    Year: 2023
    
    Abstract: This study examines the relationship between BRCA1 mutations and breast cancer risk
    in a cohort of 5,000 women. We found that BRCA1 mutation carriers have a 65% lifetime risk
    of developing breast cancer.
    
    Methods: Prospective cohort study with 10-year follow-up.
    
    Results: BRCA1 mutations strongly associated with breast cancer (HR=5.2, p<0.001).
    Also found associations with ovarian cancer risk.
    """
    
    print("Testing LangChain pipeline...")
    result = process_paper_with_langchain(sample_text, "test.pdf", provider='anthropic')
    print(json.dumps(result, indent=2))