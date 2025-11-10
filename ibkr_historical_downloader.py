# ibkr_historical_downloader.py
from ib_insync import *
import pandas as pd
from datetime import datetime, timedelta
import os

class IBKRDataDownloader:
    def __init__(self):
        self.ib = IB()
        
    def connect(self):
        """Connect to IBKR TWS or Gateway"""
        try:
            # Connect to TWS (port 7497) or Gateway (port 4001)
            self.ib.connect('127.0.0.1', 7497, clientId=1)
            print("✅ Connected to IBKR")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def create_contract(self, symbol, sec_type='STK', exchange='SMART', currency='USD'):
        """Create IBKR contract"""
        contract = Contract()
        contract.symbol = symbol
        contract.secType = sec_type
        contract.exchange = exchange
        contract.currency = currency
        return contract
    
    def download_historical_data(self, symbol, duration='1 Y', bar_size='1 min'):
        """Download historical data from IBKR"""
        print(f"📥 Downloading {symbol} {bar_size} data for {duration}...")
        
        contract = self.create_contract(symbol)
        
        try:
            # Request historical data
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow='TRADES',
                useRTH=True,  # Regular Trading Hours only
                formatDate=1,
                keepUpToDate=False
            )
            
            # Convert to DataFrame
            df = util.df(bars)
            
            if not df.empty:
                # Clean up column names
                df = df.rename(columns={'date': 'timestamp'})
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                print(f"✅ Downloaded {len(df)} bars for {symbol}")
                return df
            else:
                print(f"❌ No data returned for {symbol}")
                return None
                
        except Exception as e:
            print(f"❌ Error downloading {symbol}: {e}")
            return None
    
    def download_multiple_symbols(self, symbols, duration='1 Y', bar_size='1 min'):
        """Download data for multiple symbols"""
        all_data = {}
        
        for symbol in symbols:
            data = self.download_historical_data(symbol, duration, bar_size)
            if data is not None:
                all_data[symbol] = data
                
                # Save immediately
                filename = f"data/historical/{symbol}_{bar_size.replace(' ', '')}_{duration.replace(' ', '')}_{datetime.now().strftime('%Y%m%d')}.csv"
                data.to_csv(filename, index=False)
                print(f"💾 Saved: {filename}")
            
            # Small delay between requests
            self.ib.sleep(1)
        
        return all_data
    
    def disconnect(self):
        """Disconnect from IBKR"""
        self.ib.disconnect()
        print("🔌 Disconnected from IBKR")

def main():
    # Create data directory
    os.makedirs("data/historical", exist_ok=True)
    
    # Initialize downloader
    downloader = IBKRDataDownloader()
    
    # Connect to IBKR
    if downloader.connect():
        try:
            # Symbols to download
            symbols = ['SPY', 'QQQ']
            
            # Download 1 year of 1-minute data
            print("🚀 DOWNLOADING HIGH-QUALITY IBKR DATA...")
            all_data = downloader.download_multiple_symbols(
                symbols=symbols,
                duration='1 Y',      # 1 year
                bar_size='1 min'     # 1 minute bars
            )
            
            print(f"\n🎉 DOWNLOAD COMPLETE!")
            for symbol, data in all_data.items():
                print(f"📈 {symbol}: {len(data):,} bars | {data['timestamp'].min()} to {data['timestamp'].max()}")
                
        finally:
            downloader.disconnect()
    else:
        print("❌ Cannot proceed without IBKR connection")

if __name__ == "__main__":
    main()
