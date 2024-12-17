from typing import Dict, List
import pandas as pd
import numpy as np

class FinancialAnalyzer:
    def __init__(self):
        self.key_metrics = [
            'pe_ratio',
            'debt_equity_ratio',
            'current_ratio',
            'quick_ratio',
            'roe',
            'roa'
        ]

    def calculate_financial_ratios(self, financial_data: Dict) -> Dict[str, float]:
        """Calculate key financial ratios from financial statements"""
        ratios = {}
        
        try:
            # P/E Ratio
            if financial_data.get('net_income') and financial_data.get('shares_outstanding'):
                eps = financial_data['net_income'] / financial_data['shares_outstanding']
                if financial_data.get('stock_price'):
                    ratios['pe_ratio'] = financial_data['stock_price'] / eps

            # Debt to Equity Ratio
            if financial_data.get('total_debt') and financial_data.get('total_equity'):
                ratios['debt_equity_ratio'] = financial_data['total_debt'] / financial_data['total_equity']

            # Current Ratio
            if financial_data.get('current_assets') and financial_data.get('current_liabilities'):
                ratios['current_ratio'] = financial_data['current_assets'] / financial_data['current_liabilities']

            # Quick Ratio
            if financial_data.get('current_assets') and financial_data.get('inventory') and financial_data.get('current_liabilities'):
                quick_assets = financial_data['current_assets'] - financial_data['inventory']
                ratios['quick_ratio'] = quick_assets / financial_data['current_liabilities']

            # Return on Equity (ROE)
            if financial_data.get('net_income') and financial_data.get('total_equity'):
                ratios['roe'] = financial_data['net_income'] / financial_data['total_equity']

            # Return on Assets (ROA)
            if financial_data.get('net_income') and financial_data.get('total_assets'):
                ratios['roa'] = financial_data['net_income'] / financial_data['total_assets']

        except Exception as e:
            print(f"Error calculating ratios: {str(e)}")

        return ratios

    def analyze_insider_trading(self, insider_trades: List[Dict]) -> Dict:
        """Analyze patterns in insider trading activity"""
        df = pd.DataFrame(insider_trades)
        
        analysis = {
            'total_transactions': len(df),
            'buy_count': len(df[df['transaction_type'] == 'BUY']),
            'sell_count': len(df[df['transaction_type'] == 'SELL']),
            'net_volume': df[df['transaction_type'] == 'BUY']['shares'].sum() - 
                         df[df['transaction_type'] == 'SELL']['shares'].sum(),
            'average_transaction_size': df['shares'].mean()
        }
        
        return analysis

    def analyze_institutional_holdings(self, institutional_data: List[Dict]) -> Dict:
        """Analyze institutional ownership patterns"""
        df = pd.DataFrame(institutional_data)
        
        analysis = {
            'total_institutions': len(df),
            'total_shares_held': df['shares_held'].sum(),
            'percentage_outstanding': (df['shares_held'].sum() / df['total_shares'].iloc[0]) * 100,
            'top_holders': df.nlargest(5, 'shares_held')[['institution_name', 'shares_held']].to_dict('records')
        }
        
        return analysis

    def calculate_risk_metrics(self, price_history: List[float]) -> Dict:
        """Calculate risk metrics based on price history"""
        prices = np.array(price_history)
        returns = np.diff(prices) / prices[:-1]
        
        risk_metrics = {
            'volatility': np.std(returns) * np.sqrt(252),  # Annualized volatility
            'max_drawdown': np.min(prices) / np.max(prices) - 1,
            'sharpe_ratio': np.mean(returns) / np.std(returns) * np.sqrt(252),
            'beta': None  # Would need market returns to calculate beta
        }
        
        return risk_metrics
