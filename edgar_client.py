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
        padded_cik = cik.zfill(10)
        formatted_accession = accession_number.replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/data/{padded_cik}/{formatted_accession}/{accession_number}.txt"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(f"Failed to fetch document: {response.status_code}")

    def extract_text_content(self, html_content: str) -> str:
        """Extract readable text from HTML content using trafilatura"""
        return trafilatura.extract(html_content)

    def get_recent_filings(self, cik: str, form_types: List[str], days_back: int = 30) -> List[Dict]:
        """Get recent filings for a company filtered by form types"""
        filings_data = self.get_company_filings(cik)
        recent_filings = []
        cutoff_date = datetime.now() - timedelta(days=days_back)

        for idx, form in enumerate(filings_data.get('filings', {}).get('recent', {}).get('form', [])):
            if form in form_types:
                filing_date = datetime.strptime(
                    filings_data['filings']['recent']['filingDate'][idx],
                    '%Y-%m-%d'
                )
                if filing_date >= cutoff_date:
                    recent_filings.append({
                        'form': form,
                        'filing_date': filing_date,
                        'accession_number': filings_data['filings']['recent']['accessionNumber'][idx]
                    })

        return recent_filings
