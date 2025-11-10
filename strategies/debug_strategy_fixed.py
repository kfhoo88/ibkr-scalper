#!/usr/bin/env python3
"""
Fixed Strategy Debugger
"""

import pandas as pd
import logging
from strategies.debug_scalper import DebugScalpingStrategy

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("🚀 Fixed Strategy Condition Debugger")
    print("=" * 45)
    
    # Test with our signal data
    test_files = [
        ('SPY Bullish Signal', 'data/historical/SPY_bullish_signal.csv'),
        ('SPY Bearish Signal', 'data/historical/SPY_bearish_signal.csv'),
        ('QQQ Bullish Signal', 'data/historical/QQQ_bullish_signal.csv'),
    ]
    
    strategy = DebugScalpingStrategy()
    
    for test_name, filepath in test_files:
        print(f"\n" + "="*60)
        print(f"🔍 DEBUGGING: {test_name}")
        print(f"📁 File: {filepath}")
        print("="*60)
        
        try:
            data = pd.read_csv(filepath, index_col=0, parse_dates=True)
            
            # Test multiple points to find where signals trigger
            test_points = [100, 110, 120, 130, 140]
            
            for point in test_points:
                if point < len(data):
                    print(f"\n" + "-"*40)
                    print(f"🧪 Testing at bar {point}: {data.index[point]}")
                    print("-"*40)
                    
                    test_data = data.iloc[:point]
                    analysis = strategy.analyze_market(test_data)
                    
                    if analysis and analysis['signal'] != 'HOLD':
                        print(f"\n🎉 SIGNAL FOUND AT BAR {point}!")
                        print(f"🎯 Signal: {analysis['signal']}")
                        break
                    elif analysis:
                        print(f"📊 Result: {analysis['signal']}")
                    else:
                        print("❌ No analysis returned")
                        
        except Exception as e:
            print(f"❌ Error testing {test_name}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n" + "="*60)
    print("🎯 DEBUGGING COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()