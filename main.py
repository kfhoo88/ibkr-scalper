# main.py - CLEAN VERSION
import pandas as pd
import sys
import os

# Add core to path
sys.path.append('core')

def main():
    print("🚀 SPY/QQQ OPTIONS SCALPING SYSTEM")
    print("==========================================")
    print("Strategy: HA + MA + Candlestick Patterns")
    print("Trading: Calls/Puts Only | $200 Max Position")
    print("Risk: 50% Stop Loss | Rolling for Profits")
    print("Target: $20k/month Scalable System")
    print("==========================================")
    
    # Load data
    try:
        data_path = "data/historical/SPY_1min_data.csv"
        data = pd.read_csv(data_path)
        
        # Fix timestamp column
        if 'Unnamed: 0' in data.columns:
            data = data.rename(columns={'Unnamed: 0': 'timestamp'})
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        
        print(f"✅ Data loaded: {len(data)} bars")
        print(f"📅 Period: {data['timestamp'].iloc[0]} to {data['timestamp'].iloc[-1]}")
        
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        return
    
    # Run backtest using our NEW core system
    try:
        from backtester import OptionsBacktester
        
        backtester = OptionsBacktester()
        results = backtester.backtest(data, 'SPY')
        
        print("\n🎉 BACKTEST COMPLETED!")
        print("Check the results above and adjust parameters in config/scalping_config.yaml")
        
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
