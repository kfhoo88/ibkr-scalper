#!/usr/bin/env python3
"""
Debug Strategy Signals - See Why Trades Are/Are Not Triggered
"""

import pandas as pd
import logging
from strategies.complete_scalper import CompleteScalpingStrategy

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_strategy_signals():
    """Debug why signals are/aren't being generated"""
    strategy = CompleteScalpingStrategy()
    
    # Load data
    spy_data = pd.read_csv('data/historical/SPY_synthetic.csv', index_col=0, parse_dates=True)
    
    print("🔍 DEBUGGING STRATEGY SIGNALS")
    print("=" * 40)
    
    # Test on last 50 bars
    test_data = spy_data.tail(50)
    
    for i in range(20, len(test_data)):
        current_data = test_data.iloc[:i]
        analysis = strategy.analyze_market(current_data)
        
        if analysis:
            print(f"\n📊 Bar {i}: {test_data.index[i]}")
            print(f"   Signal: {analysis['signal']}")
            print(f"   HA Trend: {analysis['ha_trend']} (1=Bullish, -1=Bearish, 0=Neutral)")
            print(f"   EMA Trend: {analysis['ema_trend']} (1=Bullish, -1=Bearish, 0=Neutral)")
            print(f"   HA Doji: {analysis['ha_doji']}")
            print(f"   Bullish Pattern: {analysis['bullish_pattern']}")
            print(f"   Bearish Pattern: {analysis['bearish_pattern']}")
            print(f"   Volume Ratio: {analysis['volume_ratio']:.2f}")
            print(f"   Trend Strength: {analysis['trend_strength']:.2f}")
            
            # Check why signal is HOLD
            if analysis['signal'] == 'HOLD':
                print("   ❓ WHY HOLD:")
                conditions = []
                
                if analysis['trend_strength'] < strategy.min_trend_strength:
                    conditions.append(f"Trend strength {analysis['trend_strength']:.2f} < {strategy.min_trend_strength}")
                
                if analysis['ha_trend'] != 1 and analysis['ha_trend'] != -1:
                    conditions.append(f"HA trend neutral ({analysis['ha_trend']})")
                
                if analysis['ema_trend'] != 1 and analysis['ema_trend'] != -1:
                    conditions.append(f"EMA trend neutral ({analysis['ema_trend']})")
                
                if not analysis['bullish_pattern'] and not analysis['bearish_pattern']:
                    conditions.append("No candlestick pattern")
                
                if analysis['ha_doji']:
                    conditions.append("HA Doji detected")
                
                if not analysis['volume_ok']:
                    conditions.append(f"Volume ratio {analysis['volume_ratio']:.2f} < {strategy.volume_threshold}")
                
                for condition in conditions:
                    print(f"     - {condition}")
            
            # Stop if we find a trade signal
            if analysis['signal'] != 'HOLD':
                print("🎯 TRADE SIGNAL FOUND!")
                break

def create_better_test_data():
    """Create more realistic test data with clear trends"""
    print("\n📈 Creating Better Test Data with Clear Trends")
    print("=" * 45)
    
    import numpy as np
    from datetime import datetime, timedelta
    
    # Create clear bullish trend data
    dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='1H')
    dates = dates[dates.dayofweek < 5]  # Weekdays only
    
    # Bullish trend: steadily rising prices
    base_price = 450
    prices = []
    
    for i in range(len(dates)):
        # Steady upward trend with some noise
        trend = i * 0.1  # $0.10 per hour
        noise = np.random.normal(0, 0.5)
        price = base_price + trend + noise
        prices.append(price)
    
    # Create DataFrame with realistic OHLC
    data = pd.DataFrame(index=dates)
    data['Close'] = prices
    data['Open'] = [p - np.random.normal(0, 0.2) for p in prices]
    data['High'] = [max(o, c) + abs(np.random.normal(0, 0.3)) for o, c in zip(data['Open'], data['Close'])]
    data['Low'] = [min(o, c) - abs(np.random.normal(0, 0.3)) for o, c in zip(data['Open'], data['Close'])]
    data['Volume'] = np.random.randint(1000000, 5000000, len(dates))
    
    # Save the better test data
    data.to_csv('data/historical/SPY_trending.csv')
    print(f"✅ Created trending data: {len(data)} bars")
    print(f"   Price range: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")
    
    return data

def test_with_trending_data():
    """Test strategy with clearly trending data"""
    print("\n🧪 Testing with Trending Data")
    print("=" * 35)
    
    strategy = CompleteScalpingStrategy()
    data = pd.read_csv('data/historical/SPY_trending.csv', index_col=0, parse_dates=True)
    
    # Analyze the data
    analysis = strategy.analyze_market(data)
    
    if analysis:
        print("📊 ANALYSIS RESULTS:")
        print(f"   Signal: {analysis['signal']}")
        print(f"   HA Trend: {analysis['ha_trend']}")
        print(f"   EMA Trend: {analysis['ema_trend']}")
        print(f"   Trend Strength: {analysis['trend_strength']:.2f}")
        print(f"   Volume Ratio: {analysis['volume_ratio']:.2f}")
        
        if analysis['signal'] == 'HOLD':
            print("   ❗ Still no signal with trending data")
        else:
            print("   🎯 TRADE SIGNAL GENERATED!")
    else:
        print("❌ No analysis returned")

def main():
    print("🚀 Strategy Debugger")
    print("=" * 25)
    
    # Debug current signals
    debug_strategy_signals()
    
    # Create better test data
    create_better_test_data()
    
    # Test with trending data
    test_with_trending_data()
    
    print(f"\n💡 Next: Adjust strategy parameters if needed")

if __name__ == "__main__":
    main()