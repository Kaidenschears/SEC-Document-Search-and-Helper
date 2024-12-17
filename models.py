from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Company:
    cik: str
    name: str
    sic: str
    industry: str
    
@dataclass
class Filing:
    id: int
    company_cik: str
    form_type: str
    filing_date: datetime
    document_url: str
    processed_content: str
    created_at: datetime

@dataclass
class FinancialMetric:
    id: int
    company_cik: str
    metric_name: str
    metric_value: float
    as_of_date: datetime
    created_at: datetime

@dataclass
class AnalysisResult:
    id: int
    company_cik: str
    analysis_type: str
    analysis_result: str
    analysis_date: datetime
    created_at: datetime
