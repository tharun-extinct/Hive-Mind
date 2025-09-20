import requests
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json
from collections import Counter, defaultdict
from dotenv import load_dotenv
load_dotenv()

class NewsSentimentAnalyzer:
    """A class to fetch, analyze, and visualize news sentiment data from Alpha Vantage"""
    
    def __init__(self, api_key=None):
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required. Set ALPHA_VANTAGE_API_KEY in .env file")
        
        # Set style for better looking plots
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def fetch_news_sentiment(self, tickers, limit=1000):
        """
        Fetch news sentiment data for given tickers
        
        Args:
            tickers (str or list): Ticker symbols (e.g., 'AAPL' or ['AAPL', 'GOOGL'])
            limit (int): Maximum number of articles to retrieve
            
        Returns:
            dict: Raw API response data
        """
        if isinstance(tickers, list):
            tickers = ','.join(tickers)
            
        url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={tickers}&limit={limit}&apikey={self.api_key}'
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if 'Error Message' in data:
                raise Exception(f"API Error: {data['Error Message']}")
            if 'Note' in data:
                raise Exception(f"API Limit: {data['Note']}")
                
            return data
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def process_sentiment_data(self, raw_data):
        """
        Process raw sentiment data into organized pandas DataFrames
        
        Args:
            raw_data (dict): Raw API response
            
        Returns:
            tuple: (articles_df, ticker_sentiment_df, topics_df)
        """
        if 'feed' not in raw_data:
            raise ValueError("No feed data found in API response")
        
        articles = []
        ticker_sentiments = []
        topics = []
        
        print(f"Processing {len(raw_data['feed'])} articles...")
        
        for article in raw_data['feed']:
            # Process article-level data
            article_data = {
                'title': article.get('title', ''),
                'url': article.get('url', ''),
                'time_published': self._parse_datetime(article.get('time_published', '')),
                'source': article.get('source', ''),
                'summary': article.get('summary', ''),
                'overall_sentiment_score': float(article.get('overall_sentiment_score', 0)),
                'overall_sentiment_label': article.get('overall_sentiment_label', ''),
                'category': article.get('category_within_source', 'n/a')
            }
            articles.append(article_data)
            
            # Process ticker sentiment data
            for ticker_info in article.get('ticker_sentiment', []):
                ticker_data = {
                    'article_title': article.get('title', ''),
                    'time_published': article_data['time_published'],
                    'ticker': ticker_info.get('ticker', ''),
                    'relevance_score': float(ticker_info.get('relevance_score', 0)),
                    'ticker_sentiment_score': float(ticker_info.get('ticker_sentiment_score', 0)),
                    'ticker_sentiment_label': ticker_info.get('ticker_sentiment_label', '')
                }
                ticker_sentiments.append(ticker_data)
            
            # Process topics data
            for topic_info in article.get('topics', []):
                topic_data = {
                    'article_title': article.get('title', ''),
                    'time_published': article_data['time_published'],
                    'topic': topic_info.get('topic', ''),
                    'relevance_score': float(topic_info.get('relevance_score', 0))
                }
                topics.append(topic_data)
        
        articles_df = pd.DataFrame(articles)
        ticker_sentiments_df = pd.DataFrame(ticker_sentiments)
        topics_df = pd.DataFrame(topics)
        
        # Debug info
        print(f"Articles DataFrame shape: {articles_df.shape}")
        print(f"Articles columns: {list(articles_df.columns)}")
        print(f"Ticker sentiments DataFrame shape: {ticker_sentiments_df.shape}")
        print(f"Topics DataFrame shape: {topics_df.shape}")
        
        if not articles_df.empty:
            print(f"Sample sentiment labels: {articles_df['overall_sentiment_label'].value_counts()}")
        
        return (articles_df, ticker_sentiments_df, topics_df)
    
    def _parse_datetime(self, time_str):
        """Parse Alpha Vantage datetime format"""
        try:
            return datetime.strptime(time_str, '%Y%m%dT%H%M%S')
        except:
            return None
    
    def create_sentiment_overview(self, articles_df, ticker_sentiments_df):
        """Create overview visualizations of sentiment data"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('News Sentiment Analysis Overview', fontsize=16, fontweight='bold')
        
        # Overall sentiment distribution
        if 'overall_sentiment_label' in articles_df.columns and not articles_df['overall_sentiment_label'].empty:
            sentiment_counts = articles_df['overall_sentiment_label'].value_counts()
            axes[0, 0].pie(sentiment_counts.values, labels=sentiment_counts.index, autopct='%1.1f%%', startangle=90)
            axes[0, 0].set_title('Overall Sentiment Distribution')
        else:
            axes[0, 0].text(0.5, 0.5, 'No sentiment\nlabel data\navailable', 
                           ha='center', va='center', transform=axes[0, 0].transAxes)
            axes[0, 0].set_title('Overall Sentiment Distribution - No Data')
        
        # Sentiment score histogram
        axes[0, 1].hist(articles_df['overall_sentiment_score'], bins=20, alpha=0.7, edgecolor='black')
        axes[0, 1].set_xlabel('Sentiment Score')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].set_title('Sentiment Score Distribution')
        axes[0, 1].axvline(0, color='red', linestyle='--', label='Neutral')
        axes[0, 1].legend()
        
        # Articles by source (top 10)
        source_counts = articles_df['source'].value_counts().head(10)
        axes[1, 0].barh(range(len(source_counts)), source_counts.values)
        axes[1, 0].set_yticks(range(len(source_counts)))
        axes[1, 0].set_yticklabels(source_counts.index)
        axes[1, 0].set_xlabel('Number of Articles')
        axes[1, 0].set_title('Top 10 News Sources')
        
        # Ticker sentiment comparison
        if not ticker_sentiments_df.empty:
            ticker_avg = ticker_sentiments_df.groupby('ticker')['ticker_sentiment_score'].mean().sort_values(ascending=True)
            axes[1, 1].barh(range(len(ticker_avg)), ticker_avg.values)
            axes[1, 1].set_yticks(range(len(ticker_avg)))
            axes[1, 1].set_yticklabels(ticker_avg.index)
            axes[1, 1].set_xlabel('Average Sentiment Score')
            axes[1, 1].set_title('Average Ticker Sentiment')
            axes[1, 1].axvline(0, color='red', linestyle='--', label='Neutral')
            axes[1, 1].legend()
        
        plt.tight_layout()
        return fig
    
    def create_time_series_analysis(self, articles_df, ticker_sentiments_df):
        """Create time-series analysis of sentiment"""
        if articles_df['time_published'].isna().all():
            print("No valid timestamps found for time series analysis")
            return None
        
        fig, axes = plt.subplots(2, 1, figsize=(15, 10))
        fig.suptitle('Sentiment Time Series Analysis', fontsize=16, fontweight='bold')
        
        # Overall sentiment over time
        articles_clean = articles_df.dropna(subset=['time_published'])
        articles_clean = articles_clean.sort_values('time_published')
        
        if len(articles_clean) > 0:
            axes[0].plot(articles_clean['time_published'], articles_clean['overall_sentiment_score'], 
                        marker='o', alpha=0.6, linewidth=1)
            axes[0].set_ylabel('Overall Sentiment Score')
            axes[0].set_title('Overall Sentiment Over Time')
            axes[0].axhline(0, color='red', linestyle='--', alpha=0.7, label='Neutral')
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)
        
        # Ticker sentiment over time (if multiple tickers)
        if not ticker_sentiments_df.empty:
            ticker_clean = ticker_sentiments_df.dropna(subset=['time_published'])
            for ticker in ticker_clean['ticker'].unique():
                ticker_data = ticker_clean[ticker_clean['ticker'] == ticker].sort_values('time_published')
                if len(ticker_data) > 1:
                    axes[1].plot(ticker_data['time_published'], ticker_data['ticker_sentiment_score'], 
                               marker='o', alpha=0.7, label=ticker, linewidth=2)
            
            axes[1].set_xlabel('Time')
            axes[1].set_ylabel('Ticker Sentiment Score')
            axes[1].set_title('Ticker Sentiment Over Time')
            axes[1].axhline(0, color='red', linestyle='--', alpha=0.7, label='Neutral')
            axes[1].legend()
            axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.xticks(rotation=45)
        return fig
    
    def create_topic_analysis(self, topics_df):
        """Analyze and visualize topic distributions"""
        if topics_df.empty:
            print("No topic data available for analysis")
            return None
        
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Topic Analysis', fontsize=16, fontweight='bold')
        
        # Topic frequency
        topic_counts = topics_df['topic'].value_counts().head(10)
        axes[0].barh(range(len(topic_counts)), topic_counts.values)
        axes[0].set_yticks(range(len(topic_counts)))
        axes[0].set_yticklabels(topic_counts.index)
        axes[0].set_xlabel('Number of Mentions')
        axes[0].set_title('Top 10 Topics by Frequency')
        
        # Average relevance by topic
        topic_relevance = topics_df.groupby('topic')['relevance_score'].mean().sort_values(ascending=False).head(10)
        axes[1].barh(range(len(topic_relevance)), topic_relevance.values)
        axes[1].set_yticks(range(len(topic_relevance)))
        axes[1].set_yticklabels(topic_relevance.index)
        axes[1].set_xlabel('Average Relevance Score')
        axes[1].set_title('Top 10 Topics by Relevance')
        
        plt.tight_layout()
        return fig
    
    def create_detailed_ticker_analysis(self, ticker_sentiments_df, ticker='AAPL'):
        """Create detailed analysis for a specific ticker"""
        if ticker_sentiments_df.empty:
            print("No ticker sentiment data available")
            return None
        
        ticker_data = ticker_sentiments_df[ticker_sentiments_df['ticker'] == ticker]
        if ticker_data.empty:
            print(f"No data found for ticker: {ticker}")
            return None
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'Detailed Analysis for {ticker}', fontsize=16, fontweight='bold')
        
        # Sentiment distribution
        sentiment_counts = ticker_data['ticker_sentiment_label'].value_counts()
        axes[0, 0].pie(sentiment_counts.values, labels=sentiment_counts.index, autopct='%1.1f%%', startangle=90)
        axes[0, 0].set_title('Sentiment Label Distribution')
        
        # Sentiment vs Relevance scatter
        axes[0, 1].scatter(ticker_data['relevance_score'], ticker_data['ticker_sentiment_score'], alpha=0.6)
        axes[0, 1].set_xlabel('Relevance Score')
        axes[0, 1].set_ylabel('Sentiment Score')
        axes[0, 1].set_title('Sentiment vs Relevance')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Sentiment score distribution
        axes[1, 0].hist(ticker_data['ticker_sentiment_score'], bins=20, alpha=0.7, edgecolor='black')
        axes[1, 0].set_xlabel('Sentiment Score')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].set_title('Sentiment Score Distribution')
        axes[1, 0].axvline(0, color='red', linestyle='--', label='Neutral')
        axes[1, 0].legend()
        
        # Relevance score distribution
        axes[1, 1].hist(ticker_data['relevance_score'], bins=20, alpha=0.7, edgecolor='black')
        axes[1, 1].set_xlabel('Relevance Score')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].set_title('Relevance Score Distribution')
        
        plt.tight_layout()
        return fig
    
    def save_data(self, articles_df, ticker_sentiments_df, topics_df, prefix='sentiment_analysis'):
        """Save processed data to CSV files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save to data directory
        data_dir = 'data'
        os.makedirs(data_dir, exist_ok=True)
        
        files_saved = []
        
        if not articles_df.empty:
            articles_file = f'{data_dir}/{prefix}_articles_{timestamp}.csv'
            articles_df.to_csv(articles_file, index=False)
            files_saved.append(articles_file)
        
        if not ticker_sentiments_df.empty:
            ticker_file = f'{data_dir}/{prefix}_ticker_sentiment_{timestamp}.csv'
            ticker_sentiments_df.to_csv(ticker_file, index=False)
            files_saved.append(ticker_file)
        
        if not topics_df.empty:
            topics_file = f'{data_dir}/{prefix}_topics_{timestamp}.csv'
            topics_df.to_csv(topics_file, index=False)
            files_saved.append(topics_file)
        
        return files_saved
    
    def generate_summary_report(self, articles_df, ticker_sentiments_df, topics_df):
        """Generate a comprehensive summary report"""
        report = []
        report.append("=== NEWS SENTIMENT ANALYSIS SUMMARY ===\n")
        
        # Articles summary
        report.append(f"📰 ARTICLES OVERVIEW:")
        report.append(f"  • Total articles: {len(articles_df)}")
        if not articles_df.empty:
            report.append(f"  • Average sentiment score: {articles_df['overall_sentiment_score'].mean():.3f}")
            if 'overall_sentiment_label' in articles_df.columns and not articles_df['overall_sentiment_label'].empty:
                most_common = articles_df['overall_sentiment_label'].mode()
                if len(most_common) > 0:
                    report.append(f"  • Most common sentiment: {most_common[0]}")
            report.append(f"  • Unique sources: {articles_df['source'].nunique()}")
        
        # Ticker sentiment summary
        report.append(f"\n📈 TICKER SENTIMENT:")
        if not ticker_sentiments_df.empty:
            report.append(f"  • Total ticker mentions: {len(ticker_sentiments_df)}")
            report.append(f"  • Unique tickers: {ticker_sentiments_df['ticker'].nunique()}")
            
            # Best and worst performing tickers
            ticker_avg = ticker_sentiments_df.groupby('ticker')['ticker_sentiment_score'].mean()
            if len(ticker_avg) > 0:
                best_ticker = ticker_avg.idxmax()
                worst_ticker = ticker_avg.idxmin()
                report.append(f"  • Most positive: {best_ticker} ({ticker_avg[best_ticker]:.3f})")
                report.append(f"  • Most negative: {worst_ticker} ({ticker_avg[worst_ticker]:.3f})")
        
        # Topics summary
        report.append(f"\n🏷️ TOPICS ANALYSIS:")
        if not topics_df.empty:
            report.append(f"  • Total topic mentions: {len(topics_df)}")
            report.append(f"  • Unique topics: {topics_df['topic'].nunique()}")
            most_common_topic = topics_df['topic'].mode()
            if len(most_common_topic) > 0:
                report.append(f"  • Most discussed topic: {most_common_topic[0]}")
        
        # Time range
        if not articles_df.empty and not articles_df['time_published'].isna().all():
            time_range = articles_df.dropna(subset=['time_published'])
            if len(time_range) > 0:
                earliest = time_range['time_published'].min()
                latest = time_range['time_published'].max()
                report.append(f"\n⏰ TIME RANGE:")
                report.append(f"  • From: {earliest}")
                report.append(f"  • To: {latest}")
        
        return '\n'.join(report)

