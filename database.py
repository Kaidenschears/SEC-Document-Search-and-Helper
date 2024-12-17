import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

class Database:
    def __init__(self):
        self.conn_params = {
            'dbname': os.environ['PGDATABASE'],
            'user': os.environ['PGUSER'],
            'password': os.environ['PGPASSWORD'],
            'host': os.environ['PGHOST'],
            'port': os.environ['PGPORT']
        }

    @contextmanager
    def get_connection(self):
        conn = psycopg2.connect(**self.conn_params)
        try:
            yield conn
        finally:
            conn.close()

    def initialize_tables(self):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Create filings table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS filings (
                        id SERIAL PRIMARY KEY,
                        company_cik TEXT,
                        form_type TEXT,
                        filing_date DATE,
                        document_url TEXT,
                        processed_content TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create financial metrics table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS financial_metrics (
                        id SERIAL PRIMARY KEY,
                        company_cik TEXT,
                        metric_name TEXT,
                        metric_value FLOAT,
                        as_of_date DATE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create analysis results table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_results (
                        id SERIAL PRIMARY KEY,
                        company_cik TEXT,
                        analysis_type TEXT,
                        analysis_result TEXT,
                        analysis_date DATE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            conn.commit()

    def store_filing(self, cik, form_type, filing_date, document_url, processed_content):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO filings (company_cik, form_type, filing_date, document_url, processed_content)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (cik, form_type, filing_date, document_url, processed_content))
                filing_id = cur.fetchone()[0]
                conn.commit()
                return filing_id

    def store_financial_metric(self, cik, metric_name, metric_value, as_of_date):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO financial_metrics (company_cik, metric_name, metric_value, as_of_date)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (cik, metric_name, metric_value, as_of_date))
                metric_id = cur.fetchone()[0]
                conn.commit()
                return metric_id

    def get_recent_filings(self, cik, limit=10):
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM filings 
                    WHERE company_cik = %s 
                    ORDER BY filing_date DESC 
                    LIMIT %s
                """, (cik, limit))
                return cur.fetchall()

    def get_financial_metrics(self, cik):
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM financial_metrics 
                    WHERE company_cik = %s 
                    ORDER BY as_of_date DESC
                """, (cik,))
                return cur.fetchall()
