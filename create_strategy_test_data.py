#!/usr/bin/env python3
"""
Create Data That Specifically Triggers Strategy Signals
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def create_signal_test_data():
    """Create data that will definitely trigger strategy signals"""
    print("🎯 Creating Strategy Signal Test Data")
    print("=" * 45)
    
    os.makedirs('data/historical', exist_ok=True)
    
    # Create 1 day of 1-minute data with clear signals
    base_date = datetime(2024, 1, 10)  # Fixed date for consistency
    dates = []
    
    # Market hours: 9:30 AM to 4:00 PM
    market_open = base_date.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = base_date.replace(hour=16, minute=0, second=0, microsecond=0)
    
    current_time = market_open
    while current_time <= market_close:
        dates.append(current_time)
        current_time += timedelta(minutes=1)
    
    print(f"📅 Created 1-day test data: {len(dates)} 1-minute bars")
    
    # Create data that WILL trigger signals
    spy_bullish = create_bullish_signal_data(dates, 'SPY', 450)
    spy_bearish = create_bearish_signal_data(dates, 'SPY', 450)
    qqq_bullish = create_bullish_signal_data(dates, 'QQQ', 380)
    
    # Save test data
    spy_bullish.to_csv('data/historical/SPY_bullish_signal.csv')
    spy_bearish.to_csv('data/historical/SPY_bearish_signal.csv') 
    qqq_bullish.to_csv('data/historical/QQQ_bullish_signal.csv')
    
    print(f"\n💾 Saved signal test data:")
    print(f"   SPY_bullish_signal.csv - Should trigger BUY_CALL")
    print(f"   SPY_bearish_signal.csv - Should trigger BUY_PUT") 
    print(f"   QQQ_bullish_signal.csv - Should trigger BUY_CALL")
    
    return spy_bullish, spy_bearish, qqq_bullish

def create_bullish_signal_data(dates, symbol, start_price):
    """Create data that triggers BUY_CALL signals"""
    print(f"\n📈 Creating BULLISH signal data for {symbol}...")
    
    np.random.seed(42)
    
    # Phase 1: Consolidation (first 100 bars)
    prices = [start_price]
    for i in range(1, 100):
        # Sideways movement
        change = np.random.normal(0, 0.0001)
        prices.append(prices[-1] * (1 + change))
    
    # Phase 2: STRONG BULLISH BREAKOUT (bars 100-150)
    # This should trigger all our bullish conditions
    for i in range(100, 150):
        if i < len(dates):
            # Strong bullish momentum
            change = np.random.normal(0.0005, 0.0001)  # Strong uptrend
            prices.append(prices[-1] * (1 + change))
    
    # Ensure we have enough data points
    while len(prices) < len(dates):
        prices.append(prices[-1] * (1 + np.random.normal(0.0001, 0.0001)))
    
    prices = prices[:len(dates)]  # Trim to match dates
    
    # Create OHLC data with BULLISH patterns
    data = pd.DataFrame(index=dates[:len(prices)])
    data['Close'] = prices
    
    # Create bullish OHLC patterns
    data['Open'] = data['Close'].shift(1).fillna(start_price)  # Open at previous close
    data['High'] = data[['Open', 'Close']].max(axis=1) * (1 + np.random.uniform(0.0001, 0.0003))
    data['Low'] = data[['Open', 'Close']].min(axis=1) * (1 - np.random.uniform(0.0001, 0.0002))
    data['Volume'] = np.random.randint(50000, 150000, len(data))
    
    # ADD SPECIFIC BULLISH PATTERNS THAT TRIGGER OUR STRATEGY
    
    # 1. Bullish Engulfing Pattern at bar 120
    if 120 < len(data):
        # Bearish candle first
        data.loc[data.index[119], 'Open'] = data['Close'].iloc[118] * 1.002
        data.loc[data.index[119], 'Close'] = data['Open'].iloc[119] * 0.998
        data.loc[data.index[119], 'Volume'] = 80000
        
        # Bullish engulfing candle
        data.loc[data.index[120], 'Open'] = data['Close'].iloc[119] * 0.998  # Lower open
        data.loc[data.index[120], 'Close'] = data['Open'].iloc[120] * 1.004  # Higher close - ENGULFING
        data.loc[data.index[120], 'High'] = data['Close'].iloc[120] * 1.001
        data.loc[data.index[120], 'Low'] = data['Open'].iloc[120] * 0.999
        data.loc[data.index[120], 'Volume'] = 250000  # HIGH VOLUME
    
    # 2. Ensure HA and EMA alignment
    # Strong uptrend from bar 100 onwards
    for i in range(100, min(130, len(data))):
        data.loc[data.index[i], 'Close'] = data['Close'].iloc[i-1] * 1.001  # Consistent gains
        data.loc[data.index[i], 'Open'] = data['Close'].iloc[i-1]  # Gap up opens
        data.loc[data.index[i], 'Volume'] = 200000  # Sustained high volume
    
    # 3. Strong finish
    if len(data) > 200:
        for i in range(200, min(250, len(data))):
            data.loc[data.index[i], 'Close'] = data['Close'].iloc[i-1] * 1.0008
            data.loc[data.index[i], 'Volume'] = 180000
    
    print(f"   ✅ Created bullish data with patterns")
    print(f"   📊 Price range: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")
    
    return data

def create_bearish_signal_data(dates, symbol, start_price):
    """Create data that triggers BUY_PUT signals"""
    print(f"\n📉 Creating BEARISH signal data for {symbol}...")
    
    np.random.seed(43)
    
    # Phase 1: Uptrend (first 100 bars)
    prices = [start_price]
    for i in range(1, 100):
        # Small uptrend
        change = np.random.normal(0.0002, 0.0001)
        prices.append(prices[-1] * (1 + change))
    
    # Phase 2: STRONG BEARISH BREAKDOWN (bars 100-150)
    for i in range(100, 150):
        if i < len(dates):
            # Strong bearish momentum
            change = np.random.normal(-0.0005, 0.0001)  # Strong downtrend
            prices.append(prices[-1] * (1 + change))
    
    while len(prices) < len(dates):
        prices.append(prices[-1] * (1 + np.random.normal(-0.0001, 0.0001)))
    
    prices = prices[:len(dates)]
    
    data = pd.DataFrame(index=dates[:len(prices)])
    data['Close'] = prices
    data['Open'] = data['Close'].shift(1).fillna(start_price)
    data['High'] = data[['Open', 'Close']].max(axis=1) * (1 + np.random.uniform(0.0001, 0.0002))
    data['Low'] = data[['Open', 'Close']].min(axis=1) * (1 - np.random.uniform(0.0001, 0.0003))
    data['Volume'] = np.random.randint(50000, 150000, len(data))
    
    # ADD SPECIFIC BEARISH PATTERNS
    
    # 1. Bearish Engulfing Pattern at bar 120
    if 120 < len(data):
        # Bullish candle first
        data.loc[data.index[119], 'Open'] = data['Close'].iloc[118] * 0.998
        data.loc[data.index[119], 'Close'] = data['Open'].iloc[119] * 1.002
        data.loc[data.index[119], 'Volume'] = 80000
        
        # Bearish engulfing candle
        data.loc[data.index[120], 'Open'] = data['Close'].iloc[119] * 1.002  # Higher open
        data.loc[data.index[120], 'Close'] = data['Open'].iloc[120] * 0.996  # Lower close - ENGULFING
        data.loc[data.index[120], 'High'] = data['Open'].iloc[120] * 1.001
        data.loc[data.index[120], 'Low'] = data['Close'].iloc[120] * 0.999
        data.loc[data.index[120], 'Volume'] = 250000  # HIGH VOLUME
    
    # 2. Ensure bearish trend alignment
    for i in range(100, min(130, len(data))):
        data.loc[data.index[i], 'Close'] = data['Close'].iloc[i-1] * 0.999  # Consistent declines
        data.loc[data.index[i], 'Volume'] = 200000
    
    print(f"   ✅ Created bearish data with patterns")
    print(f"   📊 Price range: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")
    
    return data

def test_signal_data():
    """Test the strategy with our signal data"""
    print("\n🧪 Testing Strategy with Signal Data")
    print("=" * 45)
    
    from strategies.scalping_1min import Scalping1MinStrategy
    
    test_files = {
        'SPY Bullish': 'data/historical/SPY_bullish_signal.csv',
        'SPY Bearish': 'data/historical/SPY_bearish_signal.csv',
        'QQQ Bullish': 'data/historical/QQQ_bullish_signal.csv'
    }
    
    strategy = Scalping1MinStrategy()
    
    for test_name, filepath in test_files.items():
        print(f"\n🔍 Testing {test_name}...")
        
        try:
            data = pd.read_csv(filepath, index_col=0, parse_dates=True)
            
            # Test at the pattern point (bar 120)
            if len(data) >= 120:
                test_data = data.iloc[:120]
                analysis = strategy.analyze_market(test_data)
                
                if analysis:
                    print(f"   Signal: {analysis['signal']}")
                    print(f"   HA Trend: {analysis['ha_trend']}")
                    print(f"   EMA Trend: {analysis['ema_trend']}")
                    print(f"   Trend Strength: {analysis['trend_strength']:.2f}")
                    print(f"   Volume Ratio: {analysis['volume_ratio']:.2f}")
                    print(f"   Patterns: Bullish={analysis['bullish_pattern']}, Bearish={analysis['bearish_pattern']}")
                    
                    expected_signal = 'BUY_CALL' if 'Bullish' in test_name else 'BUY_PUT'
                    
                    if analysis['signal'] == expected_signal:
                        print(f"   ✅ SUCCESS: Correct {expected_signal} signal!")
                    else:
                        print(f"   ❌ Expected {expected_signal}, got {analysis['signal']}")
                else:
                    print("   ❌ No analysis returned")
            else:
                print("   ⚠️ Not enough data for testing")
                
        except Exception as e:
            print(f"   ❌ Error testing {test_name}: {e}")

def main():
    print("🚀 Strategy Signal Test Data Creator")
    print("=" * 40)
    
    # Create test data with clear signals
    create_signal_test_data()
    
    # Test the strategy with our signal data
    test_signal_data()
    
    print(f"\n💡 Signal test data created!")
    print(f"📁 Files in data/historical/ with *_signal.csv")
    print(f"🎯 These should trigger specific trading signals")

if __name__ == "__main__":
    main()