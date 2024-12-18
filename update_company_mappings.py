import json
import requests
import logging
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompanyMappingsUpdater:
    def __init__(self):
        self.base_url = "https://www.sec.gov/files/company_tickers.json"
        self.headers = {
            'User-Agent': 'Financial Analysis Tool learning@example.com'
        }
        self.mappings_file = Path("company_mappings.json")

    def fetch_company_data(self):
        """Fetch company data from SEC"""
        try:
            logger.info("Fetching company data from SEC...")
            response = requests.get(self.base_url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching company data: {str(e)}")
            raise

    def process_company_data(self, data):
        """Process raw company data into a more usable format"""
        processed = {}
        for _, company in data.items():
            processed[company['ticker']] = {
                'name': company['title'],
                'cik': str(company['cik_str']).zfill(10),
                'ticker': company['ticker']
            }
        return processed

    def save_mappings(self, mappings):
        """Save mappings to JSON file"""
        try:
            data_to_save = {
                'last_updated': datetime.now().isoformat(),
                'companies': mappings
            }
            with open(self.mappings_file, 'w') as f:
                json.dump(data_to_save, f, indent=2)
            logger.info(f"Saved {len(mappings)} company mappings to {self.mappings_file}")
        except Exception as e:
            logger.error(f"Error saving mappings: {str(e)}")
            raise

    def update_mappings(self):
        """Main function to update company mappings"""
        try:
            raw_data = self.fetch_company_data()
            processed_data = self.process_company_data(raw_data)
            self.save_mappings(processed_data)
            return True
        except Exception as e:
            logger.error(f"Failed to update mappings: {str(e)}")
            return False

def main():
    updater = CompanyMappingsUpdater()
    success = updater.update_mappings()
    if success:
        logger.info("Successfully updated company mappings")
    else:
        logger.error("Failed to update company mappings")

if __name__ == "__main__":
    main()
