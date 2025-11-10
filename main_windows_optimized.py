# main_windows_optimized.py
import pandas as pd
import numpy as np
import os
import sys
import time
from datetime import datetime
import multiprocessing as mp

# Add core to path
sys.path.append('core')

try:
    from backtester_enhanced import EnhancedOptionsBacktester
    print("✅ Successfully imported EnhancedOptionsBacktester")
except ImportError as e:
    print(f"❌ Import error: {e}")
    # Create a simple fallback
    class EnhancedOptionsBacktester:
        def backtest(self, data, symbol):
            return {'total_trades': 0, 'total_pnl': 0}

class WindowsOptimizedBacktester:
    def __init__(self):
        self.data_dir = 'data/historical'
        self.results_dir = 'results'
        os.makedirs(self.results_dir, exist_ok=True)
        
    def load_data_optimized(self, symbol):
        """Optimized data loading for Windows"""
        print(f"📥 LOADING {symbol} DATA (OPTIMIZED)...")
        
        files = [f for f in os.listdir(self.data_dir) 
                if f.startswith(symbol) and '1min_1year' in f and 'IBKR' in f]
        
        if not files:
            print(f"❌ No data found for {symbol}")
            return None
        
        file_path = os.path.join(self.data_dir, files[0])
        print(f"   File: {files[0]}")
        
        try:
            # Use optimized pandas reading
            data = pd.read_csv(file_path, parse_dates=['date'], infer_datetime_format=True)
            data.set_index('date', inplace=True)
            
            print(f"   ✅ Loaded {len(data):,} bars")
            print(f"   📅 {data.index[0]} to {data.index[-1]}")
            
            return data
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def run_optimized_backtest(self, symbol, use_full_data=True):
        """Run optimized backtest with progress tracking"""
        print(f"\n🎯 OPTIMIZED BACKTEST: {symbol}")
        print("=" * 50)
        
        data = self.load_data_optimized(symbol)
        if data is None:
            return None
        
        if not use_full_data:
            # Use 50,000 bars for quick test
            data = data.iloc[-50000:]
            print(f"   ⚡ Using {len(data):,} bars for quick test")
        else:
            print(f"   🚀 USING FULL {len(data):,} BARS")
        
        backtester = EnhancedOptionsBacktester("config/scalping_config.yaml")
        
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
    
    def display_optimized_results(self, results, symbol):
        """Display results in an optimized format"""
        if not results:
            return
        
        print(f"\n📊 OPTIMIZED RESULTS: {symbol}")
        print("=" * 40)
        
        trades = results.get('trades', [])
        total_trades = len(trades)
        
        if total_trades == 0:
            print("   No trades executed")
            return
        
        # Quick metrics
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        win_rate = winning_trades / total_trades
        total_pnl = results['total_pnl']
        
        print(f"   📈 Trades: {total_trades:,}")
        print(f"   ✅ Win Rate: {win_rate:.1%}")
        print(f"   💰 P&L: ${total_pnl:,.2f}")
        print(f"   📊 Return: {results['total_return']:.2%}")
        
        # Quick monthly summary
        if trades and 'entry_time' in trades[0]:
            trades_df = pd.DataFrame(trades)
            trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
            trades_df['month'] = trades_df['entry_time'].dt.to_period('M')
            monthly_pnl = trades_df.groupby('month')['pnl'].sum()
            
            profitable_months = len([p for p in monthly_pnl if p > 0])
            total_months = len(monthly_pnl)
            
            print(f"   📅 Profitable Months: {profitable_months}/{total_months}")
    
    def run_parallel_estimation(self):
        """Run quick estimations in parallel"""
        print("🔮 QUICK PERFORMANCE ESTIMATION")
        print("=" * 50)
        
        symbols = ['SPY', 'QQQ']
        
        for symbol in symbols:
            data = self.load_data_optimized(symbol)
            if data is not None:
                # Use first 10,000 bars for quick estimation
                sample_data = data.iloc[:10000]
                backtester = EnhancedOptionsBacktester()
                
                try:
                    sample_results = backtester.backtest(sample_data, symbol)
                    if sample_results:
                        trades = sample_results['total_trades']
                        pnl = sample_results['total_pnl']
                        
                        # Estimate full year (scale by data size)
                        full_estimate_trades = int(trades * (len(data) / len(sample_data)))
                        full_estimate_pnl = pnl * (len(data) / len(sample_data))
                        
                        print(f"\n   📈 {symbol} ESTIMATION:")
                        print(f"      • Full Year Trades: ~{full_estimate_trades:,}")
                        print(f"      • Full Year P&L: ~${full_estimate_pnl:,.2f}")
                        print(f"      • Monthly P&L: ~${full_estimate_pnl/12:,.2f}")
                        
                except Exception as e:
                    print(f"   ❌ {symbol} estimation failed: {e}")
    
    def run_windows_optimized(self):
        """Main optimized function for Windows"""
        print("🚀 WINDOWS-OPTIMIZED 1-YEAR BACKTEST")
        print("=" * 60)
        print("Fresh Python 3.13 - Should be faster!")
        print("=" * 60)
        
        # Show system info
        print(f"🖥️  System: Windows 10")
        print(f"🐍 Python: {sys.version.split()[0]}")
        print(f"💾 RAM: {psutil.virtual_memory().total // (1024**3)}GB available")
        
        # First show quick estimations
        self.run_parallel_estimation()
        
        # Ask user for backtest type
        try:
            print(f"\n🎯 BACKTEST OPTIONS:")
            print("   1. Quick test (50,000 bars - ~5 minutes)")
            print("   2. Full 1-year test (99,300 bars - ~15-30 minutes)")
            
            choice = input("\n   Choose option (1 or 2): ").strip()
            use_full_data = (choice == "2")
            
            if use_full_data:
                print(f"   🚀 SELECTED: FULL 1-YEAR BACKTEST")
            else:
                print(f"   ⚡ SELECTED: QUICK TEST")
                
        except:
            use_full_data = False  # Default to quick test
            print(f"   ⚡ DEFAULT: QUICK TEST")
        
        symbols = ['SPY', 'QQQ']
        all_results = {}
        
        for symbol in symbols:
            print(f"\n{'='*60}")
            print(f"PROCESSING: {symbol}")
            print(f"{'='*60}")
            
            results = self.run_optimized_backtest(symbol, use_full_data)
            if results:
                all_results[symbol] = results
                self.display_optimized_results(results, symbol)
            
            # Small delay between symbols
            time.sleep(1)
        
        # Final summary
        if all_results:
            print(f"\n🎉 BACKTESTING COMPLETE!")
            print("=" * 60)
            
            total_pnl = sum(r['total_pnl'] for r in all_results.values())
            total_trades = sum(r['total_trades'] for r in all_results.values())
            
            print(f"📊 COMBINED RESULTS:")
            print(f"   • Total Trades: {total_trades:,}")
            print(f"   • Total P&L: ${total_pnl:,.2f}")
            
            if use_full_data:
                monthly_avg = total_pnl / 12
                print(f"   • Monthly Average: ${monthly_avg:,.2f}")
                print(f"   • $20k Target: {monthly_avg/20000:.1%}")
        
        return all_results

# Add psutil for system info, but make it optional
try:
    import psutil
except ImportError:
    print("⚠️  Install psutil for system info: pip install psutil")
    psutil = None

def main():
    """Main Windows-optimized backtest"""
    print("🎯 SPY/QQQ SCALPING - WINDOWS OPTIMIZED")
    print("Fresh Python 3.13 Installation")
    print("=" * 60)
    
    backtester = WindowsOptimizedBacktester()
    results = backtester.run_windows_optimized()
    
    print(f"\n💡 NEXT STEPS:")
    if results:
        print("1. Review the performance metrics")
        print("2. Check if strategy meets expectations")
        print("3. Optimize parameters in config/scalping_config.yaml")
        print("4. Consider live paper trading")
    else:
        print("1. Check data files in data/historical/")
        print("2. Verify all dependencies are installed")
        print("3. Run setup script: python windows_setup.py")

if __name__ == "__main__":
    main()