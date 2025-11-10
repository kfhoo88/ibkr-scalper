# run_full_year_proven.py
import pandas as pd
import os
import sys
from datetime import datetime
import time

sys.path.append('core')

def run_full_year_backtest():
    """Run proven strategy on full 1-year IBKR data"""
    try:
        from backtester_proven import ProvenBacktester
    except ImportError:
        print("❌ Could not import ProvenBacktester")
        return
    
    print("🚀 PROVEN STRATEGY - FULL 1-YEAR BACKTEST")
    print("Using 99,300 bars of real 1-minute IBKR data")
    print("=" * 70)
    
    symbols = ['SPY', 'QQQ']
    all_results = {}
    
    for symbol in symbols:
        print(f"\n{'='*70}")
        print(f"PROCESSING: {symbol}")
        print(f"{'='*70}")
        
        # Load the full 1-year data
        data_file = f"{symbol}_IBKR_1min_1year_20251110.csv"
        file_path = os.path.join('data/historical', data_file)
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {data_file}")
            continue
        
        print(f"📥 Loading: {data_file}")
        start_load = time.time()
        
        # Load with optimized settings
        data = pd.read_csv(file_path, parse_dates=['date'], infer_datetime_format=True)
        data.set_index('date', inplace=True)
        
        load_time = time.time() - start_load
        print(f"   ✅ Loaded {len(data):,} bars in {load_time:.1f} seconds")
        print(f"   📅 Period: {data.index[0]} to {data.index[-1]}")
        
        # Standardize columns
        column_map = {
            'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume',
            'OPEN': 'open', 'HIGH': 'high', 'LOW': 'low', 'CLOSE': 'close', 'VOLUME': 'volume'
        }
        
        for old_col, new_col in column_map.items():
            if old_col in data.columns and new_col not in data.columns:
                data[new_col] = data[old_col]
        
        # Ensure required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in data.columns:
                print(f"❌ Missing column: {col}")
                continue
        
        print(f"   📊 Data ready: {data.shape}")
        print(f"   ⏰ Estimated time: 15-30 minutes")
        
        # Run backtest on FULL data (no sampling)
        backtester = ProvenBacktester("config/scalping_config_proven.yaml")
        
        print(f"\n   🔄 STARTING FULL 1-YEAR BACKTEST...")
        start_test = time.time()
        
        try:
            results = backtester.backtest_proven(data, symbol, sample_size=len(data))
            test_time = (time.time() - start_test) / 60  # minutes
            
            if results:
                all_results[symbol] = results
                print(f"   ✅ Completed in {test_time:.1f} minutes")
                
                # Quick summary
                trades = results['total_trades']
                win_rate = results['win_rate']
                pnl = results['total_pnl']
                
                print(f"   📈 {symbol} Results: {trades:,} trades, {win_rate:.1%} win rate, ${pnl:,.2f} P&L")
                
            else:
                print(f"   ❌ Backtest failed for {symbol}")
                
        except Exception as e:
            print(f"   ❌ Error during backtest: {e}")
        
        # Small delay between symbols
        time.sleep(2)
    
    # Final comprehensive analysis
    if all_results:
        print(f"\n{'='*70}")
        print("🎉 FULL 1-YEAR BACKTESTING COMPLETE!")
        print(f"{'='*70}")
        
        total_trades = sum(r['total_trades'] for r in all_results.values())
        total_pnl = sum(r['total_pnl'] for r in all_results.values())
        avg_win_rate = sum(r['win_rate'] for r in all_results.values()) / len(all_results)
        
        print(f"📊 COMBINED 1-YEAR PERFORMANCE:")
        print(f"   • Total Trades: {total_trades:,}")
        print(f"   • Average Win Rate: {avg_win_rate:.1%}")
        print(f"   • Total P&L: ${total_pnl:,.2f}")
        print(f"   • Annual Return: {(total_pnl / 20000):.2%}")  # $20k initial capital
        
        # Monthly breakdown
        monthly_avg = total_pnl / 12
        daily_avg = total_pnl / 252  # Trading days
        
        print(f"\n   📅 BREAKDOWN:")
        print(f"      • Monthly Average: ${monthly_avg:,.2f}")
        print(f"      • Daily Average: ${daily_avg:,.2f}")
        
        # Target achievement
        target_monthly = 20000
        achievement = (monthly_avg / target_monthly) * 100
        print(f"      • $20k/Month Target: {achievement:.1f}%")
        
        # Strategy assessment
        print(f"\n   🎯 STRATEGY ASSESSMENT:")
        if monthly_avg >= target_monthly:
            print(f"      ✅ EXCELLENT! Meets $20k/month target!")
        elif monthly_avg >= 10000:
            print(f"      📊 GOOD! Strong potential ({monthly_avg:,.0f}/month)")
        elif monthly_avg >= 5000:
            print(f"      🔧 MODERATE! Needs optimization ({monthly_avg:,.0f}/month)")
        else:
            print(f"      ⚠️  NEEDS WORK! Review strategy ({monthly_avg:,.0f}/month)")
    
    return all_results

def main():
    """Main function for full 1-year backtesting"""
    print("🎯 SPY/QQQ SCALPING - PROVEN STRATEGY")
    print("FULL 1-YEAR VALIDATION WITH REAL IBKR DATA")
    print("=" * 70)
    print("This will test the complete 99,300 bars per symbol")
    print("Using the proven MA9/MA14 + 1_OTM strategy")
    print("=" * 70)
    
    # Confirm with user
    try:
        response = input("\nRun full 1-year backtest? This will take 30-60 minutes. (y/n): ").strip().lower()
        if response != 'y':
            print("⏩ Skipping full backtest")
            return
    except:
        print("⏩ Auto-continuing with full backtest")
    
    start_time = datetime.now()
    print(f"\n🕐 Started at: {start_time.strftime('%H:%M:%S')}")
    
    results = run_full_year_backtest()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() / 60
    
    print(f"\n🕐 Completed at: {end_time.strftime('%H:%M:%S')}")
    print(f"⏱️  Total duration: {duration:.1f} minutes")
    
    if results:
        print(f"\n💡 NEXT STEPS:")
        print("1. Review the 1-year performance metrics")
        print("2. Check if strategy meets your expectations")
        print("3. Consider live paper trading if results are good")
        print("4. Optimize parameters if needed")
    else:
        print(f"\n❌ Backtesting failed - check error messages above")

if __name__ == "__main__":
    main()