# Example usage and demonstration
if __name__ == "__main__":
    try:
        # Initialize analyzer
        analyzer = NewsSentimentAnalyzer()
        
        # Fetch data for multiple tickers
        print("Fetching news sentiment data...")
        raw_data = analyzer.fetch_news_sentiment(['AAPL', 'NVDA', 'GOOGL'], limit=100)
        
        # Process the data
        print("Processing data...")
        articles_df, ticker_sentiments_df, topics_df = analyzer.process_sentiment_data(raw_data)
        
        # Generate summary report
        print("\n" + analyzer.generate_summary_report(articles_df, ticker_sentiments_df, topics_df))
        
        # Create visualizations
        print("\nGenerating visualizations...")
        
        # Overview charts
        fig1 = analyzer.create_sentiment_overview(articles_df, ticker_sentiments_df)
        plt.show()
        
        # Time series analysis
        fig2 = analyzer.create_time_series_analysis(articles_df, ticker_sentiments_df)
        if fig2:
            plt.show()
        
        # Topic analysis
        fig3 = analyzer.create_topic_analysis(topics_df)
        if fig3:
            plt.show()
        
        # Detailed ticker analysis for AAPL
        fig4 = analyzer.create_detailed_ticker_analysis(ticker_sentiments_df, 'AAPL')
        if fig4:
            plt.show()
        
        # Save data
        saved_files = analyzer.save_data(articles_df, ticker_sentiments_df, topics_df)
        print(f"\nData saved to: {', '.join(saved_files)}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Make sure your ALPHA_VANTAGE_API_KEY is set in the .env file")