import requests
import time
from datetime import datetime, timedelta
import trafilatura
from typing import Dict, List, Optional

class EDGARClient:
    def __init__(self):
        self.base_url = "https://www.sec.gov/Archives/edgar/data"
        self.submissions_url = "https://data.sec.gov/submissions"
        self.headers = {
            "User-Agent": "StockAdvisor research@example.com",
            "Accept-Encoding": "gzip, deflate",
        }
        self.last_request_time = 0
        self.rate_limit_delay = 0.1  # 100ms between requests

    def _rate_limit(self):
        """Implement rate limiting to comply with SEC EDGAR guidelines"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last_request)
        self.last_request_time = time.time()

    def get_company_filings(self, cik: str) -> Dict:
        """Fetch company filings from SEC EDGAR"""
        self._rate_limit()
        padded_cik = cik.zfill(10)
        url = f"{self.submissions_url}/CIK{padded_cik}.json"
        print(f"Fetching company filings from: {url}")
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching company filings: {str(e)}")
            raise Exception(f"Failed to fetch filings: {str(e)}")

    def get_filing_document(self, accession_number: str, cik: str, form_type: str = None) -> str:
        """Fetch specific filing document content using EDGAR data delivery API"""
        self._rate_limit()
        try:
            padded_cik = cik.zfill(10)
            clean_accession = accession_number.replace("-", "")
            
            if form_type == '4':
                # Form 4 documents can be accessed directly
                doc_url = f"{self.base_url}/{padded_cik}/{clean_accession}/{accession_number}.xml"
                print(f"Fetching Form 4 document from: {doc_url}")
                
                self._rate_limit()
                doc_response = requests.get(doc_url, headers=self.headers)
                doc_response.raise_for_status()
                
                return doc_response.text
            else:
                # For other forms, get the index first
                index_url = f"{self.base_url}/{padded_cik}/{clean_accession}/index.json"
                print(f"Fetching filing index from: {index_url}")
                
                index_response = requests.get(index_url, headers=self.headers)
                index_response.raise_for_status()
                
                # Parse index to find the main document
                index_data = index_response.json()
                main_doc = None
                
                for file_entry in index_data.get('directory', {}).get('item', []):
                    if (file_entry.get('type') == form_type or 
                        file_entry.get('name', '').endswith('.htm')):
                        main_doc = file_entry['name']
                        break
                
                if not main_doc:
                    # Try the primary document directly
                    main_doc = f"{clean_accession}.txt"
                
                # Get the actual document
                doc_url = f"{self.base_url}/{padded_cik}/{clean_accession}/{main_doc}"
                print(f"Fetching document from: {doc_url}")
                
                self._rate_limit()
                doc_response = requests.get(doc_url, headers=self.headers)
                doc_response.raise_for_status()
                
                return doc_response.text
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching document: {str(e)}")
            raise Exception(f"Failed to fetch document: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise Exception(f"Failed to process document: {str(e)}")

    def extract_text_content(self, html_content: str) -> str:
        """Extract readable text from HTML content using trafilatura"""
        return trafilatura.extract(html_content)

    def get_recent_filings(self, cik: str, form_types: List[str], days_back: int = 30) -> List[Dict]:
        """Get recent filings for a company filtered by form types"""
        try:
            print(f"Fetching recent filings for CIK: {cik}")
            filings_data = self.get_company_filings(cik)
            recent_filings = []
            cutoff_date = datetime.now() - timedelta(days=days_back)

            recent = filings_data.get('filings', {}).get('recent', {})
            if not recent:
                print(f"No recent filings found for CIK: {cik}")
                return []

            forms = recent.get('form', [])
            dates = recent.get('filingDate', [])
            accession_numbers = recent.get('accessionNumber', [])
            primary_docs = recent.get('primaryDocument', [])
            # Additional data for Form 4
            reporting_owners = recent.get('reportingOwner', [])
            transaction_amounts = recent.get('transactionShares', [])
            transaction_prices = recent.get('transactionPricePerShare', [])

            for idx, (form, date, accession, doc) in enumerate(zip(forms, dates, accession_numbers, primary_docs)):
                if form in form_types:
                    filing_date = datetime.strptime(date, '%Y-%m-%d')
                    if filing_date >= cutoff_date:
                        filing_data = {
                            'form': form,
                            'filing_date': filing_date,
                            'accession_number': accession,
                            'primary_document': doc
                        }
                        
                        # Add insider trading details for Form 4
                        if form == '4':
                            try:
                                filing_data.update({
                                    'reporting_owner': reporting_owners[idx] if idx < len(reporting_owners) else 'Unknown',
                                    'transaction_shares': transaction_amounts[idx] if idx < len(transaction_amounts) else None,
                                    'price_per_share': transaction_prices[idx] if idx < len(transaction_prices) else None
                                })
                            except IndexError:
                                print(f"Warning: Missing insider trading details for filing {accession}")
                        
                        recent_filings.append(filing_data)
                        print(f"Found {form} filing from {date} (Accession: {accession})")

            return recent_filings
        except Exception as e:
            print(f"Error getting recent filings for CIK {cik}: {str(e)}")
            raise Exception(f"Failed to fetch recent filings: {str(e)}")
