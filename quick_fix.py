# quick_fix.py
import pandas as pd
import numpy as np
from datetime import timedelta

def test_realistic_scalping():
    """Test with realistic scalping parameters"""
    print("🎯 TESTING REALISTIC SCALPING PARAMETERS")
    print("=" * 50)
    
    # Load SPY data
    data_file = "data/historical/SPY_IBKR_1min_1year_20251110.csv"
    data = pd.read_csv(data_file)
    data['date'] = pd.to_datetime(data['date'], utc=True)
    data.set_index('date', inplace=True)
    data.index = data.index.tz_localize(None)
    
    print(f"📊 Loaded {len(data):,} bars")
    print(f"💰 Typical price: ${data['close'].mean():.2f}")
    
    # Realistic scalping moves for 20 minutes
    typical_20min_move = data['close'].pct_change(20).abs().mean() * 100
    print(f"📈 Typical 20-min move: {typical_20min_move:.2f}%")
    
    # Test what 0.3% stop and 0.5% target mean in dollars
    avg_price = data['close'].mean()
    stop_dollars = avg_price * 0.003
    target_dollars = avg_price * 0.005
    
    print(f"💰 Realistic stops/targets for ${avg_price:.2f} SPY:")
    print(f"   Stop loss (0.3%): ${stop_dollars:.2f}")
    print(f"   Take profit (0.5%): ${target_dollars:.2f}")
    
    # Check how often these moves happen in 20 minutes
    data['price_change_20min'] = data['close'].pct_change(20).abs() * 100
    stops_hit = (data['price_change_20min'] >= 0.3).sum()
    targets_hit = (data['price_change_20min'] >= 0.5).sum()
    
    print(f"📊 Historical 20-min moves:")
    print(f"   Moves ≥ 0.3% (stop): {stops_hit:,} times ({stops_hit/len(data)*100:.1f}%)")
    print(f"   Moves ≥ 0.5% (target): {targets_hit:,} times ({targets_hit/len(data)*100:.1f}%)")

if __name__ == "__main__":
    test_realistic_scalping()