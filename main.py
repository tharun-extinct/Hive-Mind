"""
NSE & BSE Tick Data Fetcher
Supports both historical and real-time data fetching
"""

import asyncio
import logging
from datetime import datetime, timedelta
from market_data_fetcher import MarketDataFetcher

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Main function to demonstrate tick data fetching"""
    
    # Initialize the market data fetcher
    fetcher = MarketDataFetcher()
    
    # Example symbols
    nse_symbols = ['RELIANCE']               #, 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']
    bse_symbols = ['500325', '532540', '500209', '500180', '532174']  # BSE codes
    
    print("=== NSE & BSE Tick Data Fetcher ===\n")
    
    # Menu for user selection
    while True:
        print("\nSelect an option:")
        print("1. Get Historical Data (NSE)")
        print("2. Get Historical Data (BSE)")
        print("3. Start Real-time Data Stream (NSE)")
        print("4. Start Real-time Data Stream (BSE)")
        print("5. Get Current Market Status")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            await handle_historical_nse(fetcher, nse_symbols)
        elif choice == '2':
            await handle_historical_bse(fetcher, bse_symbols)
        elif choice == '3':
            await handle_realtime_nse(fetcher, nse_symbols)
        elif choice == '4':
            await handle_realtime_bse(fetcher, bse_symbols)
        elif choice == '5':
            await handle_market_status(fetcher)
        elif choice == '6':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")



async def handle_historical_nse(fetcher, symbols):
    """Handle historical NSE data fetching"""
    print(f"\nFetching historical data for NSE symbols: {symbols}")
    
    # Get data for last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    for symbol in symbols[:2]:  # Limit to first 2 symbols for demo
        try:
            data = await fetcher.get_historical_data(
                symbol=symbol,
                exchange='NSE',
                start_date=start_date,
                end_date=end_date,
                interval='1D'
            )
            
            if data:
                print(f"\n{symbol} - Last 5 records:")
                for record in data[-5:]:
                    print(f"  {record}")
            else:
                print(f"No data found for {symbol}")
                
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")


# BSE
async def handle_historical_bse(fetcher, symbols):
    """Handle historical BSE data fetching"""
    print(f"\nFetching historical data for BSE symbols: {symbols}")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    for symbol in symbols[:2]:  # Limit to first 2 symbols for demo
        try:
            data = await fetcher.get_historical_data(
                symbol=symbol,
                exchange='BSE',
                start_date=start_date,
                end_date=end_date,
                interval='1D'
            )
            
            if data:
                print(f"\nBSE {symbol} - Last 5 records:")
                for record in data[-5:]:
                    print(f"  {record}")
            else:
                print(f"No data found for BSE {symbol}")
                
        except Exception as e:
            logger.error(f"Error fetching BSE data for {symbol}: {e}")



async def handle_realtime_nse(fetcher, symbols):
    """Handle real-time NSE data streaming"""
    print(f"\nStarting real-time data stream for NSE symbols: {symbols[:3]}")
    print("Press Ctrl+C to stop the stream\n")
    
    try:
        async for tick_data in fetcher.get_realtime_data(symbols[:3], 'NSE'):
            print(f"[{tick_data['timestamp']}] {tick_data['symbol']}: "
                  f"LTP={tick_data['ltp']}, Volume={tick_data['volume']}")
    except Exception as e:
        logger.error(f"Error in real-time stream: {e}")



async def handle_realtime_bse(fetcher, symbols):
    """Handle real-time BSE data streaming"""
    print(f"\nStarting real-time data stream for BSE symbols: {symbols[:3]}")
    print("Press Ctrl+C to stop the stream\n")
    
    try:
        async for tick_data in fetcher.get_realtime_data(symbols[:3], 'BSE'):
            print(f"[{tick_data['timestamp']}] BSE {tick_data['symbol']}: "
                  f"LTP={tick_data['ltp']}, Volume={tick_data['volume']}")
            
    except KeyboardInterrupt:
        print("\nReal-time stream stopped by user")
    except Exception as e:
        logger.error(f"Error in BSE real-time stream: {e}")



async def handle_market_status(fetcher):
    """Handle market status check"""
    try:
        nse_status = await fetcher.get_market_status('NSE')
        bse_status = await fetcher.get_market_status('BSE')
        
        print(f"\nNSE Market Status: {nse_status}")
        print(f"BSE Market Status: {bse_status}")
        
    except Exception as e:
        logger.error(f"Error fetching market status: {e}")

if __name__ == "__main__":
    asyncio.run(main())