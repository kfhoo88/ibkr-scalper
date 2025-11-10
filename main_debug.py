# main_debug.py
import os
import sys
import yaml
import pandas as pd
from datetime import datetime
import traceback

def load_config():
    """Load configuration from YAML file"""
    config_path = "config/scalping_config.yaml"
    print(f"📁 Looking for config at: {config_path}")
    
    if not os.path.exists(config_path):
        print(f"❌ Config file not found: {config_path}")
        print(f"📂 Current directory: {os.getcwd()}")
        print(f"📂 Directory contents: {os.listdir('.')}")
        if os.path.exists('config'):
            print(f"📂 Config directory contents: {os.listdir('config')}")
        return None
    
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        print("✅ Configuration loaded successfully")
        return config
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        traceback.print_exc()
        return None

def check_data_files(symbols):
    """Check if data files exist"""
    for symbol in symbols:
        data_file = f"data/historical/{symbol}_IBKR_1min_1year_20251110.csv"
        print(f"📁 Checking data file: {data_file}")
        
        if not os.path.exists(data_file):
            print(f"❌ Data file not found: {data_file}")
            # Check what's actually in the data directory
            data_dir = "data/historical"
            if os.path.exists(data_dir):
                print(f"📂 Data directory contents: {os.listdir(data_dir)}")
        else:
            print(f"✅ Data file found: {data_file}")

def main():
    """Main execution function"""
    print("🎯 SPY/QQQ Scalping Backtester - DEBUG VERSION")
    print("=" * 60)
    
    # Load configuration
    config = load_config()
    if config is None:
        print("❌ Failed to load configuration")
        return
    
    print(f"📋 Config keys: {list(config.keys())}")
    
    # Check data files
    symbols = ['SPY', 'QQQ']
    check_data_files(symbols)
    
    # Try to import the backtester
    try:
        from core.backtester import ScalpingBacktester
        print("✅ Backtester imported successfully")
        
        # Initialize backtester
        backtester = ScalpingBacktester(config)
        print("✅ Backtester initialized successfully")
        
    except Exception as e:
        print(f"❌ Error importing backtester: {e}")
        traceback.print_exc()
        return
    
    # Test with one symbol first
    symbol = 'SPY'
    data_file = f"data/historical/{symbol}_IBKR_1min_1year_20251110.csv"
    
    if not os.path.exists(data_file):
        print(f"❌ Cannot proceed - data file not found: {data_file}")
        return
        
    try:
        print(f"📥 Loading data for {symbol}...")
        data = pd.read_csv(data_file, parse_dates=['date'])
        print(f"✅ Data loaded: {len(data)} rows")
        print(f"📊 Data columns: {list(data.columns)}")
        
        data.set_index('date', inplace=True)
        print(f"✅ Index set: {data.index[0]} to {data.index[-1]}")
        
        # Run backtest
        print("🚀 Starting backtest...")
        results = backtester.backtest(data, symbol)
        
        # Display results
        print(f"\n📈 {symbol} Results:")
        print(f"   Trades: {results['total_trades']}")
        print(f"   Win Rate: {results['win_rate']:.1%}")
        print(f"   Total P&L: ${results['total_pnl']:,.2f}")
        print(f"   Final Capital: ${results['final_capital']:,.2f}")
        
    except Exception as e:
        print(f"❌ Error during backtest: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()