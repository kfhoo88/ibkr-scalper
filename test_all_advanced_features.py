# test_all_advanced_features.py

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add strategies to path
sys.path.append('strategies')

from advanced_scalper import AdvancedScalpingStrategy

def test_hedging_mechanism():
    """Test hedging functionality"""
    print("🧪 TESTING HEDGING MECHANISM")
    print("=" * 50)
    
    strategy = AdvancedScalpingStrategy()
    
    # Add positions to trigger hedging
    positions = [
        {'type': 'stock', 'quantity': 500, 'symbol': 'SPY'},  # High delta
        {'type': 'call', 'quantity': 100, 'delta': 0.6, 'symbol': 'SPY'},  # More delta
    ]
    
    for position in positions:
        strategy.update_portfolio_greeks(position)
    
    print(f"Portfolio Delta: {strategy.portfolio_delta}")
    print(f"Delta Limit: {strategy.delta_limit}")
    
    should_hedge, reason = strategy.should_hedge()
    print(f"Should Hedge: {should_hedge}")
    print(f"Reason: {reason}")
    
    if should_hedge:
        hedge_trade = strategy.generate_hedge_trade()
        print(f"Hedge Trade: {hedge_trade}")
    
    print("✅ Hedging test completed\n")
    return should_hedge

def test_delta_rolling():
    """Test delta rolling functionality"""
    print("🧪 TESTING DELTA ROLLING")
    print("=" * 50)
    
    strategy = AdvancedScalpingStrategy()
    
    # Test high delta position
    high_delta_position = {
        'type': 'call',
        'quantity': 50,
        'delta': 0.8,
        'dte': 10,  # Near expiration
        'symbol': 'SPY'
    }
    
    should_roll, reason = strategy.should_roll_position(high_delta_position)
    print(f"Should Roll: {should_roll}")
    print(f"Reason: {reason}")
    
    if should_roll:
        roll_instruction = strategy.generate_roll_instruction(high_delta_position)
        print(f"Roll Instruction: {roll_instruction}")
    
    # Test low delta position (should not roll)
    low_delta_position = {
        'type': 'call', 
        'quantity': 50,
        'delta': 0.2,
        'dte': 45,
        'symbol': 'SPY'
    }
    
    should_roll2, reason2 = strategy.should_roll_position(low_delta_position)
    print(f"Low Delta Should Roll: {should_roll2}")
    print(f"Reason: {reason2}")
    
    print("✅ Delta rolling test completed\n")
    return should_roll

def test_volatility_adjustment():
    """Test volatility-based position sizing"""
    print("🧪 TESTING VOLATILITY ADJUSTMENT")
    print("=" * 50)
    
    strategy = AdvancedScalpingStrategy()
    
    # Test signal in high IV environment
    test_signal = {
        'signal': 'BUY',
        'price': 450.0,
        'quantity': 100,
        'type': 'stock',
        'reason': 'Bullish trend'
    }
    
    high_iv = 0.6  # 60% IV - very high
    adjusted_signal = strategy.adjust_for_volatility(test_signal, high_iv)
    
    print(f"Original Quantity: {test_signal['quantity']}")
    print(f"Adjusted Quantity: {adjusted_signal.get('quantity', 'No adjustment')}")
    print(f"IV: {high_iv}")
    print(f"IV Threshold: {strategy.config['iv_threshold']}")
    
    # Test signal in normal IV environment
    normal_iv = 0.2  # 20% IV - normal
    normal_adjusted = strategy.adjust_for_volatility(test_signal, normal_iv)
    
    print(f"Normal IV Adjusted Quantity: {normal_adjusted.get('quantity', 'No adjustment')}")
    
    print("✅ Volatility adjustment test completed\n")
    return adjusted_signal.get('quantity', 100) != test_signal['quantity']

