import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import os

from edgar_client import EDGARClient
from database import Database
from financial_analysis import FinancialAnalyzer
from llm_analyzer import LLMAnalyzer
from models import Company
from utils import cache_data, format_currency, format_percentage
from fortune500_client import Fortune500Client

# Initialize components
edgar_client = EDGARClient()
db = Database()
financial_analyzer = FinancialAnalyzer()
llm_analyzer = LLMAnalyzer()
fortune500_client = Fortune500Client()

# Initialize database tables
db.initialize_tables()

# Function to refresh Fortune 500 data
def refresh_fortune500_data():
    companies = fortune500_client.get_fortune500_companies()
    for company in companies:
        db.upsert_company(company)
    return companies

def show_fortune500():
    try:
        st.title("Fortune 500 Companies")
        
        # Add refresh button
        if st.button("🔄 Refresh Data"):
            with st.spinner("Refreshing Fortune 500 data..."):
                refresh_fortune500_data()
                st.success("Data refreshed successfully!")
        
        # Get companies from database
        companies = db.get_all_companies()
        
        if not companies:
            with st.spinner("Loading Fortune 500 data for the first time..."):
                refresh_fortune500_data()
                companies = db.get_all_companies()
        
        # Group companies by industry
        df = pd.DataFrame(companies)
        industries = sorted(df['industry'].unique())
        
        # Industry filter
        selected_industry = st.selectbox(
            "Filter by Industry",
            ["All Industries"] + list(industries)
        )
        
        st.write("Click on a company to view its analysis:")
        
        # Filter companies by selected industry
        filtered_companies = companies
        if selected_industry != "All Industries":
            filtered_companies = [c for c in companies if c['industry'] == selected_industry]
        
        # Create columns for better layout
        cols = st.columns(2)
        for idx, company in enumerate(filtered_companies):
            col = cols[idx % 2]
            if col.button(company['name'], key=f"company_{company['cik']}", use_container_width=True):
                st.session_state['selected_cik'] = company['cik']
                st.session_state['page'] = 'analysis'
                st.experimental_rerun()
                
    except Exception as e:
        st.error(f"Error loading Fortune 500 page: {str(e)}")
        st.session_state['page'] = 'home'

def main():
    st.title("SEC Financial Document Search")
    
    # Company search section
    st.subheader("Search Company")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        company_search = st.text_input(
            "Enter Company Name or CIK:",
            help="Enter a company name (e.g., 'Apple Inc.') or CIK number"
        )
    
    with col2:
        form_type = st.selectbox(
            "Document Type",
            ["10-K", "10-Q", "8-K", "4", "All"],
            help="Select the type of financial document (Form 4 contains insider trading information)"
        )
    
    if company_search:
        if company_search.isdigit():
            # Direct CIK lookup
            cik = company_search.zfill(10)
        else:
            # Use example CIK for now - we'll enhance this later
            common_companies = {
                "apple": "0000320193",
                "microsoft": "0000789019",
                "amazon": "0001018724",
                "google": "0001652044",
                "meta": "0001326801",
            }
            cik = common_companies.get(company_search.lower().split()[0], None)
            
            if not cik:
                st.warning("Company not found. Please try another name or use CIK number.")
                return
        
        # Fetch and display filings
        try:
            filings = edgar_client.get_recent_filings(
                cik,
                form_types=[form_type] if form_type != "All" else ["10-K", "10-Q", "8-K"],
                days_back=365
            )
            
            if filings:
                st.subheader("Recent Filings")
                for filing in filings:
                    filing_date = filing['filing_date'].strftime('%Y-%m-%d')
                    if filing['form'] == '4':
                        # Special display for Form 4 (Insider Trading)
                        with st.expander(f"Form 4 - Insider Trading ({filing_date})"):
                            st.write("**Insider Trading Information**")
                            st.write(f"Reporting Owner: {filing.get('reporting_owner', 'N/A')}")
                            shares = filing.get('transaction_shares')
                            price = filing.get('price_per_share')
                            if shares and price:
                                st.write(f"Transaction: {shares:,} shares @ ${price:,.2f} per share")
                                st.write(f"Total Value: ${shares * price:,.2f}")
                            
                            if st.button("View Full Document", key=filing['accession_number']):
                                doc_content = edgar_client.get_filing_document(
                                    filing['accession_number'],
                                    cik
                                )
                                readable_content = edgar_client.extract_text_content(doc_content)
                                st.text_area("Document Content", readable_content, height=400)
                    else:
                        # Standard display for other forms
                        with st.expander(f"{filing['form']} - {filing_date}"):
                            if st.button("View Document", key=filing['accession_number']):
                                doc_content = edgar_client.get_filing_document(
                                    filing['accession_number'],
                                    cik
                                )
                                readable_content = edgar_client.extract_text_content(doc_content)
                                st.text_area("Document Content", readable_content, height=400)
            else:
                st.info("No filings found for the specified criteria.")
                
        except Exception as e:
            st.error(f"Error fetching filings: {str(e)}")

