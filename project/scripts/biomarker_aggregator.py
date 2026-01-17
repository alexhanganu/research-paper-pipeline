"""
Biomarker aggregation module for cross-paper analysis.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict
from datetime import datetime

class BiomarkerAggregator:
    """Aggregate and analyze biomarker associations across multiple papers"""
    
    def __init__(self):
        self.biomarkers = defaultdict(lambda: {
            'normalized_name': '',
            'variants': set(),
            'diseases': defaultdict(lambda: {
                'papers': set(),
                'association_types': set(),
                'evidence_levels': set()
            }),
            'total_mentions': 0,
            'first_seen': None,
            'last_seen': None
        })
    
    def normalize_biomarker_name(self, name: str) -> str:
        """
        Normalize biomarker names to handle variants.
        Examples: BRCA1, BRCA-1, brca1 -> BRCA1
        
        Args:
            name: Raw biomarker name
            
        Returns:
            Normalized name
        """
        if not name:
            return ""
        
        # Remove common separators and convert to uppercase
        normalized = re.sub(r'[-_\s]', '', name).upper()
        
        # Handle common patterns
        # Gene names: remove prefixes like "gene:", "protein:"
        normalized = re.sub(r'^(GENE|PROTEIN|BIOMARKER):', '', normalized)
        
        return normalized
    
    def add_paper_results(self, paper_result: Dict):
        """
        Add biomarker data from a single paper's results.
        
        Args:
            paper_result: Dictionary containing paper processing results
        """
        filename = paper_result.get('filename', 'unknown')
        paper_title = paper_result.get('title', 'Unknown')
        biomarkers_data = paper_result.get('biomarkers', [])
        
        if not biomarkers_data:
            return
        
        timestamp = datetime.now().isoformat()
        
        for biomarker in biomarkers_data:
            if isinstance(biomarker, dict):
                raw_name = biomarker.get('name', '')
                diseases = biomarker.get('diseases', [])
                assoc_type = biomarker.get('association_type', 'unknown')
                evidence = biomarker.get('evidence_level', 'unknown')
            else:
                continue
            
            if not raw_name:
                continue
            
            # Normalize name
            normalized = self.normalize_biomarker_name(raw_name)
            
            # Update biomarker data
            bio_data = self.biomarkers[normalized]
            bio_data['normalized_name'] = normalized
            bio_data['variants'].add(raw_name)
            bio_data['total_mentions'] += 1
            
            if bio_data['first_seen'] is None:
                bio_data['first_seen'] = timestamp
            bio_data['last_seen'] = timestamp
            
            # Add disease associations
            for disease in diseases:
                if disease:
                    disease_data = bio_data['diseases'][disease.lower()]
                    disease_data['papers'].add(filename)
                    disease_data['association_types'].add(assoc_type)
                    disease_data['evidence_levels'].add(evidence)
    
    def get_summary(self) -> Dict:
        """
        Get summary statistics of aggregated biomarkers.
        
        Returns:
            Dictionary with summary stats
        """
        total_biomarkers = len(self.biomarkers)
        total_associations = sum(
            len(bio['diseases']) 
            for bio in self.biomarkers.values()
        )
        
        # Top biomarkers by mention count
        top_biomarkers = sorted(
            [(name, data['total_mentions']) for name, data in self.biomarkers.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Top diseases
        all_diseases = defaultdict(int)
        for bio_data in self.biomarkers.values():
            for disease in bio_data['diseases'].keys():
                all_diseases[disease] += len(bio_data['diseases'][disease]['papers'])
        
        top_diseases = sorted(all_diseases.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_unique_biomarkers': total_biomarkers,
            'total_biomarker_disease_associations': total_associations,
            'top_biomarkers': [
                {'name': name, 'mentions': count} 
                for name, count in top_biomarkers
            ],
            'top_diseases': [
                {'disease': disease, 'association_count': count}
                for disease, count in top_diseases
            ]
        }
    
    def get_biomarker_details(self, biomarker_name: str) -> Dict:
        """
        Get detailed information about a specific biomarker.
        
        Args:
            biomarker_name: Biomarker name (will be normalized)
            
        Returns:
            Detailed biomarker information
        """
        normalized = self.normalize_biomarker_name(biomarker_name)
        
        if normalized not in self.biomarkers:
            return None
        
        bio_data = self.biomarkers[normalized]
        
        # Convert sets to lists for JSON serialization
        diseases_list = []
        for disease, data in bio_data['diseases'].items():
            diseases_list.append({
                'disease': disease,
                'paper_count': len(data['papers']),
                'papers': list(data['papers']),
                'association_types': list(data['association_types']),
                'evidence_levels': list(data['evidence_levels'])
            })
        
        return {
            'normalized_name': bio_data['normalized_name'],
            'name_variants': list(bio_data['variants']),
            'total_mentions': bio_data['total_mentions'],
            'disease_associations': diseases_list,
            'first_seen': bio_data['first_seen'],
            'last_seen': bio_data['last_seen']
        }
    
    def export_to_json(self, output_path: str):
        """
        Export aggregated biomarker data to JSON file.
        
        Args:
            output_path: Path to save JSON file
        """
        # Convert to serializable format
        export_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'total_biomarkers': len(self.biomarkers)
            },
            'summary': self.get_summary(),
            'biomarkers': {}
        }
        
        for name in self.biomarkers.keys():
            export_data['biomarkers'][name] = self.get_biomarker_details(name)
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Biomarker data exported to: {output_path}")
    
    def export_to_csv(self, output_path: str):
        """
        Export biomarker-disease associations to CSV.
        
        Args:
            output_path: Path to save CSV file
        """
        import csv
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Biomarker',
                'Disease',
                'Paper Count',
                'Association Types',
                'Evidence Levels',
                'Total Mentions',
                'Name Variants'
            ])
            
            for biomarker_name in sorted(self.biomarkers.keys()):
                bio_data = self.biomarkers[biomarker_name]
                
                for disease, disease_data in bio_data['diseases'].items():
                    writer.writerow([
                        bio_data['normalized_name'],
                        disease,
                        len(disease_data['papers']),
                        ', '.join(disease_data['association_types']),
                        ', '.join(disease_data['evidence_levels']),
                        bio_data['total_mentions'],
                        ', '.join(list(bio_data['variants'])[:3])
                    ])
        
        print(f"Biomarker associations exported to: {output_path}")
    
    def find_high_confidence_associations(self, min_papers: int = 3) -> List[Dict]:
        """
        Find biomarker-disease associations mentioned in multiple papers.
        
        Args:
            min_papers: Minimum number of papers required
            
        Returns:
            List of high-confidence associations
        """
        high_confidence = []
        
        for biomarker_name, bio_data in self.biomarkers.items():
            for disease, disease_data in bio_data['diseases'].items():
                paper_count = len(disease_data['papers'])
                
                if paper_count >= min_papers:
                    high_confidence.append({
                        'biomarker': bio_data['normalized_name'],
                        'disease': disease,
                        'paper_count': paper_count,
                        'association_types': list(disease_data['association_types']),
                        'evidence_levels': list(disease_data['evidence_levels']),
                        'confidence_score': min(paper_count / 10.0, 1.0)  # 0-1 scale
                    })
        
        # Sort by paper count
        high_confidence.sort(key=lambda x: x['paper_count'], reverse=True)
        
        return high_confidence

def aggregate_from_results(results_file: str) -> BiomarkerAggregator:
    """
    Create aggregator from a results JSON file.
    
    Args:
        results_file: Path to paper_summaries_*.json file
        
    Returns:
        BiomarkerAggregator with loaded data
    """
    aggregator = BiomarkerAggregator()
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    for paper_result in results:
        aggregator.add_paper_results(paper_result)
    
    return aggregator

if __name__ == '__main__':
    import os
    
    # Test aggregation
    aggregator = BiomarkerAggregator()
    
    # Sample data
    sample_papers = [
        {
            'filename': 'paper1.pdf',
            'title': 'BRCA1 in breast cancer',
            'biomarkers': [
                {
                    'name': 'BRCA1',
                    'diseases': ['breast cancer', 'ovarian cancer'],
                    'association_type': 'causal',
                    'evidence_level': 'clinical_trial'
                }
            ]
        },
        {
            'filename': 'paper2.pdf',
            'title': 'BRCA-1 mutations',
            'biomarkers': [
                {
                    'name': 'BRCA-1',  # Variant spelling
                    'diseases': ['breast cancer'],
                    'association_type': 'causal',
                    'evidence_level': 'meta_analysis'
                }
            ]
        }
    ]
    
    for paper in sample_papers:
        aggregator.add_paper_results(paper)
    
    summary = aggregator.get_summary()
    print("Summary:", json.dumps(summary, indent=2))
    
    print("\nBRCA1 details:")
    print(json.dumps(aggregator.get_biomarker_details('BRCA1'), indent=2))