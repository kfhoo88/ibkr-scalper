# main_windows_fixed.py
import pandas as pd
import numpy as np
import os
import sys
import time
from datetime import datetime

# Add core to path
sys.path.append('core')

try:
    from backtester_enhanced import EnhancedOptionsBacktester
    print("✅ Successfully imported EnhancedOptionsBacktester")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class WindowsFixedBacktester:
    def __init__(self):
        self.data_dir = 'data/historical'
        self.results_dir = 'results'
        os.makedirs(self.results_dir, exist_ok=True)
        
    def load_data_fixed(self, symbol):
        """Load data with proper error handling"""
        print(f"📥 LOADING {symbol} DATA...")
        
        # Look for 1-minute data files
        files = [f for f in os.listdir(self.data_dir) 
                if f.startswith(symbol) and '1min' in f]
        
        if not files:
            print(f"❌ No 1-minute data found for {symbol}")
            print(f"   Available files: {[f for f in os.listdir(self.data_dir) if symbol in f]}")
            return None
        
        # Use the largest file (likely the 1-year data)
        file_sizes = [(f, os.path.getsize(os.path.join(self.data_dir, f))) for f in files]
        largest_file = max(file_sizes, key=lambda x: x[1])[0]
        file_path = os.path.join(self.data_dir, largest_file)
        
        print(f"   File: {largest_file}")
        
        try:
            # Load the data
            data = pd.read_csv(file_path)
            print(f"   ✅ Loaded {len(data):,} rows")
            print(f"   📋 Columns: {list(data.columns)}")
            
            # Check if we have date column
            if 'date' not in data.columns and 'Date' not in data.columns and 'Datetime' not in data.columns:
                print(f"   ⚠️  No date column found, using index")
                # Create a date index
                data.index = pd.date_range(start='2024-01-01', periods=len(data), freq='1min')
            else:
                # Use available date column
                date_col = 'date' if 'date' in data.columns else ('Date' if 'Date' in data.columns else 'Datetime')
                data[date_col] = pd.to_datetime(data[date_col])
                data.set_index(date_col, inplace=True)
            
            return data
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return None
    
    def run_fixed_backtest(self, symbol, use_full_data=True):
        """Run backtest with fixed data handling"""
        print(f"\n🎯 BACKTEST: {symbol}")
        print("=" * 50)
        
        data = self.load_data_fixed(symbol)
        if data is None:
            return None
        
        if not use_full_data:
            # Use reasonable subset for quick test
            test_size = min(50000, len(data))
            data = data.iloc[-test_size:]
            print(f"   ⚡ Using {len(data):,} bars for quick test")
        else:
            print(f"   🚀 USING FULL {len(data):,} BARS")
        
        backtester = EnhancedOptionsBacktester()
        
        print(f"   🔄 Starting backtest...")
        start_time = time.time()
        
        try:
            results = backtester.backtest(data, symbol=symbol)
            end_time = time.time()
            duration = (end_time - start_time) / 60
            
            print(f"   ✅ Completed in {duration:.1f} minutes")
            return results
            
        except Exception as e:
            print(f"❌ Backtest failed: {e}")
            return None
    
    def display_fixed_results(self, results, symbol):
        """Display results with proper formatting"""
        if not results:
            return
        
        print(f"\n📊 RESULTS: {symbol}")
        print("=" * 40)
        
        trades = results.get('trades', [])
        total_trades = len(trades)
        
        if total_trades == 0:
            print("   No trades executed")
            return
        
        # Basic metrics
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = len([t for t in trades if t['pnl'] < 0])
        win_rate = winning_trades / total_trades
        total_pnl = results['total_pnl']
        final_capital = results['final_capital']
        initial_capital = 10000
        
        print(f"   📈 Total Trades: {total_trades:,}")
        print(f"   ✅ Winning Trades: {winning_trades:,} ({win_rate:.1%})")
        print(f"   ❌ Losing Trades: {losing_trades:,} ({1-win_rate:.1%})")
        print(f"   💰 Total P&L: ${total_pnl:,.2f}")
        print(f"   💵 Final Capital: ${final_capital:,.2f}")
        print(f"   📊 Total Return: {results['total_return']:.2%}")
        
        # Additional metrics
        if trades:
            pnls = [t['pnl'] for t in trades]
            avg_trade = np.mean(pnls)
            best_trade = max(pnls)
            worst_trade = min(pnls)
            
            print(f"\n   📊 Trade Statistics:")
            print(f"      • Average Trade: ${avg_trade:.2f}")
            print(f"      • Best Trade: ${best_trade:.2f}")
            print(f"      • Worst Trade: ${worst_trade:.2f}")
            
            # Calculate monthly performance if we have trade dates
            if 'entry_time' in trades[0]:
                try:
                    trades_df = pd.DataFrame(trades)
                    trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
                    trades_df['month'] = trades_df['entry_time'].dt.to_period('M')
                    monthly_pnl = trades_df.groupby('month')['pnl'].sum()
                    
                    print(f"\n   📅 MONTHLY PERFORMANCE:")
                    for month, pnl in monthly_pnl.items():
                        status = "🟢" if pnl > 0 else "🔴"
                        print(f"      {status} {month}: ${pnl:,.2f}")
                except:
                    print(f"   📅 (Monthly data unavailable)")
    
    def run_complete_analysis(self):
        """Run complete analysis with user options"""
        print("🚀 SPY/QQQ SCALPING STRATEGY ANALYSIS")
        print("Windows 10 + Python 3.13")
        print("=" * 60)
        
        # Show available data first
        print("📊 AVAILABLE DATA:")
        for symbol in ['SPY', 'QQQ']:
            files = [f for f in os.listdir(self.data_dir) if symbol in f and '1min' in f]
            if files:
                file_sizes = [(f, os.path.getsize(os.path.join(self.data_dir, f))) for f in files]
                largest_file = max(file_sizes, key=lambda x: x[1])
                print(f"   {symbol}: {largest_file[0]} ({largest_file[1]//1024} KB)")
        
        # Get user preference
        try:
            print(f"\n🎯 BACKTEST OPTIONS:")
            print("   1. Quick test (~50,000 bars)")
            print("   2. Full dataset")
            
            choice = input("\n   Choose option (1 or 2): ").strip()
            use_full_data = (choice == "2")
            
            if use_full_data:
                print(f"   🚀 SELECTED: FULL DATASET")
            else:
                print(f"   ⚡ SELECTED: QUICK TEST")
                
        except:
            use_full_data = False
            print(f"   ⚡ DEFAULT: QUICK TEST")
        
        symbols = ['SPY', 'QQQ']
        all_results = {}
        
        for symbol in symbols:
            print(f"\n{'='*60}")
            print(f"PROCESSING: {symbol}")
            print(f"{'='*60}")
            
            results = self.run_fixed_backtest(symbol, use_full_data)
            if results:
                all_results[symbol] = results
                self.display_fixed_results(results, symbol)
            
            time.sleep(1)  # Small delay between symbols
        
        # Final summary
        if all_results:
            print(f"\n🎉 ANALYSIS COMPLETE!")
            print("=" * 60)
            
            total_pnl = sum(r['total_pnl'] for r in all_results.values())
            total_trades = sum(r['total_trades'] for r in all_results.values())
            
            print(f"📊 COMBINED RESULTS:")
            print(f"   • Total Trades: {total_trades:,}")
            print(f"   • Total P&L: ${total_pnl:,.2f}")
            
            if use_full_data:
                monthly_avg = total_pnl / 12
                target_achievement = (monthly_avg / 20000) * 100
                print(f"   • Monthly Average: ${monthly_avg:,.2f}")
                print(f"   • $20k/Month Target: {target_achievement:.1f}%")
        
        return all_results

def main():
    """Main fixed backtest function"""
    print("🎯 SPY/QQQ OPTIONS SCALPING - WINDOWS FIXED")
    print("No missing dependencies - Ready to run!")
    print("=" * 60)
    
    backtester = WindowsFixedBacktester()
    results = backtester.run_complete_analysis()
    
    print(f"\n💡 NEXT STEPS:")
    if results:
        print("1. Review strategy performance above")
        print("2. Check if win rate and P&L meet expectations") 
        print("3. Optimize parameters in config if needed")
        print("4. Consider paper trading with live data")
    else:
        print("1. Check data files in data/historical/")
        print("2. Verify the backtester_enhanced.py file exists")
        print("3. Run with different data subset sizes")

if __name__ == "__main__":
    main()