def run_analysis(cik: str):
    # Create tabs for different views
    tabs = st.tabs(["Overview", "SEC Filings", "Financial Analysis", "AI Insights"])
    
    with tabs[0]:
        show_overview(cik)
    
    with tabs[1]:
        show_sec_filings(cik)
    
    with tabs[2]:
        show_financial_analysis(cik)
    
    with tabs[3]:
        show_ai_insights(cik)

@cache_data(ttl_seconds=3600)
def show_overview(cik: str):
    st.header("Company Overview")
    
    # Fetch recent filings
    recent_filings = edgar_client.get_recent_filings(
        cik,
        form_types=['10-K', '10-Q', '8-K'],
        days_back=90
    )
    
    # Display key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Recent Filings", len(recent_filings))
    
    with col2:
        financial_metrics = db.get_financial_metrics(cik)
        if financial_metrics:
            latest_pe = next((m for m in financial_metrics if m['metric_name'] == 'pe_ratio'), None)
            if latest_pe:
                st.metric("P/E Ratio", f"{latest_pe['metric_value']:.2f}")
    
    with col3:
        if financial_metrics:
            latest_roe = next((m for m in financial_metrics if m['metric_name'] == 'roe'), None)
            if latest_roe:
                st.metric("ROE", f"{latest_roe['metric_value']:.2%}")

def show_sec_filings(cik: str):
    st.header("SEC Filings Analysis")
    
    # Fetch recent filings
    filings = db.get_recent_filings(cik)
    
    if filings:
        df = pd.DataFrame(filings)
        st.dataframe(df[['form_type', 'filing_date', 'document_url']])
        
        # Add filing analysis
        selected_filing = st.selectbox(
            "Select filing to analyze:",
            options=df['id'].tolist(),
            format_func=lambda x: f"{df[df['id']==x]['form_type'].iloc[0]} - {df[df['id']==x]['filing_date'].iloc[0]}"
        )
        
        if selected_filing:
            filing = df[df['id'] == selected_filing].iloc[0]
            analysis = llm_analyzer.analyze_filing(filing['processed_content'], filing['form_type'])
            
            st.subheader("AI Analysis")
            st.write(analysis['analysis'])
            
            st.subheader("Key Points")
            for point in analysis['key_points']:
                st.markdown(f"- {point}")

def show_financial_analysis(cik: str):
    st.header("Financial Analysis")
    
    metrics = db.get_financial_metrics(cik)
    
    if metrics:
        # Create time series visualization
        df = pd.DataFrame(metrics)
        df['as_of_date'] = pd.to_datetime(df['as_of_date'])
        
        # Plot financial metrics over time
        fig = go.Figure()
        
        for metric in financial_analyzer.key_metrics:
            metric_data = df[df['metric_name'] == metric]
            if not metric_data.empty:
                fig.add_trace(go.Scatter(
                    x=metric_data['as_of_date'],
                    y=metric_data['metric_value'],
                    name=metric
                ))
        
        fig.update_layout(
            title="Financial Metrics Over Time",
            xaxis_title="Date",
            yaxis_title="Value",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig)
        
        # Display current metrics
        st.subheader("Current Metrics")
        current_metrics = {}
        for metric in metrics:
            if metric['metric_name'] not in current_metrics:
                current_metrics[metric['metric_name']] = metric['metric_value']
        
        col1, col2 = st.columns(2)
        for i, (metric, value) in enumerate(current_metrics.items()):
            with col1 if i % 2 == 0 else col2:
                st.metric(metric, f"{value:.2f}")

def show_ai_insights(cik: str):
    st.header("AI Insights and Recommendations")
    
    # Fetch recent data
    filings = db.get_recent_filings(cik)
    metrics = db.get_financial_metrics(cik)
    
    if filings and metrics:
        # Generate trading recommendation
        recommendation = llm_analyzer.generate_trading_recommendation(
            financial_metrics={m['metric_name']: m['metric_value'] for m in metrics},
            recent_filings=[{
                'type': f['form_type'],
                'date': f['filing_date'],
                'content': f['processed_content'][:1000]
            } for f in filings],
            market_context="Current market conditions..."  # This would come from market data source
        )
        
        st.subheader("Trading Recommendation")
        st.write(recommendation['recommendation'])
        
        st.subheader("Confidence Score")
        st.progress(recommendation['confidence_score'])
        
        st.subheader("Reasoning")
        for point in recommendation['reasoning']:
            st.markdown(f"- {point}")

if __name__ == "__main__":
    main()
