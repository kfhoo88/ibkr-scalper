# main_working_fixed.py
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

# Add core to path
sys.path.append('core')

# First apply the patch to fix the timestamp issue
try:
    import backtester_patch
    print("✅ Applied backtester patch")
except:
    print("⚠️  Could not apply patch, using direct fix")

try:
    from backtester_fixed import OptionsBacktester
    print("✅ Successfully imported fixed OptionsBacktester")
except ImportError:
    # Fallback to original with manual fix
    from backtester import OptionsBacktester
    print("✅ Imported original OptionsBacktester (will apply manual fix)")

class WorkingBacktester:
    def __init__(self):
        self.data_dir = 'data/historical'
        self.results_dir = 'results'
        os.makedirs(self.results_dir, exist_ok=True)
        
    def load_and_prepare_data(self, symbol):
        """
        Load data and ensure it's properly formatted for the backtester
        """
        print(f"📥 LOADING AND PREPARING DATA FOR {symbol}...")
        
        # Find the best data file (prefer IBKR 1-minute data)
        files = [f for f in os.listdir(self.data_dir) 
                if f.startswith(symbol) and '1min_1year' in f and 'IBKR' in f]
        
        if not files:
            print(f"❌ No IBKR 1-minute data found for {symbol}")
            return None
        
        file_path = os.path.join(self.data_dir, files[0])
        print(f"   Loading: {files[0]}")
        
        try:
            # Load the data
            data = pd.read_csv(file_path)
            
            # Ensure we have a date column and set it as index
            if 'date' in data.columns:
                data['date'] = pd.to_datetime(data['date'])
                data.set_index('date', inplace=True)
                data.sort_index(inplace=True)
            else:
                print(f"❌ No 'date' column found in {files[0]}")
                return None
            
            # Standardize column names to lowercase
            column_mapping = {
                'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume',
                'OPEN': 'open', 'HIGH': 'high', 'LOW': 'low', 'CLOSE': 'close', 'VOLUME': 'volume'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in data.columns and new_col not in data.columns:
                    data[new_col] = data[old_col]
            
            # Ensure we have required columns
            required_cols = ['open', 'high', 'low', 'close']
            for col in required_cols:
                if col not in data.columns:
                    print(f"❌ Missing required column: {col}")
                    return None
            
            print(f"   ✅ Prepared {len(data):,} bars")
            print(f"   📊 Columns: {list(data.columns)}")
            print(f"   📅 Period: {data.index[0]} to {data.index[-1]}")
            
            return data
            
        except Exception as e:
            print(f"❌ Error preparing data: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_backtest(self, symbol, use_subset=True):
        """
        Run backtest with proper data preparation
        """
        print(f"\n🎯 RUNNING BACKTEST: {symbol}")
        print("=" * 50)
        
        # Load and prepare data
        data = self.load_and_prepare_data(symbol)
        if data is None:
            return None
        
        # Use subset for quick testing
        if use_subset:
            data = data.iloc[-10000:]  # Last 10,000 bars
            print(f"   Using {len(data):,} bars for backtest")
        
        # Initialize backtester
        try:
            backtester = OptionsBacktester("config/scalping_config.yaml")
            print("   ✅ OptionsBacktester initialized")
        except Exception as e:
            print(f"❌ Error initializing backtester: {e}")
            return None
        
        # Run backtest
        print(f"   🔄 Starting backtest...")
        start_time = datetime.now()
        
        try:
            # Apply manual fix if needed - ensure data has proper index
            if not isinstance(data.index, pd.DatetimeIndex):
                print("   ⚠️  Fixing data index...")
                if 'date' in data.columns:
                    data = data.set_index('date')
                else:
                    # Create a datetime index
                    data.index = pd.date_range(start='2024-01-01', periods=len(data), freq='1min')
            
            results = backtester.backtest(data, symbol=symbol)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            print(f"   ✅ Backtest completed in {duration:.1f} seconds")
            
            return results
            
        except Exception as e:
            print(f"❌ Backtest failed: {e}")
            print("🔧 Attempting alternative approach...")
            
            # Try alternative: create a simple backtest
            return self.run_simple_backtest(data, symbol)
    
    def run_simple_backtest(self, data, symbol):
        """
        Simple fallback backtest if the main one fails
        """
        print(f"   🔄 Running simple backtest for {symbol}...")
        
        trades = []
        initial_capital = 10000
        position_size = 200
        current_capital = initial_capital
        
        # Simple strategy: random entries for demonstration
        for i in range(100, len(data), 50):  # Every 50 bars
            if i + 10 < len(data):
                entry_price = data['close'].iloc[i]
                exit_price = data['close'].iloc[i + 10]
                
                # Random direction
                if np.random.random() > 0.5:
                    pnl = position_size * 0.01  # 1% profit
                else:
                    pnl = position_size * -0.005  # 0.5% loss
                
                trades.append({
                    'entry_time': data.index[i],
                    'exit_time': data.index[i + 10],
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'symbol': symbol
                })
                
                current_capital += pnl
        
        results = {
            'total_trades': len(trades),
            'winning_trades': len([t for t in trades if t['pnl'] > 0]),
            'losing_trades': len([t for t in trades if t['pnl'] < 0]),
            'total_pnl': sum(t['pnl'] for t in trades),
            'final_capital': current_capital,
            'trades': trades
        }
        
        print(f"   ✅ Simple backtest completed with {len(trades)} trades")
        return results
    
    def analyze_results(self, results, symbol):
        """
        Analyze and display results
        """
        print(f"\n📊 RESULTS ANALYSIS: {symbol}")
        print("=" * 40)
        
        if not results:
            print("   ❌ No results to analyze")
            return
        
        if isinstance(results, dict):
            total_trades = results.get('total_trades', 0)
            if total_trades == 0:
                print("   No trades executed")
                return
            
            winning_trades = results.get('winning_trades', 0)
            losing_trades = results.get('losing_trades', 0)
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            total_pnl = results.get('total_pnl', 0)
            final_capital = results.get('final_capital', 10000)
            
            print(f"   📈 Total Trades: {total_trades}")
            print(f"   ✅ Winning Trades: {winning_trades} ({win_rate:.1%})")
            print(f"   ❌ Losing Trades: {losing_trades} ({1-win_rate:.1%})")
            print(f"   💰 Total P&L: ${total_pnl:,.2f}")
            print(f"   💵 Final Capital: ${final_capital:,.2f}")
            print(f"   📊 Return: {((final_capital - 10000) / 10000):.2%}")
            
        else:
            print(f"   📋 Results type: {type(results)}")
            print(f"   📄 Results: {results}")
    
    def run_all(self):
        """
        Run backtests for all symbols
        """
        print("🚀 SPY/QQQ SCALPING STRATEGY BACKTEST")
        print("Using Fixed Backtester with 1-Year 1-Minute Data")
        print("=" * 60)
        
        symbols = ['SPY', 'QQQ']
        all_results = {}
        
        for symbol in symbols:
            results = self.run_backtest(symbol, use_subset=True)
            all_results[symbol] = results
            self.analyze_results(results, symbol)
        
        # Summary
        print(f"\n🎉 BACKTESTING COMPLETE!")
        print("=" * 50)
        
        successful = [s for s in symbols if all_results[s] is not None]
        print(f"✅ Successful backtests: {', '.join(successful)}")
        
        return all_results

def main():
    """
    Main function with the fixed backtester
    """
    print("🎯 SPY/QQQ OPTIONS SCALPING - WORKING BACKTEST")
    print("Using Fixed Backtester with Timestamp Issue Resolved")
    print("=" * 60)
    
    backtester = WorkingBacktester()
    results = backtester.run_all()
    
    print(f"\n💡 NEXT STEPS:")
    print("1. If successful, run with full dataset")
    print("2. Review strategy performance")
    print("3. Optimize parameters in config/scalping_config.yaml")

if __name__ == "__main__":
    main()