# test_optimized.py
import pandas as pd
import numpy as np
import os
import sys

sys.path.append('core')

try:
    from backtester_fast import FastBacktester, test_fast_backtester
    print("SUCCESS: Imported optimized backtester")
    
    # Test with your real data
    def test_with_real_data():
        print("\nTESTING WITH REAL DATA...")
        
        # Load SPY data
        data_dir = 'data/historical'
        spy_files = [f for f in os.listdir(data_dir) if f.startswith('SPY') and '1min' in f]
        
        if spy_files:
            file_path = os.path.join(data_dir, spy_files[0])
            print(f"Loading: {spy_files[0]}")
            
            data = pd.read_csv(file_path)
            date_col = 'date' if 'date' in data.columns else ('Date' if 'Date' in data.columns else 'Datetime')
            data[date_col] = pd.to_datetime(data[date_col], utc=True)
            data.set_index(date_col, inplace=True)
            
            # Use smaller sample for quick test
            test_data = data.iloc[-20000:]  # Last 20,000 bars
            
            backtester = FastBacktester("config/scalping_config_optimized.yaml")
            results = backtester.backtest_fast(test_data, "SPY")
            
            return results
        else:
            print("No SPY data found")
            return None
    
    # Run tests
    print("1. Testing with sample data...")
    test_fast_backtester()
    
    print("\n2. Testing with real data...")
    real_results = test_with_real_data()
    
except ImportError as e:
    print(f"ERROR: {e}")
    print("Make sure core/backtester_fast.py was created")