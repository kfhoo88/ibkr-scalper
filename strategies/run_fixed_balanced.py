# run_fixed_balanced.py

import pandas as pd
import sys
import os

# Add strategies to path
sys.path.append('strategies')

from balanced_advanced_scalper_fixed import BalancedAdvancedScalpingStrategyFixed
from advanced_backtester_controlled import ControlledAdvancedBacktester

def main():
    """Run the FIXED balanced advanced strategy"""
    print("🚀 RUNNING FIXED BALANCED ADVANCED STRATEGY")
    print("=" * 60)
    print("KEY FIXES:")
    print("• Integrated exit logic for ALL trades")
    print("• Tighter stops: 0.5% loss, 1.5% profit")
    print("• Shorter hold times: 20 minutes max")
    print("• Stricter entry conditions")
    print("• Better position sizing")
    print("=" * 60)
    
    # Create fixed strategy
    strategy = BalancedAdvancedScalpingStrategyFixed()
    backtester = ControlledAdvancedBacktester(strategy, initial_capital=50000)
    
    # Load data
    try:
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
        
        print(f"📊 Data loaded: {len(data)} bars")
        
        # Run backtest
        report = backtester.backtest(data, 'SPY')
        
        print(f"\n📈 FIXED STRATEGY PERFORMANCE:")
        print(f"   Total Return: {report['total_return_pct']:.2f}%")
        print(f"   Max Drawdown: {report['max_drawdown_pct']:.2f}%")
        print(f"   Total Trades: {report['total_trades']}")
        print(f"   Hedge Operations: {report['hedge_operations']}")
        print(f"   Portfolio Delta: {report['portfolio_delta']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()