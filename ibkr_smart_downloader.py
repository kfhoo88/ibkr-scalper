# ibkr_smart_downloader.py
from ib_insync import IB, Stock, util
import pandas as pd
import asyncio
import os
from datetime import datetime, timedelta
import time

class IBKRSmartDownloader:
    def __init__(self):
        self.ib = IB()
        
    async def connect(self):
        """Connect to IBKR"""
        try:
            await self.ib.connectAsync('127.0.0.1', 7497, clientId=1, timeout=30)
            print("✅ Connected to IBKR")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def download_chunked_data(self, symbol, days_per_chunk=30, total_days=365):
        """
        Download data in smaller chunks to avoid timeouts
        """
        print(f"📥 Downloading {symbol} in {days_per_chunk}-day chunks...")
        
        end_date = datetime.now()
        all_data = []
        
        for chunk in range(0, total_days, days_per_chunk):
            chunk_start = end_date - timedelta(days=chunk + days_per_chunk)
            chunk_end = end_date - timedelta(days=chunk)
            
            # Skip future dates
            if chunk_start > datetime.now():
                continue
                
            print(f"   Chunk {chunk//days_per_chunk + 1}: {chunk_start.date()} to {chunk_end.date()}")
            
            try:
                contract = Stock(symbol, 'SMART', 'USD')
                self.ib.qualifyContracts(contract)
                
                # Request 1-minute data for this chunk
                data = await self.ib.reqHistoricalDataAsync(
                    contract,
                    endDateTime=chunk_end.strftime('%Y%m%d %H:%M:%S'),
                    durationStr=f'{days_per_chunk} D',
                    barSizeSetting='1 min',
                    whatToShow='TRADES',
                    useRTH=True,
                    formatDate=1,
                    timeout=60  # 60 second timeout per chunk
                )
                
                if data:
                    df = util.df(data)
                    if not df.empty:
                        all_data.append(df)
                        print(f"     ✅ Got {len(df)} bars")
                    else:
                        print(f"     ⚠️  No data for this period")
                else:
                    print(f"     ⚠️  Empty response")
                
                # Be nice to IBKR - add delay between requests
                await asyncio.sleep(2)
                
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
    
    async def download_with_fallback(self, symbol, total_days=365):
        """
        Try different approaches to get data
        """
        print(f"\n🎯 ATTEMPTING TO DOWNLOAD {symbol}")
        print("=" * 50)
        
        # Try 30-day chunks first
        data = await self.download_chunked_data(symbol, days_per_chunk=30, total_days=total_days)
        
        if data.empty:
            print("🔄 Falling back to 15-day chunks...")
            data = await self.download_chunked_data(symbol, days_per_chunk=15, total_days=total_days)
        
        if data.empty:
            print("🔄 Falling back to 5-day chunks...")
            data = await self.download_chunked_data(symbol, days_per_chunk=7, total_days=min(total_days, 60))
        
        return data
    
    def save_data(self, symbol, data):
        """Save downloaded data"""
        if data.empty:
            print(f"❌ No data to save for {symbol}")
            return False
        
        os.makedirs('data/historical', exist_ok=True)
        filename = f"data/historical/{symbol}_IBKR_1min_{datetime.now().strftime('%Y%m%d')}.csv"
        data.to_csv(filename, index=False)
        print(f"💾 Saved {len(data)} bars to {filename}")
        return True
    
    async def run(self):
        """Main download process"""
        if not await self.connect():
            return
        
        symbols = ['SPY', 'QQQ']
        results = {}
        
        for symbol in symbols:
            try:
                data = await self.download_with_fallback(symbol, total_days=60)  # Start with 60 days
                
                if not data.empty:
                    self.save_data(symbol, data)
                    results[symbol] = {
                        'bars': len(data),
                        'period': f"{data['date'].iloc[0]} to {data['date'].iloc[-1]}"
                    }
                else:
                    results[symbol] = {'bars': 0, 'period': 'No data'}
                    
            except Exception as e:
                print(f"❌ Failed to download {symbol}: {e}")
                results[symbol] = {'bars': 0, 'period': f'Error: {e}'}
        
        # Print summary
        print(f"\n🎉 DOWNLOAD SUMMARY:")
        print("=" * 50)
        for symbol, result in results.items():
            print(f"📈 {symbol}: {result['bars']} bars")
            print(f"   Period: {result['period']}")
        
        self.ib.disconnect()

async def main():
    downloader = IBKRSmartDownloader()
    await downloader.run()

if __name__ == "__main__":
    asyncio.run(main())
