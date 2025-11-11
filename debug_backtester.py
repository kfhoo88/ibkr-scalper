# debug_backtester.py
import pandas as pd
import numpy as np
import os
import sys

sys.path.append('core')

try:
    from backtester import OptionsBacktester
    print("✅ Successfully imported OptionsBacktester")
    
    # Let's examine what the backtester expects
    print("🔍 Examining OptionsBacktester structure...")
    
    # Check the backtest method signature
    import inspect
    sig = inspect.signature(OptionsBacktester.backtest)
    print(f"📋 backtest method signature: {sig}")
    
    # Load a small sample of real data to see the structure
    data_dir = 'data/historical'
    spy_files = [f for f in os.listdir(data_dir) if f.startswith('SPY') and '1min' in f]
    
    if spy_files:
        file_path = os.path.join(data_dir, spy_files[0])
        print(f"\n📊 Loading real data from: {spy_files[0]}")
        real_data = pd.read_csv(file_path, nrows=5)  # Just first 5 rows
        print("Real data columns:", list(real_data.columns))
        print("Real data sample:")
        print(real_data)
        
        # Check if timestamp column exists
        if 'timestamp' not in real_data.columns:
            print("❌ 'timestamp' column missing from real data")
            print("💡 We need to create it from the date column")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()