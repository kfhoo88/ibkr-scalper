# quick_full_test.py
import pandas as pd
import os
import sys
from datetime import datetime

sys.path.append('core')

def quick_full_test():
    """Quick test to verify we can load and process full-year data"""
    print("🧪 QUICK FULL-YEAR DATA TEST")
    print("=" * 50)
    
    # Test SPY data
    data_dir = 'data/historical'
    spy_file = 'SPY_IBKR_1min_1year_20251110.csv'
    file_path = os.path.join(data_dir, spy_file)
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {spy_file}")
        return
    
    # Load the data
    print(f"📥 Loading {spy_file}...")
    data = pd.read_csv(file_path)
    
    print(f"✅ Loaded {len(data):,} bars")
    print(f"📅 Period: {data['date'].iloc[0]} to {data['date'].iloc[-1]}")
    
    # Calculate actual time span
    start_date = pd.to_datetime(data['date'].iloc[0])
    end_date = pd.to_datetime(data['date'].iloc[-1])
    time_span = end_date - start_date
    trading_days = time_span.days
    
    print(f"📊 Time Span: {trading_days} calendar days")
    print(f"📈 Expected trades per day: ~{len(data) / trading_days / 6.5:.1f}")  # 6.5 trading hours
    
    # Test backtester import
    try:
        from backtester_enhanced import EnhancedOptionsBacktester
        print("✅ Enhanced backtester ready for full-year test")
        
        # Ask if user wants to run quick full test
        response = input("\nRun quick full-year backtest? (y/n): ").strip().lower()
        if response == 'y':
            print("🚀 Starting quick full-year backtest...")
            backtester = EnhancedOptionsBacktester()
            
            # Use a smaller subset for quick demonstration
            test_data = data.iloc[:50000]  # First 50,000 bars
            print(f"📊 Testing with {len(test_data):,} bars...")
            
            results = backtester.backtest(test_data, "SPY")
            if results:
                print(f"✅ Quick test completed: {results['total_trades']} trades")
        
    except ImportError as e:
        print(f"❌ Backtester import failed: {e}")

if __name__ == "__main__":
    quick_full_test()