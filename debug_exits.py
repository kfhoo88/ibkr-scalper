# debug_exits.py
import pandas as pd
import numpy as np
from datetime import timedelta

def debug_exit_logic():
    """Debug why stops/targets aren't hitting"""
    print("🔍 DEBUGGING EXIT LOGIC")
    print("=" * 50)
    
    # Load SPY data
    data_file = "data/historical/SPY_IBKR_1min_1year_20251110.csv"
    data = pd.read_csv(data_file)
    data['date'] = pd.to_datetime(data['date'], utc=True)
    data.set_index('date', inplace=True)
    data.index = data.index.tz_localize(None)
    
    print(f"📊 Loaded {len(data):,} bars")
    
    # Test a specific trade scenario
    test_price = data['close'].iloc[1000]  # Random entry point
    print(f"💰 Testing with entry price: ${test_price:.2f}")
    
    # Calculate stop and target prices
    stop_loss_pct = 0.003  # 0.3%
    take_profit_pct = 0.005  # 0.5%
    
    stop_price_long = test_price * (1 - stop_loss_pct)
    target_price_long = test_price * (1 + take_profit_pct)
    
    print(f"📉 LONG: Stop at ${stop_price_long:.2f} (-0.3%)")
    print(f"📈 LONG: Target at ${target_price_long:.2f} (+0.5%)")
    print(f"📊 Price range needed: ${stop_price_long:.2f} to ${target_price_long:.2f}")
    
    # Check what typical 20-minute moves look like
    data['price_change_20min'] = data['close'].pct_change(20).abs() * 100
    typical_move = data['price_change_20min'].mean()
    max_move = data['price_change_20min'].max()
    
    print(f"\n📈 Historical 20-minute moves:")
    print(f"   Average move: {typical_move:.2f}%")
    print(f"   Maximum move: {max_move:.2f}%")
    
    # Check if our stops/targets are realistic
    moves_above_stop = (data['price_change_20min'] >= 0.3).sum()
    moves_above_target = (data['price_change_20min'] >= 0.5).sum()
    
    print(f"   Moves ≥ 0.3% (stop): {moves_above_stop:,} ({moves_above_stop/len(data)*100:.1f}%)")
    print(f"   Moves ≥ 0.5% (target): {moves_above_target:,} ({moves_above_target/len(data)*100:.1f}%)")
    
    # Test actual price behavior in 20-minute windows
    print(f"\n🔍 Testing actual 20-minute windows:")
    for i in range(5):  # Test 5 random windows
        idx = np.random.randint(0, len(data) - 20)
        window = data.iloc[idx:idx+21]  # 20 minutes after entry
        entry_price = window['close'].iloc[0]
        min_price = window['close'].min()
        max_price = window['close'].max()
        actual_move_pct = (max_price - min_price) / entry_price * 100
        
        stop_hit = min_price <= entry_price * (1 - 0.003)
        target_hit = max_price >= entry_price * (1 + 0.005)
        
        print(f"   Window {i+1}: Move {actual_move_pct:.2f}% | Stop: {stop_hit} | Target: {target_hit}")

if __name__ == "__main__":
    debug_exit_logic()