# main_with_progress.py
import pandas as pd
import numpy as np
import os
import sys
import time
from datetime import datetime
from tqdm import tqdm  # Progress bar library

# Add core to path
sys.path.append('core')

try:
    from backtester_enhanced import EnhancedOptionsBacktester
    print("✅ Successfully imported EnhancedOptionsBacktester")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class ProgressBacktester(EnhancedOptionsBacktester):
    """Enhanced backtester with progress tracking"""
    
    def backtest_with_progress(self, data, symbol="SPY"):
        """Backtest with progress tracking"""
        print(f"🚀 ENHANCED BACKTEST: {symbol} Options Scalping")
        
        # Prepare the data
        prepared_data = self.prepare_data(data)
        print(f"📊 Data: {len(prepared_data):,} bars | Period: {prepared_data.index[0]} to {prepared_data.index[-1]}")
        print("=" * 60)
        
        portfolio_value = self.config['backtesting']['initial_capital']
        initial_capital = portfolio_value
        max_position_value = self.config['trading']['max_position_value']
        
        trades = []
        equity_curve = []
        
        # Create progress bar
        total_bars = len(prepared_data)
        progress_bar = tqdm(total=total_bars-20, desc=f"Backtesting {symbol}", unit="bar")
        
        # Main backtest loop with progress
        for i in range(20, len(prepared_data)):
            current_time = prepared_data.index[i]
            
            # Generate signal
            signal = self.generate_trade_signal(prepared_data, i)
            
            if signal and signal['action'] in ['BUY_CALL', 'BUY_PUT']:
                # Check if we have enough capital
                if portfolio_value >= max_position_value:
                    # Simulate trade
                    entry_price = signal['price']
                    
                    # Simple exit: after 5 bars
                    exit_bars = min(5, len(prepared_data) - i - 1)
                    if exit_bars > 0:
                        exit_data = prepared_data.iloc[i + exit_bars]
                        exit_price = exit_data['close']
                        exit_time = prepared_data.index[i + exit_bars]
                        
                        # Calculate P&L
                        if signal['action'] == 'BUY_CALL':
                            pnl_pct = (exit_price - entry_price) / entry_price
                        else:  # BUY_PUT
                            pnl_pct = (entry_price - exit_price) / entry_price
                        
                        # Apply position size and commission
                        pnl = max_position_value * pnl_pct
                        pnl -= 0.65  # Commission
                        
                        # Update portfolio
                        portfolio_value += pnl
                        
                        # Record trade
                        trade = {
                            'entry_time': current_time,
                            'exit_time': exit_time,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'direction': signal['action'],
                            'pnl': pnl,
                            'portfolio_value': portfolio_value,
                            'symbol': symbol
                        }
                        trades.append(trade)
            
            # Update progress bar
            progress_bar.update(1)
            progress_bar.set_postfix({
                'Trades': len(trades),
                'Equity': f"${portfolio_value:,.0f}"
            })
            
            # Record equity curve
            equity_curve.append({
                'timestamp': current_time,
                'equity': portfolio_value
            })
        
        progress_bar.close()
        
        # Calculate results
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = len([t for t in trades if t['pnl'] < 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        total_pnl = sum(t['pnl'] for t in trades)
        total_return = (portfolio_value - initial_capital) / initial_capital
        
        print(f"✅ BACKTEST COMPLETE")
        print(f"📈 Total Trades: {total_trades}")
        print(f"🎯 Win Rate: {win_rate:.1%}")
        print(f"💰 Total P&L: ${total_pnl:,.2f}")
        print(f"📊 Total Return: {total_return:.2%}")
        print(f"💵 Final Capital: ${portfolio_value:,.2f}")
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_return': total_return,
            'final_capital': portfolio_value,
            'trades': trades,
            'equity_curve': equity_curve
        }

class ProgressTrackingBacktester:
    def __init__(self):
        self.data_dir = 'data/historical'
        self.results_dir = 'results'
        os.makedirs(self.results_dir, exist_ok=True)
        
    def load_data(self, symbol):
        """Load data with proper timezone handling"""
        print(f"📥 LOADING {symbol} DATA...")
        
        files = [f for f in os.listdir(self.data_dir) 
                if f.startswith(symbol) and '1min' in f]
        
        if not files:
            print(f"❌ No data found for {symbol}")
            return None
        
        # Use the largest file
        file_sizes = [(f, os.path.getsize(os.path.join(self.data_dir, f))) for f in files]
        largest_file = max(file_sizes, key=lambda x: x[1])[0]
        file_path = os.path.join(self.data_dir, largest_file)
        
        print(f"   File: {largest_file}")
        
        try:
            # Load with UTC timezone to avoid warnings
            data = pd.read_csv(file_path)
            print(f"   ✅ Loaded {len(data):,} rows")
            
            # Handle date column with UTC
            date_col = 'date' if 'date' in data.columns else ('Date' if 'Date' in data.columns else 'Datetime')
            data[date_col] = pd.to_datetime(data[date_col], utc=True)
            data.set_index(date_col, inplace=True)
            
            return data
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return None
    
    def run_with_progress(self, symbol, use_full_data=True):
        """Run backtest with progress tracking"""
        print(f"\n🎯 BACKTEST: {symbol}")
        print("=" * 50)
        
        data = self.load_data(symbol)
        if data is None:
            return None
        
        if not use_full_data:
            test_size = min(20000, len(data))  # Smaller for quick testing
            data = data.iloc[-test_size:]
            print(f"   ⚡ Using {len(data):,} bars for quick test")
        else:
            print(f"   🚀 USING FULL {len(data):,} BARS")
            print(f"   ⏰ Estimated time: 5-15 minutes")
        
        backtester = ProgressBacktester()
        
        print(f"   🔄 Starting backtest with progress tracking...")
        start_time = time.time()
        
        try:
            results = backtester.backtest_with_progress(data, symbol=symbol)
            end_time = time.time()
            duration = (end_time - start_time) / 60
            
            print(f"   ✅ Completed in {duration:.1f} minutes")
            return results
            
        except Exception as e:
            print(f"❌ Backtest failed: {e}")
            return None
    
    def display_results(self, results, symbol):
        """Display comprehensive results"""
        if not results:
            return
        
        print(f"\n📊 DETAILED RESULTS: {symbol}")
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
        
        print(f"   📈 Total Trades: {total_trades:,}")
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
            profit_factor = abs(sum(p for p in pnls if p > 0)) / abs(sum(p for p in pnls if p < 0)) if losing_trades > 0 else float('inf')
            
            print(f"\n   📊 ADVANCED METRICS:")
            print(f"      • Average Trade: ${avg_trade:.2f}")
            print(f"      • Best Trade: ${best_trade:.2f}")
            print(f"      • Worst Trade: ${worst_trade:.2f}")
            print(f"      • Profit Factor: {profit_factor:.2f}")
            
            # Risk metrics
            if len(pnls) > 1:
                sharpe = np.mean(pnls) / np.std(pnls) if np.std(pnls) > 0 else 0
                print(f"      • Sharpe Ratio: {sharpe:.2f}")
    
    def run_progress_analysis(self):
        """Run analysis with progress tracking"""
        print("🚀 SPY/QQQ SCALPING - PROGRESS TRACKING")
        print("Windows 10 + Python 3.13 + Real-time Progress")
        print("=" * 70)
        
        # Install tqdm if not available
        try:
            import tqdm
        except ImportError:
            print("📦 Installing progress bar library...")
            os.system("pip install tqdm")
            import tqdm
        
        # Get user preference
        try:
            print(f"\n🎯 BACKTEST OPTIONS:")
            print("   1. Quick test (~20,000 bars - ~2-5 minutes)")
            print("   2. Full dataset (~99,300 bars - ~10-20 minutes)")
            
            choice = input("\n   Choose option (1 or 2): ").strip()
            use_full_data = (choice == "2")
            
            if use_full_data:
                print(f"   🚀 SELECTED: FULL DATASET")
                print(f"   ⚠️  This will take a while - progress bar will show status")
            else:
                print(f"   ⚡ SELECTED: QUICK TEST")
                
        except:
            use_full_data = False
            print(f"   ⚡ DEFAULT: QUICK TEST")
        
        symbols = ['SPY', 'QQQ']
        all_results = {}
        
        for symbol in symbols:
            print(f"\n{'='*70}")
            print(f"PROCESSING: {symbol}")
            print(f"{'='*70}")
            
            results = self.run_with_progress(symbol, use_full_data)
            if results:
                all_results[symbol] = results
                self.display_results(results, symbol)
            
            print(f"\n💤 Pausing for 2 seconds...")
            time.sleep(2)
        
        # Final summary
        if all_results:
            print(f"\n🎉 COMPLETE 1-YEAR ANALYSIS FINISHED!")
            print("=" * 70)
            
            total_pnl = sum(r['total_pnl'] for r in all_results.values())
            total_trades = sum(r['total_trades'] for r in all_results.values())
            total_return = total_pnl / 20000  # $20k initial capital across both symbols
            
            print(f"📊 COMBINED 1-YEAR PERFORMANCE:")
            print(f"   • Total Trades: {total_trades:,}")
            print(f"   • Total P&L: ${total_pnl:,.2f}")
            print(f"   • Annual Return: {total_return:.2%}")
            
            if use_full_data:
                monthly_avg = total_pnl / 12
                daily_avg = total_pnl / 252  # Trading days
                target_achievement = (monthly_avg / 20000) * 100
                
                print(f"\n   📅 BREAKDOWN:")
                print(f"      • Monthly Average: ${monthly_avg:,.2f}")
                print(f"      • Daily Average: ${daily_avg:,.2f}")
                print(f"      • $20k/Month Target: {target_achievement:.1f}%")
        
        return all_results

def main():
    """Main function with progress tracking"""
    print("🎯 SPY/QQQ OPTIONS SCALPING - PROGRESS TRACKING")
    print("See real-time progress as it processes 99,300 bars!")
    print("=" * 70)
    
    backtester = ProgressTrackingBacktester()
    results = backtester.run_progress_analysis()
    
    print(f"\n💡 STRATEGY ASSESSMENT:")
    if results:
        total_pnl = sum(r['total_pnl'] for r in results.values())
        monthly_avg = total_pnl / 12
        
        if monthly_avg >= 20000:
            print("🎉 EXCELLENT! Strategy meets $20k/month target!")
        elif monthly_avg >= 10000:
            print("✅ GOOD! Strategy shows strong potential")
        elif monthly_avg >= 5000:
            print("📊 MODERATE! Strategy needs optimization")
        else:
            print("🔧 NEEDS WORK! Review and optimize strategy")
        
        print(f"\nNext: Optimize parameters in config/scalping_config.yaml")
    else:
        print("1. Check if backtest completed successfully")
        print("2. Review error messages above")
        print("3. Try with smaller dataset first")

if __name__ == "__main__":
    main()