def test_portfolio_greeks():
    """Test portfolio Greek calculations"""
    print("🧪 TESTING PORTFOLIO GREEKS")
    print("=" * 50)
    
    strategy = AdvancedScalpingStrategy()
    
    # Create mixed portfolio
    portfolio = [
        {'type': 'stock', 'quantity': 100, 'symbol': 'SPY'},
        {'type': 'call', 'quantity': 20, 'delta': 0.6, 'vega': 0.1, 'theta': -0.05, 'symbol': 'SPY'},
        {'type': 'put', 'quantity': 10, 'delta': -0.4, 'vega': 0.08, 'theta': -0.03, 'symbol': 'SPY'},
        {'type': 'spread', 'quantity': 5, 'long_delta': 0.5, 'short_delta': 0.3, 'symbol': 'SPY'}  # Net delta 0.2
    ]
    
    for position in portfolio:
        strategy.update_portfolio_greeks(position)
    
    print(f"Portfolio Delta: {strategy.portfolio_delta:.2f}")
    print(f"Portfolio Vega: {strategy.portfolio_vega:.2f}") 
    print(f"Portfolio Theta: {strategy.portfolio_theta:.2f}")
    
    # Verify calculations
    expected_delta = (100 * 1.0) + (20 * 0.6) + (10 * -0.4) + (5 * (0.5 - 0.3))
    print(f"Expected Delta: {expected_delta:.2f}")
    print(f"Delta Match: {abs(strategy.portfolio_delta - expected_delta) < 0.01}")
    
    print("✅ Portfolio Greeks test completed\n")
    return abs(strategy.portfolio_delta - expected_delta) < 0.01

def test_integration_with_market_data():
    """Test the complete system with market data"""
    print("🧪 TESTING INTEGRATION WITH MARKET DATA")
    print("=" * 50)
    
    try:
        # Load sample data
        data = pd.read_csv('data/historical/SPY_1min_data.csv')
        
        # Handle datetime
        datetime_col = None
        for col in data.columns:
            if 'time' in col.lower() or 'date' in col.lower():
                datetime_col = col
                break
        
        if datetime_col:
            data[datetime_col] = pd.to_datetime(data[datetime_col])
            data = data.set_index(datetime_col)
        
        data = data.rename(columns=str.lower)
        
        strategy = AdvancedScalpingStrategy()
        
        # Test multiple bars to see signals
        signals_generated = 0
        for i in range(100, 150):  # Test 50 bars
            current_data = data.iloc[:i+1].copy()
            signal = strategy.generate_trade_signal(current_data, current_iv=0.3)
            
            if signal['signal'] != 'HOLD':
                signals_generated += 1
                print(f"Signal #{signals_generated}: {signal['signal']} at {signal['timestamp']}")
                if signals_generated >= 3:  # Show first 3 signals
                    break
        
        print(f"Total signals generated: {signals_generated}")
        print("✅ Integration test completed\n")
        return signals_generated > 0
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Run all advanced feature tests"""
    print("🚀 COMPREHENSIVE ADVANCED FEATURES VALIDATION")
    print("=" * 60)
    print("Testing: Hedging, Delta Rolling, Volatility Adjustment, Portfolio Greeks")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    test_results.append(test_hedging_mechanism())
    test_results.append(test_delta_rolling()) 
    test_results.append(test_volatility_adjustment())
    test_results.append(test_portfolio_greeks())
    test_results.append(test_integration_with_market_data())
    
    # Summary
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL ADVANCED FEATURES WORKING CORRECTLY!")
        print("\n✅ What's now implemented:")
        print("   - Dynamic hedging based on portfolio delta")
        print("   - Delta rolling for high-delta positions") 
        print("   - Volatility-adjusted position sizing")
        print("   - Portfolio Greek calculations")
        print("   - Integrated with market data analysis")
        print("\n🚀 Ready for comprehensive backtesting!")
    else:
        print(f"⚠️  {total - passed} tests need attention")
        print("   Review the failed tests above")

if __name__ == "__main__":
    main()