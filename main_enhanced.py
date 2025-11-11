# main_enhanced.py
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import sys

# Add core to path
sys.path.append('core')

try:
    from backtester import Backtester
    from options_scalper import OptionsScalper
    print("✅ Successfully imported core modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class EnhancedBacktester:
    def __init__(self):
        self.data_dir = 'data/historical'
        self.results_dir = 'results'
        os.makedirs(self.results_dir, exist_ok=True)
        
    def load_1year_1min_data(self, symbol):
        """
        Load the actual 1-year 1-minute data we downloaded from IBKR
        """
        print(f"📥 LOADING 1-YEAR 1-MIN DATA FOR {symbol}...")
        
        # Look for our IBKR 1-minute data files
        files = [f for f in os.listdir(self.data_dir) 
                if f.startswith(symbol) and '1min_1year' in f and 'IBKR' in f]
        
        if not files:
            print(f"❌ No 1-year 1-min IBKR data found for {symbol}")
            print(f"   Available files: {[f for f in os.listdir(self.data_dir) if symbol in f]}")
            return None
        
        # Use the most recent file
        latest_file = sorted(files)[-1]
        file_path = os.path.join(self.data_dir, latest_file)
        
        print(f"   Loading: {latest_file}")
        
        try:
            data = pd.read_csv(file_path)
            data['date'] = pd.to_datetime(data['date'])
            
            # Standardize column names
            column_map = {
                'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume',
                'OPEN': 'open', 'HIGH': 'high', 'LOW': 'low', 'CLOSE': 'close', 'VOLUME': 'volume'
            }
            
            for old_col, new_col in column_map.items():
                if old_col in data.columns:
                    data.rename(columns={old_col: new_col}, inplace=True)
            
            # Ensure we have required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                print(f"❌ Missing columns: {missing_cols}")
                return None
            
            data.set_index('date', inplace=True)
            data.sort_index(inplace=True)
            
            print(f"   ✅ Successfully loaded {len(data):,} bars")
            print(f"   📅 Period: {data.index.min()} to {data.index.max()}")
            print(f"   📊 Data points per day: ~{len(data) / 252:.0f}")  # Approximate trading days
            
            return data
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return None
    
    def run_comprehensive_backtest(self, symbol, use_full_data=True):
        """
        Run comprehensive backtest using real 1-year 1-minute data
        """
        print(f"\n🎯 COMPREHENSIVE BACKTEST: {symbol}")
        print("=" * 60)
        
        # Load the real data
        data = self.load_1year_1min_data(symbol)
        if data is None:
            print(f"❌ Could not load data for {symbol}")
            return None
        
        # Use subset for quick testing if desired
        if not use_full_data:
            data = data.iloc[-10000:]  # Last 10,000 bars for quick test
            print(f"   🚀 Using {len(data):,} bars for quick backtest")
        else:
            print(f"   🚀 Using FULL {len(data):,} bars for comprehensive backtest")
        
        # Initialize strategy
        strategy = OptionsScalper()
        
        # Initialize backtester with realistic parameters
        backtester = Backtester(
            strategy=strategy,
            initial_capital=10000,  # $10k starting capital
            commission=0.65,        # IBKR options commission
            position_size=200       # Our $200 position limit
        )
        
        print(f"   ⚙️  Backtest Parameters:")
        print(f"      • Initial Capital: ${backtester.initial_capital:,.2f}")
        print(f"      • Position Size: ${backtester.position_size:,.2f}")
        print(f"      • Commission: ${backtester.commission:.2f} per trade")
        
        # Run the backtest
        print(f"\n   🔄 RUNNING BACKTEST...")
        start_time = datetime.now()
        
        results = backtester.run(data)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"   ✅ BACKTEST COMPLETED IN {duration:.1f} SECONDS")
        
        return results
    
    def analyze_and_display_results(self, results, symbol):
        """
        Analyze and display comprehensive results
        """
        if not results or 'trades' not in results:
            print(f"❌ No results to analyze for {symbol}")
            return
        
        trades = results.get('trades', [])
        
        print(f"\n📊 PERFORMANCE ANALYSIS: {symbol}")
        print("=" * 50)
        
        # Basic metrics
        total_trades = len(trades)
        if total_trades == 0:
            print("   No trades executed")
            return
        
        winning_trades = len([t for t in trades if t.get('pnl', 0) > 0])
        losing_trades = len([t for t in trades if t.get('pnl', 0) < 0])
        win_rate = winning_trades / total_trades
        
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        avg_win = np.mean([t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0]) if winning_trades > 0 else 0
        avg_loss = np.mean([t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0]) if losing_trades > 0 else 0
        profit_factor = abs(avg_win * winning_trades) / abs(avg_loss * losing_trades) if losing_trades > 0 else float('inf')
        
        print(f"   📈 Total Trades: {total_trades}")
        print(f"   ✅ Winning Trades: {winning_trades} ({win_rate:.1%})")
        print(f"   ❌ Losing Trades: {losing_trades} ({1-win_rate:.1%})")
        print(f"   💰 Total P&L: ${total_pnl:,.2f}")
        print(f"   📊 Average Win: ${avg_win:.2f}")
        print(f"   📉 Average Loss: ${avg_loss:.2f}")
        print(f"   🎯 Profit Factor: {profit_factor:.2f}")
        
        # Monthly breakdown
        if trades and 'entry_time' in trades[0]:
            trades_df = pd.DataFrame(trades)
            trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
            trades_df['month'] = trades_df['entry_time'].dt.to_period('M')
            monthly_pnl = trades_df.groupby('month')['pnl'].sum()
            
            print(f"\n   📅 MONTHLY PERFORMANCE:")
            for month, pnl in monthly_pnl.items():
                status = "✅" if pnl > 0 else "❌"
                print(f"      {status} {month}: ${pnl:,.2f}")
        
        # Trade duration analysis
        if 'entry_time' in trades[0] and 'exit_time' in trades[0]:
            durations = []
            for trade in trades:
                if 'entry_time' in trade and 'exit_time' in trade:
                    duration = (pd.to_datetime(trade['exit_time']) - 
                               pd.to_datetime(trade['entry_time']))
                    durations.append(duration.total_seconds() / 60)  # in minutes
            
            if durations:
                avg_duration = np.mean(durations)
                print(f"   ⏱️  Average Trade Duration: {avg_duration:.1f} minutes")
    
    def run_all_symbols(self, use_full_data=True):
        """
        Run backtests for all symbols
        """
        print("🚀 ENHANCED SCALPING STRATEGY BACKTEST")
        print("==========================================")
        print("USING REAL 1-YEAR 1-MINUTE IBKR DATA")
        print("==========================================")
        
        symbols = ['SPY', 'QQQ']
        all_results = {}
        
        for symbol in symbols:
            results = self.run_comprehensive_backtest(symbol, use_full_data)
            if results:
                all_results[symbol] = results
                self.analyze_and_display_results(results, symbol)
        
        # Final summary
        print(f"\n🎉 BACKTESTING COMPLETE!")
        print("=" * 60)
        
        for symbol, results in all_results.items():
            trades = results.get('trades', [])
            total_pnl = sum(t.get('pnl', 0) for t in trades)
            win_rate = len([t for t in trades if t.get('pnl', 0) > 0]) / len(trades) if trades else 0
            
            print(f"📈 {symbol}: {len(trades)} trades | P&L: ${total_pnl:,.2f} | Win Rate: {win_rate:.1%}")
        
        return all_results

def main():
    """
    Enhanced main function using real 1-year 1-minute data
    """
    print("🎯 SPY/QQQ OPTIONS SCALPING - ENHANCED BACKTEST")
    print("Using 1-Year of Real 1-Minute IBKR Data")
    print("=" * 60)
    
    # Ask user if they want full data or quick test
    try:
        choice = input("Run with FULL data (f) or QUICK test (q)? [f/q]: ").strip().lower()
        use_full_data = choice != 'q'
    except:
        use_full_data = True  # Default to full data
    
    if use_full_data:
        print("🚀 RUNNING COMPREHENSIVE BACKTEST WITH FULL 1-YEAR DATA")
        print("This may take a few minutes...")
    else:
        print("⚡ RUNNING QUICK BACKTEST WITH 10,000 MOST RECENT BARS")
    
    # Initialize and run
    backtester = EnhancedBacktester()
    results = backtester.run_all_symbols(use_full_data=use_full_data)
    
    print(f"\n📋 NEXT STEPS:")
    print("1. Review the performance metrics above")
    print("2. Check individual trade details in the results")
    print("3. Optimize strategy parameters if needed")
    print("4. Run with full data for final validation")

if __name__ == "__main__":
    main()
