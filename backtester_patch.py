# backtester_patch.py
import sys
sys.path.append('core')

# Monkey patch the backtester to fix the timestamp issue
from backtester import OptionsBacktester

original_backtest = OptionsBacktester.backtest

def fixed_backtest(self, data, symbol='SPY'):
    """Fixed backtest method that uses index instead of timestamp column"""
    # Ensure data has proper index
    if 'date' in data.columns and not isinstance(data.index, pd.DatetimeIndex):
        data = data.set_index('date')
    
    # Use index for timestamp display
    print(f"📊 Data: {len(data)} bars | Period: {data.index[0]} to {data.index[-1]}")
    
    # Call original method but with fixed data
    return original_backtest(self, data, symbol)

# Apply the patch
OptionsBacktester.backtest = fixed_backtest

print("✅ Applied timestamp fix patch")
