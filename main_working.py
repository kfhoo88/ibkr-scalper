# main_working.py
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

# Add core to Python path
sys.path.append('core')

# Import the actual class that exists
try:
    from backtester import OptionsBacktester
    print("✅ Successfully imported OptionsBacktester")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class WorkingBacktester:
    def __init__(self):
        self.data_dir = 'data/historical'
        self.results_dir = 'results'
        os.makedirs(self.results_dir, exist_ok=True)
        
    def load_1year_1min_data(self, symbol):
        """
        Load the actual 1-year 1-minute IBKR data
        """
        print(f"📥 LOADING 1-YEAR 1-MIN DATA FOR {symbol}...")
        
        # Look for IBKR 1-minute data files
        files = [f for f in os.listdir(self.data_dir) 
                if f.startswith(symbol) and '1min_1year' in f and 'IBKR' in f]
        
        if not files:
            print(f"❌ No 1-year 1-min IBKR data found for {symbol}")
            # Show what files are available
            available = [f for f in os.listdir(self.data_dir) if symbol in f and f.endswith('.csv')]
            if available:
                print(f"   Available files: {available}")
                # Use any available file
                files = available
            else:
                return None
        
        # Use the most recent file
        latest_file = sorted(files)[-1]
        file_path = os.path.join(self.data_dir, latest_file)
        
        print(f"   Loading: {latest_file}")
        
        try:
            data = pd.read_csv(file_path)
            data['date'] = pd.to_datetime(data['date'])
            
            # Standardize column names to match what OptionsBacktester expects
            column_map = {
                'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume',
                'OPEN': 'open', 'HIGH': 'high', 'LOW': 'low', 'CLOSE': 'close', 'VOLUME': 'volume',
                'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close', 'Volume': 'Volume'  # Keep original too
            }
            
            for old_col, new_col in column_map.items():
                if old_col in data.columns and new_col not in data.columns:
                    data[new_col] = data[old_col]
            
            # Ensure we have the required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in data.columns:
                    print(f"❌ Missing required column: {col}")
                    print(f"   Available columns: {list(data.columns)}")
                    return None
            
            data.set_index('date', inplace=True)
            data.sort_index(inplace=True)
            
            print(f"   ✅ Successfully loaded {len(data):,} bars")
            print(f"   📅 Period: {data.index.min()} to {data.index.max()}")
            
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
        
        # Initialize the actual OptionsBacktester
        backtester = OptionsBacktester(config_path="config/scalping_config.yaml")
        
        print(f"   ⚙️  Initialized OptionsBacktester with config")
        
        # Run the backtest using the actual backtest method
        print(f"\n   🔄 RUNNING BACKTEST...")
        start_time = datetime.now()
        
        try:
            # Call the actual backtest method from OptionsBacktester
            results = backtester.backtest(data, symbol=symbol)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"   ✅ BACKTEST COMPLETED IN {duration:.1f} SECONDS")
            
            return results
            
        except Exception as e:
            print(f"❌ Error during backtest: {e}")
            return None
    
    def analyze_results(self, results, symbol):
        """
        Analyze and display results from OptionsBacktester
        """
        if not results:
            print(f"❌ No results to analyze for {symbol}")
            return
        
        print(f"\n📊 PERFORMANCE ANALYSIS: {symbol}")
        print("=" * 50)
        
        # The structure depends on what OptionsBacktester.backtest() returns
        # Let's handle different possible return structures
        
        if isinstance(results, dict):
            # If it returns a dictionary
            self._analyze_dict_results(results, symbol)
        elif isinstance(results, pd.DataFrame):
            # If it returns a DataFrame with trades
            self._analyze_dataframe_results(results, symbol)
        else:
            print(f"   Results type: {type(results)}")
            print(f"   Results: {results}")
    
    def _analyze_dict_results(self, results, symbol):
        """Analyze dictionary results"""
        # Common keys that might be in the results
        possible_keys = ['total_trades', 'winning_trades', 'losing_trades', 'win_rate', 
                        'total_pnl', 'total_return', 'final_capital', 'trades']
        
        found_keys = [key for key in possible_keys if key in results]
        
        if found_keys:
            print(f"   📈 Found metrics: {', '.join(found_keys)}")
            
            if 'total_trades' in results:
                print(f"   📊 Total Trades: {results['total_trades']}")
            if 'win_rate' in results:
                print(f"   ✅ Win Rate: {results['win_rate']:.1%}")
            if 'total_pnl' in results:
                print(f"   💰 Total P&L: ${results['total_pnl']:,.2f}")
            if 'total_return' in results:
                print(f"   📈 Total Return: {results['total_return']:.2%}")
            if 'final_capital' in results:
                print(f"   💵 Final Capital: ${results['final_capital']:,.2f}")
        else:
            # Try to extract trades if they exist
            if 'trades' in results and isinstance(results['trades'], list):
                trades = results['trades']
                self._analyze_trades_list(trades, symbol)
            else:
                print(f"   📋 Results keys: {list(results.keys())}")
    
    def _analyze_dataframe_results(self, results_df, symbol):
        """Analyze DataFrame results"""
        print(f"   📊 Results DataFrame shape: {results_df.shape}")
        print(f"   📋 Columns: {list(results_df.columns)}")
        
        # If it's a trades DataFrame
        if 'pnl' in results_df.columns:
            total_trades = len(results_df)
            winning_trades = len(results_df[results_df['pnl'] > 0])
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            total_pnl = results_df['pnl'].sum()
            
            print(f"   📈 Total Trades: {total_trades}")
            print(f"   ✅ Win Rate: {win_rate:.1%}")
            print(f"   💰 Total P&L: ${total_pnl:,.2f}")
    
    def _analyze_trades_list(self, trades, symbol):
        """Analyze list of trades"""
        if not trades:
            print(f"   No trades executed for {symbol}")
            return
        
        total_trades = len(trades)
        winning_trades = len([t for t in trades if isinstance(t, dict) and t.get('pnl', 0) > 0])
        win_rate = winning_trades / total_trades
        
        # Calculate total P&L
        total_pnl = 0
        for trade in trades:
            if isinstance(trade, dict) and 'pnl' in trade:
                total_pnl += trade['pnl']
        
        print(f"   📈 Total Trades: {total_trades}")
        print(f"   ✅ Win Rate: {win_rate:.1%}")
        print(f"   💰 Total P&L: ${total_pnl:,.2f}")
        
        # Show first few trades
        print(f"\n   📋 SAMPLE TRADES (first 3):")
        for i, trade in enumerate(trades[:3]):
            if isinstance(trade, dict):
                print(f"      Trade {i+1}: {trade}")
    
    def run_all_symbols(self, use_full_data=True):
        """
        Run backtests for all symbols using the actual OptionsBacktester
        """
        print("🚀 SPY/QQQ SCALPING STRATEGY BACKTEST")
        print("==========================================")
        print("USING REAL 1-YEAR 1-MINUTE IBKR DATA")
        print("AND ACTUAL OptionsBacktester CLASS")
        print("==========================================")
        
        symbols = ['SPY', 'QQQ']
        all_results = {}
        
        for symbol in symbols:
            results = self.run_comprehensive_backtest(symbol, use_full_data)
            if results is not None:
                all_results[symbol] = results
                self.analyze_results(results, symbol)
            else:
                print(f"❌ Backtest failed for {symbol}")
        
        # Final summary
        print(f"\n🎉 BACKTESTING COMPLETE!")
        print("=" * 60)
        
        successful_symbols = [s for s in symbols if s in all_results]
        print(f"✅ Successful backtests: {', '.join(successful_symbols)}")
        
        return all_results

def main():
    """
    Main function using the actual OptionsBacktester class
    """
    print("🎯 SPY/QQQ OPTIONS SCALPING - PRODUCTION BACKTEST")
    print("Using OptionsBacktester with 1-Year 1-Minute IBKR Data")
    print("=" * 60)
    
    # Ask user for data size preference
    try:
        choice = input("Run with FULL data (f) or QUICK test (q)? [f/q]: ").strip().lower()
        use_full_data = choice != 'q'
    except:
        use_full_data = False  # Default to quick test for safety
    
    if use_full_data:
        print("🚀 RUNNING COMPREHENSIVE BACKTEST WITH FULL 1-YEAR DATA")
        print("This may take several minutes...")
    else:
        print("⚡ RUNNING QUICK BACKTEST WITH 10,000 MOST RECENT BARS")
    
    # Initialize and run
    backtester = WorkingBacktester()
    results = backtester.run_all_symbols(use_full_data=use_full_data)
    
    print(f"\n📋 NEXT STEPS:")
    print("1. Review the performance metrics above")
    print("2. Check the strategy logic in core/backtester.py")
    print("3. Optimize parameters in config/scalping_config.yaml")
    print("4. Run with full data for final validation")

if __name__ == "__main__":
    main()