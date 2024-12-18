import requests
import time
from datetime import datetime, timedelta
import trafilatura
from typing import Dict, List, Optional

class EDGARClient:
    def __init__(self):
        self.base_url = "https://data.sec.gov/submissions"
        self.headers = {
            "User-Agent": "StockAdvisor research@example.com",
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov"
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
        url = f"{self.base_url}/CIK{padded_cik}.json"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch filings: {response.status_code}")

    def get_filing_document(self, accession_number: str, cik: str) -> str:
        """Fetch specific filing document content"""
        self._rate_limit()
        try:
            padded_cik = cik.zfill(10)
            print(f"Fetching document for CIK: {padded_cik}, Accession: {accession_number}")
            
            # First get the company submissions to find the document
            submissions_url = f"{self.base_url}/CIK{padded_cik}.json"
            print(f"Fetching submissions from: {submissions_url}")
            
            submissions_response = requests.get(submissions_url, headers=self.headers)
            if submissions_response.status_code != 200:
                raise Exception(f"Failed to fetch submissions: {submissions_response.status_code}")
            
            submissions_data = submissions_response.json()
            filings = submissions_data.get('filings', {}).get('recent', {})
            if not filings:
                raise Exception("No recent filings found")
            
            # Find the specific filing
            accession_numbers = filings.get('accessionNumber', [])
            if accession_number not in accession_numbers:
                raise Exception(f"Accession number {accession_number} not found in recent filings")
            
            idx = accession_numbers.index(accession_number)
            primary_doc = filings.get('primaryDocument', [])[idx]
            
            # Construct the document URL
            clean_accession = accession_number.replace("-", "")
            doc_url = f"https://www.sec.gov/Archives/edgar/data/{padded_cik}/{clean_accession}/{primary_doc}"
            print(f"Fetching document from: {doc_url}")
            
            # Get the actual document
            self._rate_limit()
            doc_response = requests.get(doc_url, headers=self.headers)
            
            if doc_response.status_code == 200:
                return doc_response.text
            else:
                raise Exception(f"Failed to fetch document content: {doc_response.status_code}")
                
        except Exception as e:
            print(f"Error fetching document for CIK {cik}, accession {accession_number}: {str(e)}")
            raise Exception(f"Failed to fetch document: {str(e)}")

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

            for idx, (form, date, accession, doc) in enumerate(zip(forms, dates, accession_numbers, primary_docs)):
                if form in form_types:
                    filing_date = datetime.strptime(date, '%Y-%m-%d')
                    if filing_date >= cutoff_date:
                        recent_filings.append({
                            'form': form,
                            'filing_date': filing_date,
                            'accession_number': accession,
                            'primary_document': doc
                        })
                        print(f"Found {form} filing from {date} (Accession: {accession})")

            return recent_filings
        except Exception as e:
            print(f"Error getting recent filings for CIK {cik}: {str(e)}")
            raise Exception(f"Failed to fetch recent filings: {str(e)}")
