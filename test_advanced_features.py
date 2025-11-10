# test_advanced_features.py

import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime, timedelta

# Add the package directories to path
sys.path.extend(['strategies', 'risk', 'execution', 'analysis'])

def test_hedging_mechanisms():
    """Test if hedging features are working"""
    print("🧪 TESTING HEDGING MECHANISMS")
    print("=" * 50)
    
    try:
        # Try to import hedging modules
        from risk.hedge_manager import HedgeManager
        from strategies.options_scalper import OptionsScalpingStrategy
        
        print("✅ HedgeManager imported successfully")
        
        # Test hedge manager initialization
        hedge_mgr = HedgeManager(max_delta=1000, max_vega=500)
        print("✅ HedgeManager initialized")
        
        # Test delta calculation
        test_position = {'type': 'CALL', 'strike': 450, 'quantity': 10, 'delta': 0.6}
        portfolio_delta = hedge_mgr.calculate_portfolio_delta([test_position])
        print(f"✅ Portfolio delta calculation: {portfolio_delta}")
        
        # Test hedging logic
        hedge_trade = hedge_mgr.get_hedge_trade(portfolio_delta)
        if hedge_trade:
            print(f"✅ Hedge trade generated: {hedge_trade}")
        else:
            print("✅ No hedge needed (within limits)")
            
        return True
        
    except ImportError as e:
        print(f"❌ Hedging modules not found: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing hedging: {e}")
        return False

def test_delta_rolling():
    """Test delta rolling mechanisms"""
    print("\n🧪 TESTING DELTA ROLLING")
    print("=" * 50)
    
    try:
        from risk.position_manager import PositionManager
        from strategies.volatility_strategy import VolatilityStrategy
        
        print("✅ PositionManager imported successfully")
        
        # Test position manager
        pos_mgr = PositionManager(delta_threshold=0.7, roll_target=0.3)
        print("✅ PositionManager initialized")
        
        # Test rolling logic
        high_delta_position = {
            'symbol': 'SPY',
            'option_type': 'CALL', 
            'strike': 450,
            'delta': 0.75,
            'dte': 5,
            'quantity': 10
        }
        
        should_roll = pos_mgr.should_roll_position(high_delta_position)
        print(f"✅ Roll decision for high delta position: {should_roll}")
        
        if should_roll:
            roll_instruction = pos_mgr.generate_roll_instruction(high_delta_position)
            print(f"✅ Roll instruction: {roll_instruction}")
            
        return True
        
    except ImportError as e:
        print(f"❌ Delta rolling modules not found: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing delta rolling: {e}")
        return False

def test_options_aware_backtest():
    """Test if options-aware backtesting works"""
    print("\n🧪 TESTING OPTIONS-AWARE BACKTESTING")
    print("=" * 50)
    
    try:
        from backtesting.options_backtester import OptionsBacktester
        from data.options_data_manager import OptionsDataManager
        
        print("✅ OptionsBacktester imported successfully")
        
        # Test initialization
        backtester = OptionsBacktester(initial_capital=50000, use_hedging=True)
        print("✅ OptionsBacktester initialized with hedging")
        
        # Test data manager
        data_mgr = OptionsDataManager()
        print("✅ OptionsDataManager initialized")
        
        return True
        
    except ImportError as e:
        print(f"❌ Options backtesting modules not found: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing options backtesting: {e}")
        return False

def test_comprehensive_strategy():
    """Test the comprehensive strategy with all features"""
    print("\n🧪 TESTING COMPREHENSIVE STRATEGY")
    print("=" * 50)
    
    try:
        # Try to import the main strategy that should include all features
        from strategies.comprehensive_scalper import ComprehensiveScalpingStrategy
        
        print("✅ ComprehensiveScalpingStrategy imported successfully")
        
        # Initialize strategy with all features enabled
        strategy = ComprehensiveScalpingStrategy(
            use_hedging=True,
            use_delta_rolling=True, 
            use_volatility_adjustment=True,
            max_delta_exposure=1000,
            max_portfolio_risk=0.02
        )
        print("✅ Comprehensive strategy initialized with all features")
        
        # Test strategy configuration
        print(f"✅ Hedging enabled: {strategy.use_hedging}")
        print(f"✅ Delta rolling enabled: {strategy.use_delta_rolling}")
        print(f"✅ Max delta: {strategy.max_delta_exposure}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Comprehensive strategy not found: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing comprehensive strategy: {e}")
        return False

def test_with_sample_data():
    """Test with sample options data if available"""
    print("\n🧪 TESTING WITH SAMPLE DATA")
    print("=" * 50)
    
    try:
        # Check for options data files
        options_data_files = [
            'data/options/SPY_options_chain.csv',
            'data/options/QQQ_options_chain.csv', 
            'data/historical/options_data.csv'
        ]
        
        found_files = []
        for filepath in options_data_files:
            if os.path.exists(filepath):
                found_files.append(filepath)
                print(f"✅ Found options data: {filepath}")
        
        if found_files:
            # Try to load options data
            for filepath in found_files:
                try:
                    data = pd.read_csv(filepath)
                    print(f"✅ Loaded options data: {data.shape[0]} rows, {data.shape[1]} columns")
                    print(f"   Columns: {list(data.columns)}")
                    break
                except Exception as e:
                    print(f"❌ Error loading {filepath}: {e}")
        else:
            print("❌ No options data files found")
            print("💡 Create sample options data for testing")
            
    except Exception as e:
        print(f"❌ Error in data test: {e}")

def main():
    """Run all advanced feature tests"""
    print("🚀 COMPREHENSIVE ADVANCED FEATURES TEST")
    print("=" * 60)
    print("Testing: Hedging, Delta Rolling, Options Awareness")
    print("=" * 60)
    
    # Run all tests
    tests = [
        test_hedging_mechanisms,
        test_delta_rolling, 
        test_options_aware_backtest,
        test_comprehensive_strategy,
        test_with_sample_data
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL ADVANCED FEATURES WORKING!")
        print("\nNext steps:")
        print("1. Run comprehensive options backtest")
        print("2. Test hedging in live market conditions") 
        print("3. Validate delta rolling performance")
    else:
        print("⚠️  Some advanced features missing or not working")
        print("\nRecommended actions:")
        print("1. Check if all package files are present")
        print("2. Verify imports in strategy modules")
        print("3. Create sample options data for testing")
        print("4. Review the original package structure")

if __name__ == "__main__":
    main()