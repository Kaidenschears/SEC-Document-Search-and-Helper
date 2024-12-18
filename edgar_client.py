import requests
import time
import json
import os
from typing import Dict, List
import trafilatura
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

class EDGARClient:
    def __init__(self):
        self.base_url = "https://www.sec.gov/Archives/edgar/data"
        self.headers = {
            'User-Agent': 'Financial Analysis Tool learning@example.com'
        }
        self.last_request_time = 0
        self.rate_limit_delay = 0.1  # 100ms between requests
        # Initialize company mappings at startup
        self._cached_companies = None
        self._last_cache_update = None
        self._load_company_mappings()  # Preload mappings
    
    def _rate_limit(self):
        """Implement rate limiting to comply with SEC EDGAR guidelines"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last_request)
        self.last_request_time = time.time()
    
    def get_company_filings(self, cik: str) -> Dict:
        """Get company filings data using EDGAR data delivery API"""
        self._rate_limit()
        try:
            padded_cik = cik.zfill(10)
            url = f"https://data.sec.gov/submissions/CIK{padded_cik}.json"
            print(f"Fetching company filings from: {url}")
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"Error fetching company filings: {str(e)}")
            raise Exception(f"Failed to fetch filings: {str(e)}")

    def get_filing_document(self, accession_number: str, cik: str, form_type: str = None) -> str:
        """Fetch specific filing document content using EDGAR data delivery API"""
        self._rate_limit()
        try:
            padded_cik = cik.zfill(10)
            clean_accession = accession_number.replace("-", "")
            
            if form_type == '4':
                # Form 4 documents have a special structure
                print(f"Fetching Form 4 document for CIK {padded_cik}, accession {accession_number}")
                
                # First try the index to find the correct document
                index_url = f"{self.base_url}/{padded_cik}/{clean_accession}/index.json"
                try:
                    self._rate_limit()
                    index_response = requests.get(index_url, headers=self.headers)
                    index_response.raise_for_status()
                    index_data = index_response.json()
                    
                    # Look for form4.xml in the index
                    form4_file = None
                    for file in index_data.get('directory', {}).get('item', []):
                        if file.get('name', '').endswith('.xml') and 'form4' in file.get('name', '').lower():
                            form4_file = file['name']
                            break
                    
                    if form4_file:
                        doc_url = f"{self.base_url}/{padded_cik}/{clean_accession}/{form4_file}"
                        print(f"Found Form 4 XML file, fetching from: {doc_url}")
                        self._rate_limit()
                        doc_response = requests.get(doc_url, headers=self.headers)
                        doc_response.raise_for_status()
                        return doc_response.text
                        
                except Exception as e:
                    print(f"Failed to fetch Form 4 from index: {str(e)}")
                    
                # If index approach fails, try common Form 4 URL patterns
                patterns = [
                    f"{self.base_url}/{padded_cik}/{clean_accession}/form4.xml",
                    f"{self.base_url}/{padded_cik}/{clean_accession}/xslF345X03/form4.xml",
                    f"{self.base_url}/{padded_cik}/{clean_accession}/{clean_accession}.txt",
                    f"{self.base_url}/{padded_cik}/{clean_accession}/primary_doc.xml"
                ]
                
                for pattern in patterns:
                    try:
                        print(f"Trying Form 4 pattern: {pattern}")
                        self._rate_limit()
                        response = requests.get(pattern, headers=self.headers)
                        response.raise_for_status()
                        return response.text
                    except Exception as e:
                        print(f"Failed with pattern {pattern}: {str(e)}")
                        continue
                
                raise Exception("Could not retrieve Form 4 document using any known method")
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
                
        except Exception as e:
            print(f"Error fetching document: {str(e)}")
            raise Exception(f"Failed to fetch document: {str(e)}")
    
    def extract_text_content(self, html_content: str) -> str:
        """Extract readable text from HTML content using trafilatura"""
        result = trafilatura.extract(html_content)
        if result is None:
            return "No readable content found"
        return result

    def parse_form4_content(self, xml_content: str) -> Dict:
        """Parse Form 4 XML content to extract key insider trading information"""
        try:
            root = ET.fromstring(xml_content)
            
            # Extract reporting owner information
            owner_data = root.find(".//reportingOwner")
            if owner_data is None:
                print("No reporting owner found in XML")
                return {"error": "No reporting owner found"}
                
            owner_name = owner_data.find(".//rptOwnerName")
            owner_title = owner_data.find(".//officerTitle")
            
            # Look for both non-derivative and derivative transactions
            transactions = []
            
            # Check non-derivative transactions
            for trans in root.findall(".//nonDerivativeTransaction"):
                try:
                    shares_elem = trans.find(".//transactionShares/value")
                    price_elem = trans.find(".//transactionPricePerShare/value")
                    transaction_code = trans.find(".//transactionCode")
                    
                    if shares_elem is not None and price_elem is not None:
                        transactions.append({
                            "type": "non-derivative",
                            "shares": float(shares_elem.text),
                            "price_per_share": float(price_elem.text),
                            "transaction_code": transaction_code.text if transaction_code is not None else "Unknown"
                        })
                except Exception as e:
                    print(f"Error parsing non-derivative transaction: {str(e)}")
            
            # Check derivative transactions
            for trans in root.findall(".//derivativeTransaction"):
                try:
                    shares_elem = trans.find(".//transactionShares/value")
                    price_elem = trans.find(".//transactionPricePerShare/value")
                    transaction_code = trans.find(".//transactionCode")
                    
                    if shares_elem is not None and price_elem is not None:
                        transactions.append({
                            "type": "derivative",
                            "shares": float(shares_elem.text),
                            "price_per_share": float(price_elem.text),
                            "transaction_code": transaction_code.text if transaction_code is not None else "Unknown"
                        })
                except Exception as e:
                    print(f"Error parsing derivative transaction: {str(e)}")
            
            if not transactions:
                print("No valid transactions found in XML")
                return {"error": "No transaction data found"}
            
            # Calculate total shares and average price for summary
            total_shares = sum(t["shares"] for t in transactions)
            weighted_price = sum(t["shares"] * t["price_per_share"] for t in transactions) / total_shares if total_shares > 0 else 0
            
            # Determine overall transaction type (P = Purchase, S = Sale)
            transaction_codes = [t["transaction_code"] for t in transactions]
            transaction_type = "Purchase" if "P" in transaction_codes else "Sale"
            
            return {
                "owner_name": owner_name.text if owner_name is not None else "Unknown",
                "owner_title": owner_title.text if owner_title is not None else "Unknown Position",
                "transaction_type": transaction_type,
                "shares": total_shares,
                "price_per_share": weighted_price,
                "transactions": transactions  # Include all transactions for detailed view
            }
        except Exception as e:
            print(f"Error parsing Form 4 content: {str(e)}")
            return {"error": f"Failed to parse Form 4 content: {str(e)}"}

    _cached_companies = None
    _last_cache_update = None

    def _load_company_mappings(self):
        """Load company mappings with caching"""
        try:
            # Check if cache is still valid (5 minutes)
            now = time.time()
            if (self._cached_companies is not None and 
                self._last_cache_update is not None and 
                now - self._last_cache_update < 300):
                return self._cached_companies

            mappings_file = "company_mappings.json"
            if not os.path.exists(mappings_file):
                print("Company mappings file not found. Please run update_company_mappings.py first.")
                return {}

            with open(mappings_file, 'r') as f:
                data = json.load(f)
                self._cached_companies = data.get('companies', {})
                self._last_cache_update = now
                return self._cached_companies

        except Exception as e:
            print(f"Error loading company mappings: {str(e)}")
            return {}

    def search_company(self, company_name: str) -> List[Dict]:
        """Search for companies by name using SEC API"""
        self._rate_limit()
        try:
            # SEC's company search API
            url = "https://www.sec.gov/files/company_tickers.json"
            print(f"Searching for company: {company_name}")
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            company_data = response.json()
            
            # Search through the companies
            matches = []
            search_term = company_name.lower()
            
            for _, company in company_data.items():
                if search_term in company['title'].lower():
                    matches.append({
                        'name': company['title'],
                        'cik': str(company['cik_str']).zfill(10),
                        'ticker': company['ticker']
                    })
            
            return matches

        except Exception as e:
            print(f"Error searching for company: {str(e)}")
            return []

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
                        filing_data = {
                            'form': form,
                            'filing_date': filing_date,
                            'accession_number': accession,
                            'primary_document': doc
                        }
                        
                        recent_filings.append(filing_data)
                        print(f"Found {form} filing from {date} (Accession: {accession})")

            return recent_filings
        except Exception as e:
            print(f"Error getting recent filings for CIK {cik}: {str(e)}")
            raise Exception(f"Failed to fetch recent filings: {str(e)}")
