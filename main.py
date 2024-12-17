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

# Initialize components
edgar_client = EDGARClient()
db = Database()
financial_analyzer = FinancialAnalyzer()
llm_analyzer = LLMAnalyzer()

# Initialize database tables
db.initialize_tables()

def show_fortune500():
    try:
        st.title("Fortune 500 Companies")
        st.markdown("### Top Tech Companies")
        
        # Sample Fortune 500 companies with their CIKs
        fortune500 = {
            "Apple Inc.": "0000320193",
            "Microsoft Corporation": "0000789019",
            "Amazon.com Inc.": "0001018724",
            "Alphabet Inc. (Google)": "0001652044",
            "Meta Platforms Inc.": "0001326801",
        }
        
        st.write("Click on a company to view its analysis:")
        
        # Create columns for better layout
        cols = st.columns(2)
        for idx, (company, cik) in enumerate(fortune500.items()):
            col = cols[idx % 2]
            if col.button(company, key=f"company_{cik}", use_container_width=True):
                st.session_state['selected_cik'] = cik
                st.session_state['page'] = 'analysis'
                st.experimental_rerun()
                
    except Exception as e:
        st.error(f"Error loading Fortune 500 page: {str(e)}")
        st.session_state['page'] = 'home'

def main():
    st.title("Intelligent Stock Advisory System")
    
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state['page'] = 'home'
    if 'selected_cik' not in st.session_state:
        st.session_state['selected_cik'] = None
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    if st.sidebar.button("Fortune 500 Companies"):
        st.session_state['page'] = 'fortune500'
        st.rerun()
    
    # Manual CIK input
    st.sidebar.title("Company Selection")
    cik = st.sidebar.text_input("Enter Company CIK:", 
                               value=st.session_state.get('selected_cik', "0000320193"))
    
    # Page routing
    if st.session_state['page'] == 'fortune500':
        show_fortune500()
    elif cik:
        run_analysis(cik)

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
