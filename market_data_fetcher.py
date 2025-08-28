"""
Market Data Fetcher for NSE & BSE
Handles both historical and real-time tick data
"""

import asyncio
import aiohttp
import pandas as pd
import yfinance as yf
import requests
import requests_cache  # For caching HTTP requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, AsyncGenerator, Union
import logging
import json
import random
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TickData:
    """Data class for tick information"""
    symbol: str
    exchange: str
    timestamp: datetime
    ltp: float  # Last Traded Price
    volume: int
    open_price: float
    high: float
    low: float
    close: float
    change: float
    change_percent: float

class MarketDataFetcher:
    """Main class for fetching market data from NSE & BSE"""
    
    def __init__(self):
        # Create cache directory if it doesn't exist
        os.makedirs('.cache', exist_ok=True)
        
        # Install the requests cache
        # This will cache all HTTP requests to reduce rate limiting issues
        requests_cache.install_cache(
            '.cache/market_data_cache',
            backend='sqlite',
            expire_after=3600  # Cache for 1 hour
        )
        
        self.session = None
        self.nse_base_url = "https://www.nseindia.com"
        self.bse_base_url = "https://api.bseindia.com"
        
        # Headers to mimic browser requests - more browser-like to avoid detection
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://finance.yahoo.com/',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Chromium";v="105", "Not)A;Brand";v="8"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session
    
    async def get_historical_data(
        self, 
        symbol: str, 
        exchange: str = 'NSE',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = '1D'
    ) -> List[Dict]:
        """
        Get historical data for a symbol
        
        Args:
            symbol: Stock symbol
            exchange: 'NSE' or 'BSE'
            start_date: Start date for data
            end_date: End date for data
            interval: Data interval ('1D', '1H', '5m', etc.)
        
        Returns:
            List of historical data records
        """
        try:
            if exchange.upper() == 'NSE':
                return await self._get_nse_historical_data(symbol, start_date, end_date, interval)
            elif exchange.upper() == 'BSE':
                return await self._get_bse_historical_data(symbol, start_date, end_date, interval)
            else:
                raise ValueError(f"Unsupported exchange: {exchange}")
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return []
    
    async def _get_nse_historical_data(self, symbol: str, start_date: Optional[datetime], end_date: Optional[datetime], interval: str) -> List[Dict]:
        """Get NSE historical data using yfinance as fallback"""
        try:
            # Use yfinance for reliable historical data
            ticker_symbol = f"{symbol}.NS"  # NSE suffix
            
            # Convert interval to yfinance format
            yf_interval = self._convert_interval_to_yf(interval)
            
            # Set default dates if none provided
            start = start_date.strftime('%Y-%m-%d') if start_date else None
            end = end_date.strftime('%Y-%m-%d') if end_date else None
            
            # Fetch data with session for better reliability
            session = requests.Session()
            ticker = yf.Ticker(ticker_symbol, session=session)
            hist_data = ticker.history(
                start=start,
                end=end,
                interval=yf_interval
            )
            
            # Convert to our format
            records = []
            for date, row in hist_data.iterrows():
                records.append({
                    'symbol': symbol,
                    'exchange': 'NSE',
                    'timestamp': date,
                    'open': round(row['Open'], 2),
                    'high': round(row['High'], 2),
                    'low': round(row['Low'], 2),
                    'close': round(row['Close'], 2),
                    'volume': int(row['Volume']),
                    'ltp': round(row['Close'], 2)
                })
            
            return records
            
        except Exception as e:
            logger.error(f"Error fetching NSE data for {symbol}: {e}")
            return []
    
    async def _get_bse_historical_data(self, symbol: str, start_date: Optional[datetime], end_date: Optional[datetime], interval: str) -> List[Dict]:
        """Get BSE historical data using yfinance"""
        try:
            # Use yfinance for BSE data
            ticker_symbol = f"{symbol}.BO"  # BSE suffix
            
            yf_interval = self._convert_interval_to_yf(interval)
            
            # Set default dates if none provided
            start = start_date.strftime('%Y-%m-%d') if start_date else None
            end = end_date.strftime('%Y-%m-%d') if end_date else None
            
            # Fetch data with session for better reliability
            session = requests.Session()
            ticker = yf.Ticker(ticker_symbol, session=session)
            hist_data = ticker.history(
                start=start,
                end=end,
                interval=yf_interval
            )
            
            records = []
            for date, row in hist_data.iterrows():
                records.append({
                    'symbol': symbol,
                    'exchange': 'BSE',
                    'timestamp': date,
                    'open': round(row['Open'], 2),
                    'high': round(row['High'], 2),
                    'low': round(row['Low'], 2),
                    'close': round(row['Close'], 2),
                    'volume': int(row['Volume']),
                    'ltp': round(row['Close'], 2)
                })
            
            return records
            
        except Exception as e:
            logger.error(f"Error fetching BSE data for {symbol}: {e}")
            return []
    
    def _convert_interval_to_yf(self, interval: str) -> str:
        """Convert our interval format to yfinance format"""
        interval_map = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1H': '1h',
            '1D': '1d',
            '1W': '1wk',
            '1M': '1mo'
        }
        return interval_map.get(interval, '1d')
    
    async def get_realtime_data(self, symbols: List[str], exchange: str = 'NSE') -> AsyncGenerator[Dict, None]:
        """
        Get real-time tick data for symbols
        
        Args:
            symbols: List of stock symbols
            exchange: 'NSE' or 'BSE'
        
        Yields:
            Real-time tick data
        """
        try:
            if exchange.upper() == 'NSE':
                async for tick in self._get_nse_realtime_data(symbols):
                    yield tick
            elif exchange.upper() == 'BSE':
                async for tick in self._get_bse_realtime_data(symbols):
                    yield tick
            else:
                raise ValueError(f"Unsupported exchange: {exchange}")
                
        except Exception as e:
            logger.error(f"Error in real-time data stream: {e}")
    
    async def _get_nse_realtime_data(self, symbols: List[str]) -> AsyncGenerator[Dict, None]:
        """Simulate NSE real-time data (replace with actual API when available)"""
        # Use a cache to store recent data and prevent frequent API calls
        cache = {}
        cache_expiry = {}
        cache_duration = 60  # Cache duration in seconds
        
        # Initial delay between requests (will be increased if rate-limited)
        base_delay = 5  # Start with 5 seconds between requests
        max_delay = 30  # Maximum delay in seconds
        current_delay = base_delay
        
        while True:
            for symbol in symbols:
                try:
                    current_time = datetime.now()
                    
                    # Use cached data if available and not expired
                    if (symbol in cache and symbol in cache_expiry and 
                        current_time < cache_expiry[symbol]):
                        # Use cached data
                        base_price = cache[symbol]
                        logger.info(f"Using cached data for {symbol}")
                    else:
                        # Get latest price using yfinance with session for better reliability
                        session = requests.Session()
                        ticker = yf.Ticker(f"{symbol}.NS", session=session)
                        info = ticker.info
                        
                        # Store in cache
                        base_price = info.get('regularMarketPrice', 100.0)
                        cache[symbol] = base_price
                        cache_expiry[symbol] = current_time + timedelta(seconds=cache_duration)
                        
                        # Reset delay if successful
                        current_delay = base_delay
                        logger.info(f"Successfully fetched new data for {symbol}")
                    
                    # Simulate real-time tick
                    tick_data = {
                        'symbol': symbol,
                        'exchange': 'NSE',
                        'timestamp': current_time.strftime('%H:%M:%S'),
                        'ltp': round(base_price + random.uniform(-2, 2), 2),
                        'volume': random.randint(1000, 50000),
                        'change': round(random.uniform(-5, 5), 2),
                        'change_percent': round(random.uniform(-2, 2), 2)
                    }
                    
                    yield tick_data
                    await asyncio.sleep(current_delay)  # Use dynamic delay between ticks
                    
                except Exception as e:
                    if "Too Many Requests" in str(e):
                        # Implement exponential backoff for rate limiting
                        current_delay = min(current_delay * 2, max_delay)
                        logger.warning(f"Rate limited for {symbol}. Increasing delay to {current_delay}s")
                    else:
                        logger.error(f"Error getting real-time data for {symbol}: {e}")
                    
                    await asyncio.sleep(current_delay)
    
    async def _get_bse_realtime_data(self, symbols: List[str]) -> AsyncGenerator[Dict, None]:
        """Simulate BSE real-time data"""
        # Use a cache to store recent data and prevent frequent API calls
        cache = {}
        cache_expiry = {}
        cache_duration = 60  # Cache duration in seconds
        
        # Initial delay between requests (will be increased if rate-limited)
        base_delay = 5  # Start with 5 seconds between requests
        max_delay = 30  # Maximum delay in seconds
        current_delay = base_delay
        
        while True:
            for symbol in symbols:
                try:
                    current_time = datetime.now()
                    
                    # Use cached data if available and not expired
                    if (symbol in cache and symbol in cache_expiry and 
                        current_time < cache_expiry[symbol]):
                        # Use cached data
                        base_price = cache[symbol]
                        logger.info(f"Using cached data for BSE {symbol}")
                    else:
                        # Get latest price using yfinance with session for better reliability
                        session = requests.Session()
                        ticker = yf.Ticker(f"{symbol}.BO", session=session)
                        info = ticker.info
                        
                        # Store in cache
                        base_price = info.get('regularMarketPrice', 100.0)
                        cache[symbol] = base_price
                        cache_expiry[symbol] = current_time + timedelta(seconds=cache_duration)
                        
                        # Reset delay if successful
                        current_delay = base_delay
                        logger.info(f"Successfully fetched new data for BSE {symbol}")
                    
                    # Simulate real-time tick
                    tick_data = {
                        'symbol': symbol,
                        'exchange': 'BSE',
                        'timestamp': current_time.strftime('%H:%M:%S'),
                        'ltp': round(base_price + random.uniform(-2, 2), 2),
                        'volume': random.randint(1000, 50000),
                        'change': round(random.uniform(-5, 5), 2),
                        'change_percent': round(random.uniform(-2, 2), 2)
                    }
                    
                    yield tick_data
                    await asyncio.sleep(current_delay)  # Use dynamic delay between ticks
                    
                except Exception as e:
                    if "Too Many Requests" in str(e):
                        # Implement exponential backoff for rate limiting
                        current_delay = min(current_delay * 2, max_delay)
                        logger.warning(f"Rate limited for BSE {symbol}. Increasing delay to {current_delay}s")
                    else:
                        logger.error(f"Error getting BSE real-time data for {symbol}: {e}")
                    
                    await asyncio.sleep(current_delay)
    
    async def get_market_status(self, exchange: str = 'NSE') -> str:
        """
        Get current market status
        
        Args:
            exchange: 'NSE' or 'BSE'
        
        Returns:
            Market status string
        """
        try:
            current_time = datetime.now().time()
            
            # Market hours: 9:15 AM to 3:30 PM IST (Monday to Friday)
            market_open = datetime.strptime("09:15", "%H:%M").time()
            market_close = datetime.strptime("15:30", "%H:%M").time()
            
            is_weekday = datetime.now().weekday() < 5  # Monday = 0, Sunday = 6
            
            if is_weekday and market_open <= current_time <= market_close:
                return f"{exchange} Market is OPEN"
            else:
                return f"{exchange} Market is CLOSED"
                
        except Exception as e:
            logger.error(f"Error checking market status: {e}")
            return f"{exchange} Market status UNKNOWN"
    
    async def get_symbol_info(self, symbol: str, exchange: str = 'NSE') -> Dict:
        """Get detailed information about a symbol"""
        try:
            # Use a static cache for symbol info with 24-hour expiry
            cache_key = f"{symbol}_{exchange}"
            
            # Check if we have a file-based cache for this symbol
            cache_file = f".cache_{cache_key}.json"
            
            try:
                # Try to read from cache
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                # Check if cache is still valid (less than 24 hours old)
                cache_time = datetime.fromisoformat(cached_data.get('timestamp', '2020-01-01'))
                if datetime.now() - cache_time < timedelta(hours=24):
                    logger.info(f"Using cached info for {symbol} on {exchange}")
                    return cached_data.get('data', {})
            except (FileNotFoundError, json.JSONDecodeError):
                # Cache doesn't exist or is invalid
                pass
                
            # If not in cache or cache expired, fetch new data
            suffix = '.NS' if exchange.upper() == 'NSE' else '.BO'
            
            # Use session for better handling of rate limits
            session = requests.Session()
            ticker = yf.Ticker(f"{symbol}{suffix}", session=session)
            
            # Implement retry with exponential backoff
            max_retries = 3
            retry_delay = 5
            
            for retry in range(max_retries):
                try:
                    info = ticker.info
                    
                    # Create result
                    result = {
                        'symbol': symbol,
                        'exchange': exchange,
                        'company_name': info.get('longName', 'N/A'),
                        'sector': info.get('sector', 'N/A'),
                        'market_cap': info.get('marketCap', 'N/A'),
                        'pe_ratio': info.get('trailingPE', 'N/A'),
                        '52_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
                        '52_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
                        'current_price': info.get('regularMarketPrice', 'N/A')
                    }
                    
                    # Cache the result
                    with open(cache_file, 'w') as f:
                        json.dump({
                            'timestamp': datetime.now().isoformat(),
                            'data': result
                        }, f)
                        
                    return result
                    
                except Exception as e:
                    if "Too Many Requests" in str(e):
                        if retry < max_retries - 1:
                            wait_time = retry_delay * (2 ** retry)
                            logger.warning(f"Rate limited for {symbol}, retrying in {wait_time}s")
                            await asyncio.sleep(wait_time)
                        else:
                            raise
                    else:
                        raise
            
            # Fallback return in case all retries fail
            return {}
            
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
            return {}
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if self.session and not self.session.closed:
            asyncio.create_task(self.session.close())