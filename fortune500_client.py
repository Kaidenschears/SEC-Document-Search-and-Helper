from typing import List, Dict
from models import Company
from edgar_client import EDGARClient

class Fortune500Client:
    def __init__(self):
        self.edgar_client = EDGARClient()
        # Top Fortune 500 companies with their CIKs
        self.fortune500_ciks = {
            "0000320193": "Apple Inc.",
            "0000789019": "Microsoft Corporation",
            "0001018724": "Amazon.com Inc.",
            "0001652044": "Alphabet Inc.",
            "0001067983": "Berkshire Hathaway Inc.",
            "0000051143": "JPMorgan Chase & Co.",
            "0000093410": "Walmart Inc.",
            "0000078003": "United Health Group Inc.",
            "0000037996": "Bank of America Corp.",
            "0000200406": "Chevron Corporation",
            "0001534701": "Meta Platforms Inc.",
            "0000040545": "General Motors Co.",
            "0000027419": "The Coca-Cola Company",
            "0000732717": "The Walt Disney Company",
            "0001018840": "NVIDIA Corporation"
            # We can add more companies as needed
        }
        
    def get_fortune500_companies(self) -> List[Company]:
        """
        Fetch Fortune 500 companies using SEC EDGAR API
        Returns a list of Company objects with enriched data
        """
        companies = []
        
        for cik, name in self.fortune500_ciks.items():
            try:
                # Get company filings to extract SIC and other details
                filings_data = self.edgar_client.get_company_filings(cik)
                
                # Extract industry/sector information from filing data
                sic = str(filings_data.get('sic', ''))
                industry = self._get_industry_from_sic(sic)
                
                companies.append(Company(
                    cik=cik,
                    name=name,
                    sic=sic,
                    industry=industry
                ))
                
            except Exception as e:
                print(f"Error fetching data for {name} (CIK: {cik}): {str(e)}")
                # Still add the company with basic information
                companies.append(Company(
                    cik=cik,
                    name=name,
                    sic='',
                    industry='Unknown'
                ))
        
        return companies
    
    def _get_industry_from_sic(self, sic: str) -> str:
        """Map SIC codes to industry categories"""
        sic_map = {
            '7372': 'Technology - Software',
            '3571': 'Technology - Hardware',
            '5961': 'Retail - E-commerce',
            '6331': 'Finance - Insurance',
            '6021': 'Finance - Banking',
            '5331': 'Retail - Department Stores',
            '2834': 'Healthcare',
            '2911': 'Energy',
            '7370': 'Technology Services',
            '3711': 'Automotive'
        }
        
        return sic_map.get(sic, 'Other')
