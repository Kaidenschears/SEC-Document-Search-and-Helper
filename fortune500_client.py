from typing import List, Dict
from models import Company
from edgar_client import EDGARClient

class Fortune500Client:
    def __init__(self):
        self.edgar_client = EDGARClient()
        # Top Fortune 500 companies with their CIKs
        # Extended list of Fortune 500 companies with their CIKs
        self.fortune500_ciks = {
            # Technology
            "0000320193": "Apple Inc.",
            "0000789019": "Microsoft Corporation",
            "0001018724": "Amazon.com Inc.",
            "0001652044": "Alphabet Inc.",
            "0001534701": "Meta Platforms Inc.",
            "0001018840": "NVIDIA Corporation",
            "0000858877": "Intel Corporation",
            "0001045810": "NVIDIA Corporation",
            "0000320187": "HP Inc.",
            
            # Finance
            "0001067983": "Berkshire Hathaway Inc.",
            "0000051143": "JPMorgan Chase & Co.",
            "0000037996": "Bank of America Corp.",
            "0000070858": "Citigroup Inc.",
            "0000093410": "Wells Fargo & Company",
            "0000927628": "Goldman Sachs Group Inc.",
            
            # Retail
            "0000093410": "Walmart Inc.",
            "0000063908": "Costco Wholesale Corporation",
            "0000912463": "Home Depot Inc.",
            "0001551152": "Target Corporation",
            
            # Healthcare
            "0000078003": "UnitedHealth Group Inc.",
            "0000064803": "CVS Health Corporation",
            "0001551152": "Johnson & Johnson",
            "0001800157": "Pfizer Inc.",
            
            # Energy
            "0000093410": "ExxonMobil Corporation",
            "0000200406": "Chevron Corporation",
            "0001094517": "ConocoPhillips",
            
            # Manufacturing
            "0000040545": "General Motors Co.",
            "0001324424": "Tesla Inc.",
            "0000037996": "Ford Motor Company",
            
            # Consumer Goods
            "0000027419": "The Coca-Cola Company",
            "0000732717": "The Walt Disney Company",
            "0000077476": "PepsiCo Inc.",
            "0001637459": "Procter & Gamble Company",
            
            # Telecommunications
            "0000732717": "AT&T Inc.",
            "0000732712": "Verizon Communications Inc.",
            "0001283699": "T-Mobile US Inc."
        }
        
    def get_fortune500_companies(self) -> List[Company]:
        """
        Fetch Fortune 500 companies using SEC EDGAR API
        Returns a list of Company objects with enriched data
        """
        companies = []
        errors = []
        
        for cik, name in self.fortune500_ciks.items():
            try:
                # Get company filings to extract SIC and other details
                filings_data = self.edgar_client.get_company_filings(cik)
                
                if not filings_data:
                    raise ValueError(f"No data returned for {name}")
                
                # Extract company information
                company_info = filings_data.get('companyInfo', {})
                sic = str(company_info.get('sic', ''))
                industry = self._get_industry_from_sic(sic)
                
                # Verify the company name from EDGAR data
                edgar_name = company_info.get('name', '')
                if edgar_name and edgar_name != name:
                    print(f"Name mismatch for CIK {cik}: Local={name}, EDGAR={edgar_name}")
                    name = edgar_name  # Use the official name from EDGAR
                
                companies.append(Company(
                    cik=cik,
                    name=name,
                    sic=sic,
                    industry=industry
                ))
                
            except Exception as e:
                error_msg = f"Error fetching data for {name} (CIK: {cik}): {str(e)}"
                print(error_msg)
                errors.append(error_msg)
                
                # Add company with basic information even if API call fails
                companies.append(Company(
                    cik=cik,
                    name=name,
                    sic='',
                    industry='Unknown'
                ))
        
        # Log error summary if any errors occurred
        if errors:
            print(f"\nEncountered {len(errors)} errors while fetching company data:")
            for error in errors:
                print(f"- {error}")
        
        return sorted(companies, key=lambda x: x.name)
    
    def _get_industry_from_sic(self, sic: str) -> str:
        """Map SIC codes to industry categories"""
        # Technology
        if sic in ['7371', '7372', '7373', '7374', '7375', '7376', '7377', '7378', '7379']:
            return 'Technology - Software & Services'
        elif sic in ['3570', '3571', '3572', '3575', '3576', '3577', '3578', '3579']:
            return 'Technology - Hardware'
        
        # Finance
        elif sic in ['6021', '6022', '6029', '6035', '6036']:
            return 'Finance - Banking'
        elif sic in ['6311', '6321', '6331', '6351', '6361', '6399']:
            return 'Finance - Insurance'
        elif sic in ['6211', '6221', '6282', '6289']:
            return 'Finance - Investment Services'
        
        # Retail
        elif sic in ['5211', '5311', '5331', '5399']:
            return 'Retail - Department Stores'
        elif sic in ['5961', '5962', '5963']:
            return 'Retail - E-commerce'
        elif sic in ['5411', '5412', '5422', '5461']:
            return 'Retail - Food & Grocery'
        
        # Healthcare
        elif sic in ['2833', '2834', '2835', '2836']:
            return 'Healthcare - Pharmaceuticals'
        elif sic in ['8011', '8021', '8031', '8041', '8051', '8061', '8071', '8082', '8090']:
            return 'Healthcare - Services'
        elif sic in ['3841', '3842', '3843', '3844', '3845']:
            return 'Healthcare - Equipment'
        
        # Energy
        elif sic in ['2911', '1311', '1381', '1382', '1389']:
            return 'Energy - Oil & Gas'
        elif sic in ['4911', '4931', '4932', '4939']:
            return 'Energy - Utilities'
        
        # Manufacturing
        elif sic in ['3711', '3713', '3714', '3715', '3716']:
            return 'Manufacturing - Automotive'
        elif sic in ['3721', '3724', '3728']:
            return 'Manufacturing - Aerospace'
        
        # Telecommunications
        elif sic in ['4812', '4813', '4822', '4899']:
            return 'Telecommunications'
        
        # Consumer Goods
        elif sic in ['2080', '2082', '2086', '2087']:
            return 'Consumer Goods - Beverages'
        elif sic in ['2000', '2011', '2013', '2015', '2020', '2024']:
            return 'Consumer Goods - Food Products'
        
        return 'Other'
