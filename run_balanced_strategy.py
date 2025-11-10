# run_balanced_strategy.py

import pandas as pd
import sys
import os

# Add strategies to path
sys.path.append('strategies')

from balanced_advanced_scalper import BalancedAdvancedScalpingStrategy
from advanced_backtester_controlled import ControlledAdvancedBacktester

def main():
    """Run the balanced advanced strategy"""
    print("🚀 RUNNING BALANCED ADVANCED STRATEGY")
    print("=" * 60)
    
    # Create balanced strategy
    strategy = BalancedAdvancedScalpingStrategy()
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
        else:
            # Create datetime index if no datetime column
            data.index = pd.date_range(start='2024-01-01 09:30:00', periods=len(data), freq='1min')
        
        data = data.rename(columns=str.lower)
        
        print(f"📊 Data loaded: {len(data)} bars, {data.index[0]} to {data.index[-1]}")
        
        # Run backtest
        report = backtester.backtest(data, 'SPY')
        
        print(f"\n📈 BALANCED STRATEGY PERFORMANCE:")
        print(f"   Total Return: {report['total_return_pct']:.2f}%")
        print(f"   Max Drawdown: {report['max_drawdown_pct']:.2f}%")
        print(f"   Sharpe Ratio: {report['sharpe_ratio']:.2f}")
        print(f"   Total Trades: {report['total_trades']}")
        print(f"   Hedge Operations: {report['hedge_operations']}")
        print(f"   Portfolio Delta: {report['portfolio_delta']}")
        
        # Show trade breakdown
        if report['total_trades'] > 0:
            print(f"\n💰 TRADE BREAKDOWN:")
            print(f"   Expected improvements:")
            print(f"   • Exit strategy: 1% stop loss, 2% take profit")
            print(f"   • Time-based exits: 30min max hold")
            print(f"   • Better signal quality")
            print(f"   • Both long and short signals")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()