# ibkr_1min_1year_downloader.py
from ib_insync import IB, Stock, util
import pandas as pd
import os
from datetime import datetime, timedelta
import time

class IBKR1MinDownloader:
    def __init__(self):
        self.ib = IB()
        
    def connect(self):
        """Connect to IBKR synchronously"""
        try:
            self.ib.connect('127.0.0.1', 7497, clientId=1, timeout=30)
            print("✅ Connected to IBKR")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def download_1min_data_chunked(self, symbol, total_days=365):
        """
        Download 1-minute data in small chunks to avoid IBKR limits
        """
        print(f"📥 Downloading {symbol} 1-min data for {total_days} days...")
        
        end_date = datetime.now()
        all_data = []
        
        # IBKR has limits on how much 1-min data you can request at once
        # We'll use 7-day chunks which should work reliably
        days_per_chunk = 7
        chunk_count = 0
        
        for chunk_start_day in range(0, total_days, days_per_chunk):
            chunk_end = end_date - timedelta(days=chunk_start_day)
            chunk_start = chunk_end - timedelta(days=days_per_chunk)
            
            # Skip future dates
            if chunk_start > datetime.now():
                continue
                
            chunk_count += 1
            print(f"   Chunk {chunk_count}: {chunk_start.date()} to {chunk_end.date()}")
            
            try:
                contract = Stock(symbol, 'SMART', 'USD')
                self.ib.qualifyContracts(contract)
                
                # Request 1-minute data for this chunk
                bars = self.ib.reqHistoricalData(
                    contract,
                    endDateTime=chunk_end.strftime('%Y%m%d %H:%M:%S'),
                    durationStr=f'{days_per_chunk} D',
                    barSizeSetting='1 min',  # 1-minute data!
                    whatToShow='TRADES',
                    useRTH=True,  # Regular Trading Hours only
                    formatDate=1,
                    timeout=90  # Longer timeout for 1-min data
                )
                
                if bars:
                    df = util.df(bars)
                    if not df.empty:
                        all_data.append(df)
                        print(f"     ✅ Got {len(df)} 1-min bars")
                        
                        # Show progress
                        total_bars = sum(len(chunk) for chunk in all_data)
                        estimated_total = (total_days * 6.5 * 60)  # 6.5 hours/day * 60 min/hour
                        progress_pct = (total_bars / estimated_total) * 100
                        print(f"     📊 Progress: {total_bars} bars ({progress_pct:.1f}%)")
                    else:
                        print(f"     ⚠️  No data for this period")
                else:
                    print(f"     ⚠️  Empty response")
                
                # Be nice to IBKR - longer delay for 1-min data
                time.sleep(3)
                
            except Exception as e:
                print(f"     ❌ Chunk failed: {e}")
                # Continue with next chunk
                continue
        
        if all_data:
            combined_data = pd.concat(all_data, ignore_index=True)
            combined_data.sort_values('date', inplace=True)
            combined_data.drop_duplicates(subset=['date'], inplace=True)
            return combined_data
        else:
            return pd.DataFrame()
    
    def download_with_retry(self, symbol, total_days=365):
        """
        Try different chunk sizes if we hit limits
        """
        print(f"\n🎯 DOWNLOADING 1-YEAR 1-MIN DATA FOR {symbol}")
        print("=" * 60)
        
        # Try 7-day chunks first (most reliable)
        data = self.download_1min_data_chunked(symbol, days_per_chunk=7, total_days=total_days)
        
        if data.empty or len(data) < 1000:  # If we got very little data
            print("🔄 Retrying with 5-day chunks...")
            data = self.download_1min_data_chunked(symbol, days_per_chunk=5, total_days=min(total_days, 180))
        
        if data.empty or len(data) < 1000:
            print("🔄 Retrying with 3-day chunks...")
            data = self.download_1min_data_chunked(symbol, days_per_chunk=3, total_days=min(total_days, 90))
        
        return data
    
    def download_1min_data_chunked(self, symbol, days_per_chunk=7, total_days=365):
        """
        Download with configurable chunk size
        """
        print(f"📥 Downloading {symbol} 1-min data in {days_per_chunk}-day chunks...")
        
        end_date = datetime.now()
        all_data = []
        chunk_count = 0
        
        for chunk_start_day in range(0, total_days, days_per_chunk):
            chunk_end = end_date - timedelta(days=chunk_start_day)
            chunk_start = chunk_end - timedelta(days=days_per_chunk)
            
            # Skip future dates
            if chunk_start > datetime.now():
                continue
                
            chunk_count += 1
            print(f"   Chunk {chunk_count}: {chunk_start.date()} to {chunk_end.date()}")
            
            try:
                contract = Stock(symbol, 'SMART', 'USD')
                self.ib.qualifyContracts(contract)
                
                bars = self.ib.reqHistoricalData(
                    contract,
                    endDateTime=chunk_end.strftime('%Y%m%d %H:%M:%S'),
                    durationStr=f'{days_per_chunk} D',
                    barSizeSetting='1 min',
                    whatToShow='TRADES',
                    useRTH=True,
                    formatDate=1,
                    timeout=120
                )
                
                if bars:
                    df = util.df(bars)
                    if not df.empty:
                        all_data.append(df)
                        print(f"     ✅ Got {len(df)} 1-min bars")
                    else:
                        print(f"     ⚠️  No data for this period")
                else:
                    print(f"     ⚠️  Empty response")
                
                time.sleep(3)  # Important: respect IBKR rate limits
                
            except Exception as e:
                print(f"     ❌ Chunk failed: {e}")
                continue
        
        if all_data:
            combined_data = pd.concat(all_data, ignore_index=True)
            combined_data.sort_values('date', inplace=True)
            combined_data.drop_duplicates(subset=['date'], inplace=True)
            return combined_data
        else:
            return pd.DataFrame()
    
    def save_data(self, symbol, data):
        """Save downloaded 1-minute data"""
        if data.empty:
            print(f"❌ No data to save for {symbol}")
            return False
        
        os.makedirs('data/historical', exist_ok=True)
        filename = f"data/historical/{symbol}_IBKR_1min_1year_{datetime.now().strftime('%Y%m%d')}.csv"
        data.to_csv(filename, index=False)
        
        # Calculate some stats
        total_bars = len(data)
        date_range = data['date'].min(), data['date'].max()
        days_covered = (date_range[1] - date_range[0]).days
        
        print(f"💾 Saved {total_bars:,} 1-min bars to {filename}")
        print(f"📊 Coverage: {days_covered} days from {date_range[0]} to {date_range[1]}")
        
        return True
    
    def run(self):
        """Main download process for 1-year 1-minute data"""
        if not self.connect():
            return
        
        symbols = ['SPY', 'QQQ']
        results = {}
        
        for symbol in symbols:
            try:
                print(f"\n{'='*60}")
                print(f"🚀 DOWNLOADING 1-YEAR 1-MIN DATA: {symbol}")
                print(f"{'='*60}")
                
                # Download 1-year of 1-minute data
                data = self.download_with_retry(symbol, total_days=365)
                
                if not data.empty:
                    self.save_data(symbol, data)
                    results[symbol] = {
                        'bars': len(data),
                        'period': f"{data['date'].min()} to {data['date'].max()}",
                        'days': (data['date'].max() - data['date'].min()).days
                    }
                else:
                    results[symbol] = {'bars': 0, 'period': 'No data', 'days': 0}
                    
            except Exception as e:
                print(f"❌ Failed to download {symbol}: {e}")
                results[symbol] = {'bars': 0, 'period': f'Error: {e}', 'days': 0}
        
        # Print final summary
        print(f"\n🎉 1-YEAR 1-MIN DOWNLOAD SUMMARY:")
        print("=" * 60)
        for symbol, result in results.items():
            if result['bars'] > 0:
                expected_bars = result['days'] * 6.5 * 60  # 6.5 trading hours/day
                completeness = (result['bars'] / expected_bars) * 100
                print(f"📈 {symbol}: {result['bars']:,} 1-min bars")
                print(f"   📅 {result['days']} days coverage")
                print(f"   📊 Data completeness: {completeness:.1f}%")
                print(f"   🗓️  Period: {result['period']}")
            else:
                print(f"❌ {symbol}: FAILED - {result['period']}")
        
        self.ib.disconnect()
        print("🔌 Disconnected from IBKR")

def main():
    downloader = IBKR1MinDownloader()
    downloader.run()

if __name__ == "__main__":
    main()
