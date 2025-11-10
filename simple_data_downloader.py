# simple_data_downloader.py
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os

def download_high_quality_data():
    """Download the best available data using yfinance workarounds"""
    print("🚀 DOWNLOADING HIGH-QUALITY MARKET DATA...")
    
    # Create directory
    os.makedirs("data/historical", exist_ok=True)
    
    symbols = ['SPY', 'QQQ']
    all_data = {}
    
    for symbol in symbols:
        print(f"\n{'='*50}")
        print(f"📊 DOWNLOADING {symbol}")
        print(f"{'='*50}")
        
        # METHOD 1: Try 2-minute data (often works when 1-minute fails)
        print("🔄 Trying 2-minute data...")
        try:
            data_2min = yf.download(symbol, period="1y", interval="2m")
            if len(data_2min) > 1000:  # Reasonable amount of data
                filename = f"data/historical/{symbol}_2min_1year_{datetime.now().strftime('%Y%m%d')}.csv"
                data_2min.to_csv(filename)
                print(f"✅ 2-min data: {len(data_2min):,} bars")
                all_data[symbol] = data_2min
                continue
        except:
            pass
        
        # METHOD 2: Try 5-minute data (very reliable)
        print("🔄 Trying 5-minute data...")
        try:
            data_5min = yf.download(symbol, period="1y", interval="5m")
            filename = f"data/historical/{symbol}_5min_1year_{datetime.now().strftime('%Y%m%d')}.csv"
            data_5min.to_csv(filename)
            print(f"✅ 5-min data: {len(data_5min):,} bars")
            all_data[symbol] = data_5min
            continue
        except Exception as e:
            print(f"❌ 5-min failed: {e}")
        
        # METHOD 3: Download daily data and resample (fallback)
        print("🔄 Downloading daily data as fallback...")
        try:
            data_daily = yf.download(symbol, period="2y", interval="1d")
            filename = f"data/historical/{symbol}_daily_2year_{datetime.now().strftime('%Y%m%d')}.csv"
            data_daily.to_csv(filename)
            print(f"✅ Daily data: {len(data_daily):,} bars")
            all_data[symbol] = data_daily
        except Exception as e:
            print(f"❌ All methods failed for {symbol}: {e}")
    
    return all_data

def update_backtester_for_new_data(data_type="5min"):
    """Show how to update your main.py for the new data"""
    print(f"\n🔧 UPDATING YOUR BACKTESTER FOR {data_type.upper()} DATA:")
    
    if data_type == "2min":
        print("""
# In main.py, change this line:
data_path = "data/historical/SPY_2min_1year_20241219.csv"

# Update time-based parameters:
risk:
  max_hold_minutes: 20    # Now = 10 bars (still works!)
        """)
    elif data_type == "5min":
        print("""
# In main.py, change this line:
data_path = "data/historical/SPY_5min_1year_20241219.csv"

# Update time-based parameters:
risk:
  max_hold_minutes: 20    # Now = 4 bars (still works!)
  
trading:
  avoid_open_minutes: 15  # Now = 3 bars
  avoid_close_minutes: 30 # Now = 6 bars
        """)

def main():
    print("🎯 SMART DATA DOWNLOADER")
    print("==========================================")
    print("This will try multiple methods to get the best available data")
    print("==========================================")
    
    # Download data
    all_data = download_high_quality_data()
    
    # Results
    print(f"\n🎉 DOWNLOAD SUMMARY:")
    print("==========================================")
    for symbol, data in all_data.items():
        if data is not None:
            print(f"📈 {symbol}: {len(data):,} bars")
            print(f"   File: data/historical/{symbol}_*.csv")
            print(f"   Period: {data.index[0]} to {data.index[-1]}")
        else:
            print(f"❌ {symbol}: Failed to download")
    
    # Show how to update backtester
    if all_data:
        first_symbol = list(all_data.keys())[0]
        first_data = all_data[first_symbol]
        if '2min' in first_data.index.inferred_freq:
            update_backtester_for_new_data("2min")
        elif '5min' in first_data.index.inferred_freq:
            update_backtester_for_new_data("5min")
        else:
            update_backtester_for_new_data("daily")

if __name__ == "__main__":
    main()
