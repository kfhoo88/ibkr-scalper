# test_backtester.py
import pandas as pd
import numpy as np
import os
import sys

sys.path.append('core')

try:
    from backtester import OptionsBacktester
    print("✅ Successfully imported OptionsBacktester")
    
    # Test initialization
    print("🧪 Testing OptionsBacktester initialization...")
    backtester = OptionsBacktester()
    print("✅ OptionsBacktester initialized successfully")
    
    # Test with sample data
    print("🧪 Testing with sample data...")
    
    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=1000, freq='1min')
    sample_data = pd.DataFrame({
        'open': np.random.normal(100, 1, 1000),
        'high': np.random.normal(101, 1, 1000),
        'low': np.random.normal(99, 1, 1000),
        'close': np.random.normal(100, 1, 1000),
        'volume': np.random.randint(1000, 10000, 1000)
    }, index=dates)
    
    print(f"📊 Sample data shape: {sample_data.shape}")
    
    # Test backtest method
    try:
        results = backtester.backtest(sample_data, symbol="TEST")
        print("✅ backtest() method executed successfully")
        print(f"📋 Results type: {type(results)}")
    except Exception as e:
        print(f"❌ backtest() method failed: {e}")
    
except Exception as e:
    print(f"❌ Error: {e}")