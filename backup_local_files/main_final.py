# main_final.py
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

sys.path.append('core')

try:
    from backtester_enhanced import EnhancedOptionsBacktester
    print("✅ Successfully imported EnhancedOptionsBacktester")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class FinalBacktester:
    def __init__(self):
        self.data_dir = 'data/historical'
        self.results_dir = 'results'
        os.makedirs(self.results_dir, exist_ok=True)
        
    def load_best_data(self, symbol):
        """Load the best available data for backtesting"""
        print(f"📥 LOADING BEST DATA FOR {symbol}...")
        
        # Prefer IBKR 1-minute data
        files = [f for f in os.listdir(self.data_dir) 
                if f.startswith(symbol) and '1min_1year' in f and 'IBKR' in f]
        
        if not files:
            print(f"❌ No IBKR 1-minute data found for {symbol}")
            return None
        
        file_path = os.path.join(self.data_dir, files[0])
        print(f"   Loading: {files[0]}")
        
        try:
            data = pd.read_csv(file_path)
            print(f"   ✅ Raw data loaded: {len(data):,} rows, {len(data.columns)} columns")
            print(f"   📋 Columns: {list(data.columns)}")
            
            return data
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return None
    
    def run_comprehensive_backtest(self, symbol, use_full_data=False):
        """Run comprehensive backtest using enhanced backtester"""
        print(f"\n🎯 COMPREHENSIVE BACKTEST: {symbol}")
        print("=" * 60)
        
        # Load data
        raw_data = self.load_best_data(symbol)
        if raw_data is None:
            return None
        
        # Initialize enhanced backtester
        backtester = EnhancedOptionsBacktester("config/scalping_config.yaml")
        
        # Use subset for quick testing unless full data requested
        if use_full_data:
            test_data = raw_data
            print(f"   🚀 Using FULL {len(test_data):,} bars")
        else:
            test_data = raw_data.iloc[-20000:]  # Last 20,000 bars for reasonable test
            print(f"   ⚡ Using {len(test_data):,} most recent bars")
        
        # Run backtest
        print(f"   🔄 Starting enhanced backtest...")
        start_time = datetime.now()
        
        try:
            results = backtester.backtest(test_data, symbol=symbol)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"   ✅ Enhanced backtest completed in {duration:.1f} seconds")
            return results
            
        except Exception as e:
            print(f"❌ Enhanced backtest failed: {e}")
            return None
    
    def analyze_performance(self, results, symbol):
        """Comprehensive performance analysis"""
        if not results:
            return
        
        print(f"\n📊 DETAILED PERFORMANCE: {symbol}")
        print("=" * 50)
        
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
        
        print(f"   📈 Total Trades: {total_trades}")
        print(f"   ✅ Winning Trades: {winning_trades} ({win_rate:.1%})")
        print(f"   ❌ Losing Trades: {losing_trades} ({1-win_rate:.1%})")
        print(f"   💰 Total P&L: ${total_pnl:,.2f}")
        print(f"   💵 Final Capital: ${final_capital:,.2f}")
        print(f"   📊 Total Return: {results['total_return']:.2%}")
        
        # Trade statistics
        if trades:
            pnls = [t['pnl'] for t in trades]
            avg_trade = np.mean(pnls)
            best_trade = max(pnls)
            worst_trade = min(pnls)
            
            print(f"   📊 Average Trade: ${avg_trade:.2f}")
            print(f"   🏆 Best Trade: ${best_trade:.2f}")
            print(f"   📉 Worst Trade: ${worst_trade:.2f}")
            
            # Monthly performance
            trades_df = pd.DataFrame(trades)
            trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
            trades_df['month'] = trades_df['entry_time'].dt.to_period('M')
            monthly_pnl = trades_df.groupby('month')['pnl'].sum()
            
            print(f"\n   📅 MONTHLY PERFORMANCE:")
            for month, pnl in monthly_pnl.items():
                status = "🟢" if pnl > 0 else "🔴"
                print(f"      {status} {month}: ${pnl:,.2f}")
    
    def run_production_backtest(self):
        """Run production-ready backtest"""
        print("🚀 PRODUCTION SCALPING STRATEGY BACKTEST")
        print("Using Enhanced Backtester with Real Market Data")
        print("=" * 60)
        
        symbols = ['SPY', 'QQQ']
        all_results = {}
        
        for symbol in symbols:
            # First run with subset for quick validation
            print(f"\n🔧 VALIDATING {symbol}...")
            results = self.run_comprehensive_backtest(symbol, use_full_data=False)
            
            if results and results['total_trades'] > 0:
                all_results[symbol] = results
                self.analyze_performance(results, symbol)
                
                # Ask if user wants to run full backtest
                try:
                    run_full = input(f"\n   Run FULL 1-year backtest for {symbol}? (y/n): ").strip().lower()
                    if run_full == 'y':
                        print(f"   🚀 STARTING FULL 1-YEAR BACKTEST FOR {symbol}...")
                        full_results = self.run_comprehensive_backtest(symbol, use_full_data=True)
                        if full_results:
                            all_results[symbol + '_FULL'] = full_results
                            self.analyze_performance(full_results, symbol + " (FULL)")
                except:
                    print("   ⏩ Skipping full backtest")
            else:
                print(f"❌ Validation failed for {symbol}")
        
        # Final summary
        print(f"\n🎉 PRODUCTION BACKTESTING COMPLETE!")
        print("=" * 60)
        
        successful = [s for s in symbols if s in all_results]
        print(f"✅ Successful backtests: {', '.join(successful)}")
        
        if all_results:
            total_all_pnl = sum(results['total_pnl'] for results in all_results.values() 
                              if isinstance(results, dict) and 'total_pnl' in results)
            print(f"💰 COMBINED P&L: ${total_all_pnl:,.2f}")
        
        return all_results

def main():
    """Main production backtest function"""
    print("🎯 SPY/QQQ OPTIONS SCALPING - PRODUCTION BACKTEST")
    print("Using Enhanced Backtester with Real 1-Year 1-Minute Data")
    print("=" * 60)
    
    backtester = FinalBacktester()
    results = backtester.run_production_backtest()
    
    print(f"\n📋 NEXT STEPS:")
    print("1. Review the strategy performance above")
    print("2. Check individual trade details in the results")
    print("3. Optimize strategy parameters in config/scalping_config.yaml")
    print("4. Consider running overnight with full dataset")
    print("5. Prepare for live paper trading")

if __name__ == "__main__":
    main()