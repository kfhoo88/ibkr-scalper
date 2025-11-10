# test_real_data.py

import pandas as pd
import sys
import os

# Add the strategies directory to path
sys.path.append('strategies')

from backtester_updated import run_backtest_test

if __name__ == "__main__":
    print("🧪 Testing Updated Strategy with Real Data")
    run_backtest_test()