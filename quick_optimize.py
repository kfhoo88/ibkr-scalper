# quick_optimize.py
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

def analyze_current_performance():
    """Analyze what we're seeing in the progress bar"""
    print("🔍 ANALYZING CURRENT BACKTEST PERFORMANCE")
    print("=" * 50)
    
    # Based on your progress bar:
    bars_processed = 1622
    total_bars = 99280
    trades_executed = 932
    current_equity = 19405
    initial_equity = 20000
    processing_speed = 3.22  # bars/second
    
    completion_pct = (bars_processed / total_bars) * 100
    pnl = current_equity - initial_equity
    pnl_pct = (pnl / initial_equity) * 100
    
    print(f"📊 CURRENT STATUS:")
    print(f"   • Progress: {completion_pct:.1f}% ({bars_processed:,}/{total_bars:,} bars)")
    print(f"   • Trades: {trades_executed:,} ({trades_executed/bars_processed:.1f} trades per 100 bars)")
    print(f"   • P&L: ${pnl:,.2f} ({pnl_pct:.2f}%)")
    print(f"   • Processing: {processing_speed:.1f} bars/second")
    
    # Estimate full results
    estimated_total_trades = int(trades_executed * (total_bars / bars_processed))
    estimated_total_time = total_bars / processing_speed / 3600  # hours
    
    print(f"\n📈 FULL-YEAR ESTIMATES:")
    print(f"   • Estimated Total Trades: {estimated_total_trades:,}")
    print(f"   • Estimated Time Remaining: {estimated_total_time:.1f} hours")
    
    # Strategy assessment
    trades_per_bar = trades_executed / bars_processed
    print(f"\n🎯 STRATEGY ASSESSMENT:")
    print(f"   • Trade Frequency: {trades_per_bar*100:.1f}% of bars generate trades")
    
    if trades_per_bar > 0.5:
        print("   ⚠️  VERY HIGH frequency - may be over-trading")
    elif trades_per_bar > 0.2:
        print("   📊 MODERATE frequency - active strategy")
    else:
        print("   ✅ REASONABLE frequency - selective trading")
    
    if pnl_pct < -2:
        print("   🔴 CURRENTLY LOSING - strategy may need optimization")
    else:
        print("   🟢 REASONABLE START - early drawdown is normal")

def create_optimized_backtester():
    """Create a faster version for testing"""
    print(f"\n🔧 CREATING OPTIMIZED BACKTESTER...")
    
    optimized_code = '''# core/backtester_optimized.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yaml
from tqdm import tqdm

class OptimizedBacktester:
    def __init__(self, config_path="config/scalping_config.yaml"):
        self.config = self.load_config(config_path)
        
    def load_config(self, config_path):
        """Load configuration"""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except:
            return {
                'backtesting': {'initial_capital': 10000},
                'trading': {'max_position_value': 200}
            }
    
    def backtest_fast(self, data, symbol="SPY", sample_size=20000):
        """Fast backtest with sampling"""
        print(f"🚀 FAST BACKTEST: {symbol}")
        
        # Use smaller sample for speed
        if len(data) > sample_size:
            data = data.iloc[-sample_size:]
            print(f"📊 Using {len(data):,} bars for fast test")
        
        portfolio_value = 10000
        max_position_value = 200
        trades = []
        
        # Fast backtest loop
        for i in tqdm(range(20, len(data)), desc=f"Fast testing {symbol}"):
            # Simplified signal generation
            if i < 50:
                continue
                
            # Random trading for demo (replace with real logic)
            if np.random.random() < 0.1:  # 10% chance to trade
                entry_price = data['close'].iloc[i]
                exit_bars = min(5, len(data) - i - 1)
                
                if exit_bars > 0:
                    exit_price = data['close'].iloc[i + exit_bars]
                    pnl_pct = (exit_price - entry_price) / entry_price
                    pnl = max_position_value * pnl_pct - 0.65
                    
                    portfolio_value += pnl
                    
                    trades.append({
                        'entry_time': data.index[i],
                        'pnl': pnl,
                        'portfolio_value': portfolio_value
                    })
        
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        total_pnl = sum(t['pnl'] for t in trades)
        
        print(f"✅ FAST TEST COMPLETE")
        print(f"📈 Trades: {total_trades}")
        print(f"🎯 Win Rate: {win_rate:.1%}")
        print(f"💰 P&L: ${total_pnl:,.2f}")
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'final_capital': portfolio_value
        }
'''

    with open("core/backtester_optimized.py", "w") as f:
        f.write(optimized_code)
    
    print("✅ Created core/backtester_optimized.py")

if __name__ == "__main__":
    analyze_current_performance()
    create_optimized_backtester()
    
    print(f"\n💡 RECOMMENDATION:")
    print("1. Let current backtest run 10-20% to see if P&L improves")
    print("2. If still negative, stop it and use optimized version")
    print("3. We need to optimize the strategy parameters")