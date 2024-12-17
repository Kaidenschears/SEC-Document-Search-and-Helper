from typing import Dict, List
import openai
import os

class LLMAnalyzer:
    def __init__(self):
        self.context_template = """
        You are a financial analyst expert specialized in SEC filings analysis.
        Analyze the following information and provide insights:
        
        Context:
        {context}
        
        Question: {question}
        """

    def analyze_filing(self, filing_content: str, filing_type: str) -> Dict:
        """Analyze filing content using LLM"""
        prompt = self.context_template.format(
            context=f"Filing Type: {filing_type}\n\nContent: {filing_content[:4000]}",  # Truncate for token limit
            question="What are the key insights and potential risks from this filing?"
        )
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a financial analyst expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return {
                'analysis': response.choices[0].message.content,
                'confidence': 0.8,  # Placeholder for actual confidence scoring
                'key_points': self._extract_key_points(response.choices[0].message.content)
            }
        except Exception as e:
            return {
                'analysis': f"Error analyzing filing: {str(e)}",
                'confidence': 0,
                'key_points': []
            }

    def generate_trading_recommendation(self, 
                                     financial_metrics: Dict,
                                     recent_filings: List[Dict],
                                     market_context: str) -> Dict:
        """Generate trading recommendation based on available data"""
        context = f"""
        Financial Metrics:
        {financial_metrics}
        
        Recent Filings Summary:
        {recent_filings}
        
        Market Context:
        {market_context}
        """
        
        prompt = self.context_template.format(
            context=context,
            question="What is your trading recommendation based on this information?"
        )
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a financial advisor expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            return {
                'recommendation': response.choices[0].message.content,
                'confidence_score': 0.7,  # Placeholder for actual confidence scoring
                'reasoning': self._extract_reasoning(response.choices[0].message.content)
            }
        except Exception as e:
            return {
                'recommendation': f"Error generating recommendation: {str(e)}",
                'confidence_score': 0,
                'reasoning': []
            }

    def _extract_key_points(self, analysis: str) -> List[str]:
        """Extract key points from analysis text"""
        prompt = f"""
        Extract the key points from this analysis as a list:
        {analysis}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Extract key points in a concise list format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            key_points = response.choices[0].message.content.split('\n')
            return [point.strip('- ') for point in key_points if point.strip()]
        except:
            return []

    def _extract_reasoning(self, recommendation: str) -> List[str]:
        """Extract reasoning points from recommendation"""
        prompt = f"""
        Extract the main reasoning points behind this recommendation:
        {recommendation}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Extract reasoning points in a clear list format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            reasoning = response.choices[0].message.content.split('\n')
            return [point.strip('- ') for point in reasoning if point.strip()]
        except:
            return []
