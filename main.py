# main.py
import os
import sys
import yaml
import pandas as pd
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from YAML file"""
    config_path = "config/scalping_config.yaml"
    if not os.path.exists(config_path):
        logger.error(f"❌ Config file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    logger.info("✅ Configuration loaded successfully")
    return config

def main():
    """Main execution function"""
    print("🎯 SPY/QQQ Scalping Backtester")
    print("=" * 50)
    
    # Load configuration
    config = load_config()
    
    # Import and initialize backtester
    try:
        from core.options_scalper import OptionsScalpingBacktester
        backtester = OptionsScalpingBacktester(config)
        logger.info("✅ OPTIONS Backtester initialized")
        logger.info("💰 Trading: 30% stops / 20% targets on OPTIONS PREMIUM")
        logger.info("⚡ Simulating 8x leverage for ATM options")
    except ImportError as e:
        logger.error(f"❌ Failed to import backtester: {e}")
        sys.exit(1)
    
    # Run backtest for each symbol
    symbols = ['SPY', 'QQQ']
    all_results = {}
    
    for symbol in symbols:
        print(f"\n📊 Processing {symbol}...")
        print("-" * 40)
        
        # Load data
        data_file = f"data/historical/{symbol}_IBKR_1min_1year_20251110.csv"
        if not os.path.exists(data_file):
            print(f"❌ Data file not found: {data_file}")
            continue
            
        try:
            # Load with proper datetime handling
            data = pd.read_csv(data_file)
            print(f"✅ Loaded {len(data):,} rows for {symbol}")
            print(f"📊 Columns: {list(data.columns)}")
            
            # Find date column
            date_col = None
            for col in data.columns:
                if 'date' in col.lower():
                    date_col = col
                    break
            if date_col is None:
                date_col = data.columns[0]  # Use first column as fallback
                
            print(f"📅 Using date column: '{date_col}'")
            
            # Convert to datetime and set index
            data[date_col] = pd.to_datetime(data[date_col], utc=True)
            data.set_index(date_col, inplace=True)
            data.index = data.index.tz_localize(None)  # Remove timezone
            
            print(f"📅 Period: {data.index[0]} to {data.index[-1]}")
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            import traceback
            traceback.print_exc()
            continue
        
        # Run backtest
        print("🚀 Running backtest...")
        try:
            results = backtester.backtest(data, symbol)
            all_results[symbol] = results
            
            # Display results
            print(f"\n📈 {symbol} Results:")
            print(f"   Trades: {results['total_trades']:,}")
            print(f"   Win Rate: {results['win_rate']:.1%}")
            print(f"   Total P&L: ${results['total_pnl']:,.2f}")
            print(f"   Final Capital: ${results['final_capital']:,.2f}")
            print(f"   Stops: {results['stops']} | Targets: {results['targets']} | Time Exits: {results['time_exits']}")
            print(f"   Avg Hold: {results['avg_hold_minutes']:.1f} minutes")
            
        except Exception as e:
            print(f"❌ Error during backtest: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    if all_results:
        print(f"\n{'='*50}")
        print("🎉 BACKTESTING COMPLETE!")
        print(f"{'='*50}")
        
        total_pnl = sum(r['total_pnl'] for r in all_results.values())
        total_trades = sum(r['total_trades'] for r in all_results.values())
        avg_win_rate = sum(r['win_rate'] for r in all_results.values()) / len(all_results)
        
        print(f"📊 COMBINED RESULTS:")
        print(f"   Total Trades: {total_trades:,}")
        print(f"   Average Win Rate: {avg_win_rate:.1%}")
        print(f"   Total P&L: ${total_pnl:,.2f}")
        
        monthly_avg = total_pnl / 12
        print(f"   Monthly Average: ${monthly_avg:,.2f}")
        print(f"   $20k Target: {(monthly_avg/20000)*100:.1f}%")

if __name__ == "__main__":
    main()