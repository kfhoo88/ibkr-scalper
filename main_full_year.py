# main_full_year.py
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
import time

sys.path.append('core')

try:
    from backtester_enhanced import EnhancedOptionsBacktester
    print("✅ Successfully imported EnhancedOptionsBacktester")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class FullYearBacktester:
    def __init__(self):
        self.data_dir = 'data/historical'
        self.results_dir = 'results'
        os.makedirs(self.results_dir, exist_ok=True)
        
    def load_full_year_data(self, symbol):
        """Load the complete 1-year 1-minute dataset"""
        print(f"📥 LOADING FULL 1-YEAR DATA FOR {symbol}...")
        
        # Find the IBKR 1-minute data
        files = [f for f in os.listdir(self.data_dir) 
                if f.startswith(symbol) and '1min_1year' in f and 'IBKR' in f]
        
        if not files:
            print(f"❌ No IBKR 1-minute data found for {symbol}")
            return None
        
        file_path = os.path.join(self.data_dir, files[0])
        print(f"   Loading: {files[0]}")
        
        try:
            data = pd.read_csv(file_path)
            print(f"   ✅ Full dataset loaded: {len(data):,} bars")
            print(f"   📅 Complete period: {data['date'].iloc[0]} to {data['date'].iloc[-1]}")
            
            return data
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return None
    
    def run_full_year_backtest(self, symbol):
        """Run backtest on the ENTIRE 1-year dataset"""
        print(f"\n🎯 FULL 1-YEAR BACKTEST: {symbol}")
        print("=" * 60)
        
        # Load the complete dataset
        full_data = self.load_full_year_data(symbol)
        if full_data is None:
            return None
        
        # Initialize enhanced backtester
        backtester = EnhancedOptionsBacktester("config/scalping_config.yaml")
        
        print(f"   🚀 USING COMPLETE DATASET: {len(full_data):,} bars")
        print(f"   ⏰ This will take several minutes...")
        
        # Run backtest on FULL data
        start_time = time.time()
        
        try:
            results = backtester.backtest(full_data, symbol=symbol)
            end_time = time.time()
            duration = (end_time - start_time) / 60  # Convert to minutes
            
            print(f"   ✅ Full-year backtest completed in {duration:.1f} minutes")
            return results
            
        except Exception as e:
            print(f"❌ Full-year backtest failed: {e}")
            return None
    
    def analyze_full_year_performance(self, results, symbol):
        """Comprehensive analysis of full-year performance"""
        if not results:
            return
        
        print(f"\n📊 FULL 1-YEAR PERFORMANCE: {symbol}")
        print("=" * 60)
        
        trades = results.get('trades', [])
        total_trades = len(trades)
        
        if total_trades == 0:
            print("   No trades executed in the full year")
            return
        
        # Basic metrics
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = len([t for t in trades if t['pnl'] < 0])
        win_rate = winning_trades / total_trades
        total_pnl = results['total_pnl']
        final_capital = results['final_capital']
        initial_capital = 10000
        
        print(f"   📈 Total Trades (1 Year): {total_trades:,}")
        print(f"   ✅ Winning Trades: {winning_trades:,} ({win_rate:.1%})")
        print(f"   ❌ Losing Trades: {losing_trades:,} ({1-win_rate:.1%})")
        print(f"   💰 Total P&L: ${total_pnl:,.2f}")
        print(f"   💵 Final Capital: ${final_capital:,.2f}")
        print(f"   📊 Total Return: {results['total_return']:.2%}")
        
        # Advanced metrics
        if trades:
            pnls = [t['pnl'] for t in trades]
            avg_trade = np.mean(pnls)
            best_trade = max(pnls)
            worst_trade = min(pnls)
            std_trade = np.std(pnls)
            
            print(f"\n   📊 Trade Statistics:")
            print(f"      • Average Trade: ${avg_trade:.2f}")
            print(f"      • Best Trade: ${best_trade:.2f}")
            print(f"      • Worst Trade: ${worst_trade:.2f}")
            print(f"      • Std Deviation: ${std_trade:.2f}")
            print(f"      • Risk/Reward Ratio: {abs(avg_trade)/std_trade:.2f}")
            
            # Monthly performance breakdown
            trades_df = pd.DataFrame(trades)
            trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
            trades_df['month'] = trades_df['entry_time'].dt.to_period('M')
            monthly_stats = trades_df.groupby('month').agg({
                'pnl': ['sum', 'count'],
                'portfolio_value': 'last'
            }).round(2)
            
            print(f"\n   📅 MONTHLY BREAKDOWN:")
            for month in monthly_stats.index:
                month_pnl = monthly_stats.loc[month, ('pnl', 'sum')]
                month_trades = monthly_stats.loc[month, ('pnl', 'count')]
                status = "🟢" if month_pnl > 0 else "🔴"
                print(f"      {status} {month}: ${month_pnl:,.2f} ({month_trades} trades)")
            
            # Win rate by month
            monthly_win_rates = trades_df.groupby('month').apply(
                lambda x: (x['pnl'] > 0).sum() / len(x)
            )
            
            print(f"\n   🎯 MONTHLY WIN RATES:")
            for month, win_rate in monthly_win_rates.items():
                print(f"      • {month}: {win_rate:.1%}")
    
    def estimate_performance(self, symbol):
        """Estimate what full backtest might look like based on sample"""
        print(f"\n🔮 PERFORMANCE ESTIMATION FOR {symbol}")
        print("=" * 50)
        
        # Load full data but use sample for quick estimation
        full_data = self.load_full_year_data(symbol)
        if full_data is None:
            return
        
        # Use first 10,000 bars for quick estimation
        sample_data = full_data.iloc[:10000]
        print(f"   Using {len(sample_data):,} bars for quick estimation")
        
        backtester = EnhancedOptionsBacktester("config/scalping_config.yaml")
        
        try:
            sample_results = backtester.backtest(sample_data, symbol=symbol)
            
            if sample_results and sample_results['total_trades'] > 0:
                # Extrapolate to full year
                sample_trades = sample_results['total_trades']
                sample_pnl = sample_results['total_pnl']
                sample_bars = len(sample_data)
                full_bars = len(full_data)
                
                # Estimate full year performance
                estimated_trades = int(sample_trades * (full_bars / sample_bars))
                estimated_pnl = sample_pnl * (full_bars / sample_bars)
                estimated_return = estimated_pnl / 10000
                
                print(f"\n   📈 ESTIMATED FULL-YEAR PERFORMANCE:")
                print(f"      • Estimated Trades: {estimated_trades:,}")
                print(f"      • Estimated P&L: ${estimated_pnl:,.2f}")
                print(f"      • Estimated Return: {estimated_return:.2%}")
                print(f"      • Based on {sample_trades} trades in sample")
                
        except Exception as e:
            print(f"   ❌ Estimation failed: {e}")
    
    def run_complete_analysis(self):
        """Run complete 1-year analysis for all symbols"""
        print("🚀 COMPLETE 1-YEAR SCALPING STRATEGY ANALYSIS")
        print("Using Full 99,300 Bars of 1-Minute Data")
        print("=" * 70)
        
        symbols = ['SPY', 'QQQ']
        all_results = {}
        
        # First show estimations
        for symbol in symbols:
            self.estimate_performance(symbol)
        
        # Ask user if they want to run full backtest
        try:
            print(f"\n⚠️  FULL 1-YEAR BACKTEST WARNING:")
            print("   This will process 99,300 bars per symbol")
            print("   Estimated time: 10-30 minutes per symbol")
            print("   Computer performance may be affected")
            
            run_full = input(f"\n   Run FULL 1-year backtest? (y/n): ").strip().lower()
            if run_full != 'y':
                print("   ⏩ Skipping full backtest - use estimations above")
                return {}
        except:
            print("   ⏩ Auto-skipping full backtest")
            return {}
        
        # Run full backtests
        for symbol in symbols:
            print(f"\n{'='*70}")
            print(f"STARTING FULL 1-YEAR BACKTEST: {symbol}")
            print(f"{'='*70}")
            
            results = self.run_full_year_backtest(symbol)
            if results:
                all_results[symbol] = results
                self.analyze_full_year_performance(results, symbol)
            
            # Small delay between symbols
            time.sleep(2)
        
        # Final summary
        if all_results:
            print(f"\n🎉 FULL 1-YEAR BACKTESTING COMPLETE!")
            print("=" * 70)
            
            total_combined_pnl = sum(results['total_pnl'] for results in all_results.values())
            total_combined_trades = sum(results['total_trades'] for results in all_results.values())
            
            print(f"📊 COMBINED 1-YEAR RESULTS:")
            print(f"   • Total Trades: {total_combined_trades:,}")
            print(f"   • Combined P&L: ${total_combined_pnl:,.2f}")
            print(f"   • Annual Return: {(total_combined_pnl / 20000):.2%}")
            
            # Calculate monthly average
            avg_monthly_pnl = total_combined_pnl / 12
            print(f"   • Average Monthly P&L: ${avg_monthly_pnl:,.2f}")
            
            # Compare to $20k/month target
            target_monthly = 20000
            achievement_pct = (avg_monthly_pnl / target_monthly) * 100
            print(f"   • $20k/Month Target Achievement: {achievement_pct:.1f}%")
        
        return all_results

def main():
    """Main function for full 1-year backtesting"""
    print("🎯 SPY/QQQ SCALPING - FULL 1-YEAR BACKTEST")
    print("Using Complete 99,300 Bars of 1-Minute IBKR Data")
    print("=" * 70)
    print("This will test the ENTIRE 1-year period, not just a sample!")
    print("=" * 70)
    
    backtester = FullYearBacktester()
    results = backtester.run_complete_analysis()
    
    if results:
        print(f"\n💡 STRATEGY ASSESSMENT:")
        print("1. Review the full-year performance metrics")
        print("2. Check monthly consistency")
        print("3. Analyze trade frequency and win rate")
        print("4. Compare against $20k/month target")
        print("5. Optimize parameters if needed")
    else:
        print(f"\n💡 NEXT STEPS:")
        print("1. Review the performance estimations")
        print("2. Consider running full backtest overnight")
        print("3. Optimize strategy based on sample results")
        print("4. Prepare for live paper trading")

if __name__ == "__main__":
    main()