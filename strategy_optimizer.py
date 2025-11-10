#!/usr/bin/env python3
"""
Optimize Strategy Parameters for Better Signal Generation
"""

import pandas as pd
from strategies.complete_scalper import CompleteScalpingStrategy

def optimize_parameters():
    """Test different parameter combinations"""
    print("🎯 Strategy Parameter Optimization")
    print("=" * 40)
    
    # Load data
    data = pd.read_csv('data/historical/SPY_trending.csv', index_col=0, parse_dates=True)
    
    # Test different parameter combinations
    parameter_sets = [
        {'ha_lookback': 2, 'min_trend_strength': 0.5, 'volume_threshold': 1.1},
        {'ha_lookback': 3, 'min_trend_strength': 0.4, 'volume_threshold': 1.0},
        {'ha_lookback': 4, 'min_trend_strength': 0.6, 'volume_threshold': 1.2},
        {'ha_lookback': 2, 'min_trend_strength': 0.3, 'volume_threshold': 0.9},
    ]
    
    best_signal = None
    best_params = None
    
    for params in parameter_sets:
        print(f"\n🧪 Testing parameters: {params}")
        
        strategy = CompleteScalpingStrategy()
        # Update strategy parameters
        for key, value in params.items():
            setattr(strategy, key, value)
        
        analysis = strategy.analyze_market(data)
        
        if analysis:
            print(f"   Signal: {analysis['signal']}")
            print(f"   Trend Strength: {analysis['trend_strength']:.2f}")
            
            if analysis['signal'] != 'HOLD':
                best_signal = analysis['signal']
                best_params = params
                print("   🎯 FOUND WORKING PARAMETERS!")
                break
        else:
            print("   ❌ No analysis returned")
    
    if best_params:
        print(f"\n✅ OPTIMAL PARAMETERS FOUND:")
        print(f"   {best_params}")
        print(f"   Signal: {best_signal}")
        
        # Save optimal parameters
        with open('config/optimal_params.py', 'w') as f:
            f.write(f"OPTIMAL_PARAMS = {best_params}\n")
        print("   💾 Saved to config/optimal_params.py")
    else:
        print("\n❌ No working parameters found with current data")
        print("💡 The strategy might be too strict, or data might not have clear patterns")

def create_more_realistic_data():
    """Create data with clear bullish/bearish patterns"""
    print("\n📊 Creating Pattern-Rich Test Data")
    print("=" * 40)
    
    import numpy as np
    from datetime import datetime, timedelta
    
    # Create dates
    dates = pd.date_range(start='2024-01-01 09:30', end='2024-01-01 16:00', freq='1H')
    
    # Scenario 1: Clear bullish trend with engulfing pattern
    bullish_data = pd.DataFrame(index=dates)
    
    # Create a clear bullish move
    prices = [450.0]
    for i in range(1, len(dates)):
        # Strong bullish trend
        change = np.random.normal(0.1, 0.05)  # Positive bias
        prices.append(prices[-1] * (1 + change/100))
    
    bullish_data['Close'] = prices
    bullish_data['Open'] = [p * (1 - np.random.normal(0.02, 0.01)) for p in prices]  # Often opens lower
    bullish_data['High'] = [c * (1 + abs(np.random.normal(0.03, 0.01))) for c in prices]
    bullish_data['Low'] = [o * (1 - abs(np.random.normal(0.01, 0.005))) for o in bullish_data['Open']]
    bullish_data['Volume'] = np.random.randint(2000000, 6000000, len(dates))
    
    # Add a clear bullish engulfing pattern at the end
    bullish_data.loc[bullish_data.index[-1], 'Open'] = bullish_data['Close'].iloc[-2] * 0.99
    bullish_data.loc[bullish_data.index[-1], 'Close'] = bullish_data['Open'].iloc[-1] * 1.03
    
    bullish_data.to_csv('data/historical/SPY_bullish.csv')
    print(f"✅ Created bullish pattern data: {len(bullish_data)} bars")
    
    return bullish_data

def test_pattern_data():
    """Test strategy with pattern-rich data"""
    print("\n🧪 Testing with Pattern-Rich Data")
    print("=" * 35)
    
    strategy = CompleteScalpingStrategy()
    
    # Test bullish data
    bullish_data = pd.read_csv('data/historical/SPY_bullish.csv', index_col=0, parse_dates=True)
    analysis = strategy.analyze_market(bullish_data)
    
    if analysis:
        print("📊 BULLISH PATTERN TEST:")
        print(f"   Signal: {analysis['signal']}")
        print(f"   HA Trend: {analysis['ha_trend']}")
        print(f"   EMA Trend: {analysis['ema_trend']}")
        print(f"   Bullish Pattern: {analysis['bullish_pattern']}")
        print(f"   Trend Strength: {analysis['trend_strength']:.2f}")
        
        if analysis['signal'] == 'BUY_CALL':
            print("   🎯 SUCCESS: Correctly identified bullish pattern!")
        else:
            print("   ❗ Missed bullish pattern")

def main():
    print("🚀 Strategy Parameter Optimizer")
    print("=" * 35)
    
    # Optimize parameters
    optimize_parameters()
    
    # Create pattern-rich data
    create_more_realistic_data()
    
    # Test with pattern data
    test_pattern_data()

if __name__ == "__main__":
    main()