#!/usr/bin/env python3
"""
Create Test Data with Proper Volume for Strategy Signals
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def create_volume_fixed_data():
    """Create data with volume that meets strategy requirements"""
    print("📊 Creating Volume-Fixed Test Data")
    print("=" * 45)
    
    os.makedirs('data/historical', exist_ok=True)
    
    # Create 1 day of 1-minute data
    base_date = datetime(2024, 1, 10)
    dates = []
    
    market_open = base_date.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = base_date.replace(hour=16, minute=0, second=0, microsecond=0)
    
    current_time = market_open
    while current_time <= market_close:
        dates.append(current_time)
        current_time += timedelta(minutes=1)
    
    print(f"📅 Created 1-day data: {len(dates)} 1-minute bars")
    
    # Create data with HIGH VOLUME at pattern points
    spy_high_volume = create_high_volume_data(dates, 'SPY', 450)
    
    spy_high_volume.to_csv('data/historical/SPY_high_volume.csv')
    
    print(f"\n💾 Saved volume-fixed data:")
    print(f"   SPY_high_volume.csv - With proper volume ratios")
    
    return spy_high_volume

def create_high_volume_data(dates, symbol, start_price):
    """Create data with volume that meets strategy thresholds"""
    print(f"\n📈 Creating high-volume data for {symbol}...")
    
    np.random.seed(42)
    
    # Base prices with clear trend
    prices = [start_price]
    for i in range(1, len(dates)):
        # Small overall uptrend
        trend = 0.00005  # Very small trend
        noise = np.random.normal(0, 0.0002)
        prices.append(prices[-1] * (1 + trend + noise))
    
    data = pd.DataFrame(index=dates)
    data['Close'] = prices
    data['Open'] = data['Close'].shift(1).fillna(start_price)
    data['High'] = data[['Open', 'Close']].max(axis=1) * (1.0001)
    data['Low'] = data[['Open', 'Close']].min(axis=1) * (0.9999)
    
    # Set BASE volume (this will be our average)
    base_volume = 100000
    data['Volume'] = np.random.randint(80000, 120000, len(data))
    
    # ADD HIGH VOLUME PATTERNS THAT MEET STRATEGY REQUIREMENTS
    
    # Pattern 1: Bullish engulfing with HIGH VOLUME at bar 100
    if 100 < len(data):
        # Setup: Normal volume bearish candle
        data.loc[data.index[99], 'Open'] = data['Close'].iloc[98] * 1.001
        data.loc[data.index[99], 'Close'] = data['Open'].iloc[99] * 0.999
        data.loc[data.index[99], 'Volume'] = 100000  # Normal volume
        
        # Bullish engulfing with VERY HIGH VOLUME (3x average)
        data.loc[data.index[100], 'Open'] = data['Close'].iloc[99] * 0.999
        data.loc[data.index[100], 'Close'] = data['Open'].iloc[100] * 1.003
        data.loc[data.index[100], 'High'] = data['Close'].iloc[100] * 1.001
        data.loc[data.index[100], 'Low'] = data['Open'].iloc[100] * 0.999
        data.loc[data.index[100], 'Volume'] = 300000  # 3x volume - should meet threshold
    
    # Pattern 2: Sustained high volume trend from bar 150-160
    for i in range(150, min(160, len(data))):
        data.loc[data.index[i], 'Close'] = data['Close'].iloc[i-1] * 1.001  # Uptrend
        data.loc[data.index[i], 'Open'] = data['Close'].iloc[i-1]
        data.loc[data.index[i], 'Volume'] = 250000  # 2.5x volume
    
    # Pattern 3: Bearish pattern with high volume at bar 200
    if 200 < len(data):
        # Setup: Normal volume bullish candle
        data.loc[data.index[199], 'Open'] = data['Close'].iloc[198] * 0.999
        data.loc[data.index[199], 'Close'] = data['Open'].iloc[199] * 1.001
        data.loc[data.index[199], 'Volume'] = 100000
        
        # Bearish engulfing with HIGH VOLUME
        data.loc[data.index[200], 'Open'] = data['Close'].iloc[199] * 1.001
        data.loc[data.index[200], 'Close'] = data['Open'].iloc[200] * 0.997
        data.loc[data.index[200], 'Volume'] = 280000  # 2.8x volume
    
    print(f"   ✅ Created data with high-volume patterns")
    print(f"   📊 Volume range: {data['Volume'].min()} - {data['Volume'].max()}")
    
    return data

def test_volume_data():
    """Test the volume-fixed data"""
    print("\n🧪 Testing Volume-Fixed Data")
    print("=" * 35)
    
    from strategies.debug_scalper import DebugScalpingStrategy
    
    strategy = DebugScalpingStrategy()
    data = pd.read_csv('data/historical/SPY_high_volume.csv', index_col=0, parse_dates=True)
    
    # Test at high-volume pattern points
    test_points = [100, 110, 150, 155, 200, 210]
    
    for point in test_points:
        if point < len(data):
            print(f"\n" + "-"*40)
            print(f"🧪 Testing at bar {point}")
            print("-"*40)
            
            test_data = data.iloc[:point]
            analysis = strategy.analyze_market(test_data)
            
            if analysis:
                print(f"📊 Result: {analysis['signal']}")
                if analysis['signal'] != 'HOLD':
                    print(f"🎉 SIGNAL GENERATED!")
                    break
            else:
                print("❌ No analysis returned")

def main():
    print("🚀 Volume-Fixed Test Data Creator")
    print("=" * 40)
    
    # Create data with proper volume
    create_volume_fixed_data()
    
    # Test the volume-fixed data
    test_volume_data()
    
    print(f"\n💡 Volume-fixed data created!")
    print(f"📁 File: data/historical/SPY_high_volume.csv")

if __name__ == "__main__":
    main()