#!/usr/bin/env python3
"""
Robust Data Downloader for IBKR Scalper
"""

import yfinance as yf
import pandas as pd
import logging
from datetime import datetime, timedelta
import time
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RobustDataDownloader:
    def __init__(self):
        self.symbols = ['SPY', 'QQQ']
        os.makedirs('data/historical', exist_ok=True)
        
    def download_with_retry(self, symbol, max_retries=3):
        """Download data with retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1} for {symbol}...")
                
                ticker = yf.Ticker(symbol)
                
                # Try different period options
                periods_to_try = [
                    ("1y", "1h"),    # 1 year, hourly
                    ("6mo", "1h"),   # 6 months, hourly
                    ("3mo", "1h"),   # 3 months, hourly
                    ("1mo", "1h"),   # 1 month, hourly
                    ("1y", "1d"),    # 1 year, daily (fallback)
                ]
                
                for period, interval in periods_to_try:
                    try:
                        logger.info(f"Trying {symbol} with period={period}, interval={interval}")
                        data = ticker.history(period=period, interval=interval)
                        
                        if not data.empty:
                            logger.info(f"✅ {symbol}: {len(data)} bars with period={period}")
                            return data
                            
                    except Exception as e:
                        logger.warning(f"Failed {symbol} with period={period}: {e}")
                        continue
                
                # If all periods fail, try manual date range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                try:
                    data = ticker.history(start=start_date, end=end_date, interval="1h")
                    if not data.empty:
                        logger.info(f"✅ {symbol}: {len(data)} bars with date range")
                        return data
                except:
                    pass
                    
                logger.warning(f"⚠️ No data found for {symbol} on attempt {attempt + 1}")
                time.sleep(2)  # Wait before retry
                
            except Exception as e:
                logger.error(f"❌ Error downloading {symbol}: {e}")
                time.sleep(2)
                
        return None
    
    def download_all_data(self):
        """Download data for all symbols"""
        all_data = {}
        
        for symbol in self.symbols:
            data = self.download_with_retry(symbol)
            if data is not None:
                all_data[symbol] = data
                # Save immediately
                self.save_data(symbol, data)
            else:
                logger.error(f"❌ Failed to download {symbol} after all attempts")
                
        return all_data
    
    def save_data(self, symbol, data):
        """Save data to CSV"""
        filename = f"data/historical/{symbol}.csv"
        data.to_csv(filename)
        logger.info(f"💾 Saved {symbol} data to {filename} ({len(data)} bars)")
        
    def validate_data(self, data):
        """Validate downloaded data"""
        if not data:
            return False
            
        for symbol, symbol_data in data.items():
            if symbol_data.empty:
                logger.error(f"❌ {symbol} data is empty")
                return False
                
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in symbol_data.columns]
            if missing_columns:
                logger.error(f"❌ {symbol} missing columns: {missing_columns}")
                return False
                
            logger.info(f"✅ {symbol} validation passed: {len(symbol_data)} bars")
            
        return True

def main():
    print("🚀 Robust Data Downloader")
    print("=" * 30)
    
    downloader = RobustDataDownloader()
    
    print("📥 Downloading market data...")
    data = downloader.download_all_data()
    
    if downloader.validate_data(data):
        print(f"\n🎉 SUCCESS! Downloaded {len(data)} symbols")
        for symbol, symbol_data in data.items():
            print(f"   {symbol}: {len(symbol_data)} bars")
            print(f"   Date range: {symbol_data.index[0]} to {symbol_data.index[-1]}")
    else:
        print("\n❌ Data download failed")
        print("💡 Trying alternative approach...")
        try_alternative_approach()

def try_alternative_approach():
    """Alternative approach using different method"""
    print("\n🔄 Trying alternative download method...")
    
    try:
        # Try using download instead of history
        import yfinance as yf
        
        data = yf.download(
            tickers="SPY QQQ",
            period="6mo",
            interval="1h",
            group_by='ticker',
            auto_adjust=True
        )
        
        if not data.empty:
            print("✅ Alternative method worked!")
            
            # Save SPY data
            if 'SPY' in data:
                spy_data = data['SPY']
                spy_data.to_csv('data/historical/SPY_alt.csv')
                print(f"✅ Saved SPY: {len(spy_data)} bars")
                
            # Save QQQ data  
            if 'QQQ' in data:
                qqq_data = data['QQQ']
                qqq_data.to_csv('data/historical/QQQ_alt.csv')
                print(f"✅ Saved QQQ: {len(qqq_data)} bars")
                
        else:
            print("❌ Alternative method also failed")
            
    except Exception as e:
        print(f"❌ Alternative method error: {e}")

if __name__ == "__main__":
    main()