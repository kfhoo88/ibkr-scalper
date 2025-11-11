# vwap_ma_strategy/main_clean.py
import sys
import os

# Add the current directory to path
sys.path.append(os.path.dirname(__file__))

from backtester.engine import VWAPMABacktester

def main():
    print("VWAP + MA Scalping Strategy Backtest")
    print("=====================================")
    
    # Initialize backtester
    backtester = VWAPMABacktester("config/vwap_ma_config.yaml")
    
    # Run backtests for all symbols
    results = backtester.run_all_backtests()
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY RESULTS")
    print(f"{'='*60}")
    
    total_pnl = 0
    for symbol, result in results.items():
        if result and 'error' not in result:
            total_pnl += result['total_pnl']
            print(f"{symbol}: ${result['total_pnl']:.2f} ({result['win_rate']:.1f}% win rate)")
    
    print(f"\nTotal Portfolio P&L: ${total_pnl:.2f}")

if __name__ == "__main__":
    main()