#!/usr/bin/env python3
"""
Create 1-Minute Data for Proper Scalping Strategy
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def create_1min_scalping_data():
    """Create 1-minute data specifically for scalping strategy"""
    print("📊 Creating 1-Minute Scalping Data")
    print("=" * 40)
    
    os.makedirs('data/historical', exist_ok=True)
    
    # Create 10 days of 1-minute data for scalping (realistic for testing)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=10)
    
    # Create 1-minute intervals for market hours only
    dates = []
    current_date = start_date
    
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Monday-Friday
            # Market hours: 9:30 AM to 4:00 PM
            market_open = current_date.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = current_date.replace(hour=16, minute=0, second=0, microsecond=0)
            
            current_time = market_open
            while current_time <= market_close:
                dates.append(current_time)
                current_time += timedelta(minutes=1)
        
        current_date += timedelta(days=1)
    
    print(f"📅 Created 1-minute data: {dates[0]} to {dates[-1]}")
    print(f"📈 Total 1-minute bars: {len(dates)}")
    print(f"🕒 Trading hours per day: 6.5 hours = 390 minutes")
    
    # Create 1-minute data with scalping-friendly patterns
    spy_data = create_1min_symbol_data(dates, 'SPY', 450)
    qqq_data = create_1min_symbol_data(dates, 'QQQ', 380)
    
    # Save data
    spy_data.to_csv('data/historical/SPY_1min.csv')
    qqq_data.to_csv('data/historical/QQQ_1min.csv')
    
    print(f"\n💾 Saved 1-minute data:")
    print(f"   SPY: {len(spy_data)} bars")
    print(f"   QQQ: {len(qqq_data)} bars")
    
    return spy_data, qqq_data

def create_1min_symbol_data(dates, symbol, start_price):
    """Create 1-minute data with scalping patterns"""
    print(f"\n📈 Creating 1-minute {symbol} data...")
    
    np.random.seed(42)
    
    prices = [start_price]
    opens = [start_price]
    highs = [start_price * 1.0005]  # Small spread
    lows = [start_price * 0.9995]   # Small spread
    volumes = [np.random.randint(50000, 200000)]  # Lower volume per minute
    
    # Add micro-trends and reversals for scalping
    current_trend = 0
    trend_duration = 0
    volatility = 0.0002  # Much smaller moves for 1-minute data
    
    for i in range(1, len(dates)):
        previous_close = prices[-1]
        
        # Change trends more frequently for scalping
        if trend_duration <= 0 or np.random.random() < 0.1:  # 10% chance to change trend
            current_trend = np.random.choice([-1, 0, 1])
            trend_duration = np.random.randint(5, 30)  # 5-30 minute trends
        
        trend_duration -= 1
        
        # Price movement based on trend
        if current_trend == 1:  # Uptrend
            price_change = np.random.normal(0.0001, volatility)
        elif current_trend == -1:  # Downtrend
            price_change = np.random.normal(-0.0001, volatility)
        else:  # Sideways
            price_change = np.random.normal(0, volatility)
        
        new_close = previous_close * (1 + price_change)
        
        # Create 1-minute OHLC
        new_open = previous_close  # Typically opens at previous close
        new_high = max(new_open, new_close) * (1 + abs(np.random.normal(0, volatility/2)))
        new_low = min(new_open, new_close) * (1 - abs(np.random.normal(0, volatility/2)))
        
        # Ensure realistic ranges
        price_range = new_high - new_low
        if price_range / new_open > 0.002:  # Max 0.2% range per minute
            new_high = new_open * 1.001
            new_low = new_open * 0.999
        
        prices.append(new_close)
        opens.append(new_open)
        highs.append(new_high)
        lows.append(new_low)
        
        # Volume varies with activity
        base_volume = np.random.randint(10000, 100000)
        if abs(price_change) > volatility * 2:  # Higher volume on bigger moves
            base_volume *= 2
        volumes.append(base_volume)
    
    data = pd.DataFrame({
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': prices,
        'Volume': volumes
    }, index=dates)
    
    # Add clear scalping patterns
    data = add_scalping_patterns(data, symbol)
    
    print(f"   {symbol}: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")
    return data

def add_scalping_patterns(data, symbol):
    """Add clear scalping patterns for strategy testing"""
    print(f"   Adding scalping patterns for {symbol}...")
    
    # Pattern 1: Clear bullish breakout (for CALL signals)
    bull_start = 100
    if bull_start + 20 < len(data):
        print(f"   Adding bullish pattern at index {bull_start}")
        # Create strong bullish momentum
        for i in range(bull_start, bull_start + 10):
            if i < len(data):
                # Strong bullish candles
                data.loc[data.index[i], 'Open'] = data['Close'].iloc[i-1]
                data.loc[data.index[i], 'Close'] = data['Open'].iloc[i] * 1.0015  # 0.15% up
                data.loc[data.index[i], 'High'] = data['Close'].iloc[i] * 1.0005
                data.loc[data.index[i], 'Low'] = data['Open'].iloc[i] * 0.9995
                data.loc[data.index[i], 'Volume'] = data['Volume'].iloc[i] * 3  # High volume
    
    # Pattern 2: Clear bearish breakdown (for PUT signals)  
    bear_start = 300
    if bear_start + 20 < len(data):
        print(f"   Adding bearish pattern at index {bear_start}")
        # Create strong bearish momentum
        for i in range(bear_start, bear_start + 10):
            if i < len(data):
                # Strong bearish candles
                data.loc[data.index[i], 'Open'] = data['Close'].iloc[i-1]
                data.loc[data.index[i], 'Close'] = data['Open'].iloc[i] * 0.9985  # 0.15% down
                data.loc[data.index[i], 'High'] = data['Open'].iloc[i] * 1.0005
                data.loc[data.index[i], 'Low'] = data['Close'].iloc[i] * 0.9995
                data.loc[data.index[i], 'Volume'] = data['Volume'].iloc[i] * 3  # High volume
    
    # Pattern 3: Bullish engulfing pattern
    engulf_start = 500
    if engulf_start + 2 < len(data):
        print(f"   Adding engulfing pattern at index {engulf_start}")
        # Bearish candle first
        data.loc[data.index[engulf_start-1], 'Open'] = data['Close'].iloc[engulf_start-2] * 1.001
        data.loc[data.index[engulf_start-1], 'Close'] = data['Open'].iloc[engulf_start-1] * 0.998
        
        # Bullish engulfing candle
        data.loc[data.index[engulf_start], 'Open'] = data['Close'].iloc[engulf_start-1] * 0.999
        data.loc[data.index[engulf_start], 'Close'] = data['Open'].iloc[engulf_start] * 1.003  # Strong bullish
        data.loc[data.index[engulf_start], 'Volume'] = data['Volume'].iloc[engulf_start] * 4
    
    return data

def test_1min_strategy():
    """Test strategy with 1-minute data"""
    print("\n🧪 Testing Strategy with 1-Minute Data")
    print("=" * 45)
    
    from strategies.complete_scalper import CompleteScalpingStrategy
    
    # Load 1-minute data
    spy_data = pd.read_csv('data/historical/SPY_1min.csv', index_col=0, parse_dates=True)
    
    strategy = CompleteScalpingStrategy()
    
    # Test at pattern points
    test_points = [100, 110, 300, 310, 500, 510]  # Points during patterns
    signals_found = 0
    
    for point in test_points:
        if point < len(spy_data):
            test_data = spy_data.iloc[:point]
            analysis = strategy.analyze_market(test_data)
            
            if analysis:
                print(f"\n📊 Test at {spy_data.index[point]}:")
                print(f"   Signal: {analysis['signal']}")
                print(f"   HA Trend: {analysis['ha_trend']}")
                print(f"   EMA Trend: {analysis['ema_trend']}")
                print(f"   Trend Strength: {analysis['trend_strength']:.2f}")
                print(f"   Bullish Pattern: {analysis['bullish_pattern']}")
                print(f"   Bearish Pattern: {analysis['bearish_pattern']}")
                
                if analysis['signal'] != 'HOLD':
                    signals_found += 1
                    print("   🎯 TRADE SIGNAL!")
    
    print(f"\n📈 Summary: {signals_found}/{len(test_points)} test points generated signals")
    
    if signals_found > 0:
        print("✅ SUCCESS: Strategy works with 1-minute data!")
    else:
        print("❌ Strategy still not generating signals with 1-minute data")
        print("💡 May need to adjust strategy for 1-minute timeframe")

def main():
    print("🚀 Creating 1-Minute Scalping Data")
    print("=" * 35)
    
    # Create 1-minute data
    spy_data, qqq_data = create_1min_scalping_data()
    
    # Test strategy with 1-minute data
    test_1min_strategy()
    
    print(f"\n💡 1-minute data ready for scalping!")
    print(f"📁 Files: data/historical/SPY_1min.csv")
    print(f"         data/historical/QQQ_1min.csv")

if __name__ == "__main__":
    main()