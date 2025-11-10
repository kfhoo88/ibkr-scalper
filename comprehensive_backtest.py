# comprehensive_backtest.py
import pandas as pd
import numpy as np
import os
from datetime import datetime
from core.backtester import Backtester
from core.options_scalper import OptionsScalper
import matplotlib.pyplot as plt
import seaborn as sns

class ComprehensiveBacktest:
    def __init__(self):
        self.data_dir = 'data/historical'
        self.results_dir = 'results'
        os.makedirs(self.results_dir, exist_ok=True)
        
    def load_1min_data(self, symbol):
        """Load the 1-minute data we just downloaded"""
        files = [f for f in os.listdir(self.data_dir) if f.startswith(symbol) and '1min_1year' in f]
        
        if not files:
            print(f"❌ No 1-year 1-min data found for {symbol}")
            return None
        
        latest_file = sorted(files)[-1]  # Get most recent file
        file_path = os.path.join(self.data_dir, latest_file)
        
        print(f"📊 Loading {symbol} data: {latest_file}")
        data = pd.read_csv(file_path)
        data['date'] = pd.to_datetime(data['date'])
        data.set_index('date', inplace=True)
        
        print(f"   • Loaded {len(data):,} bars")
        print(f"   • Period: {data.index.min()} to {data.index.max()}")
        
        return data
    
    def run_strategy_backtest(self, symbol, data):
        """Run our HA+MA scalping strategy on the 1-min data"""
        print(f"\n🎯 RUNNING SCALPING STRATEGY ON {symbol}")
        print("=" * 50)
        
        # Initialize strategy and backtester
        scalper = OptionsScalper()
        backtester = Backtester(scalper)
        
        # Run backtest
        results = backtester.run(data)
        
        return results
    
    def analyze_results(self, results, symbol):
        """Comprehensive analysis of backtest results"""
        print(f"\n📊 ANALYZING {symbol} BACKTEST RESULTS")
        print("=" * 50)
        
        trades = results.get('trades', [])
        
        if not trades:
            print("❌ No trades generated")
            return None
        
        # Convert trades to DataFrame for analysis
        trades_df = pd.DataFrame(trades)
        
        # Basic metrics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # P&L analysis
        total_pnl = trades_df['pnl'].sum()
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        profit_factor = abs(avg_win * winning_trades) / abs(avg_loss * losing_trades) if losing_trades > 0 else float('inf')
        
        # Trade duration analysis
        trades_df['duration'] = pd.to_timedelta(trades_df['exit_time'] - trades_df['entry_time'])
        avg_duration = trades_df['duration'].mean()
        
        print(f"📈 PERFORMANCE SUMMARY:")
        print(f"   • Total Trades: {total_trades}")
        print(f"   • Win Rate: {win_rate:.1%}")
        print(f"   • Total P&L: ${total_pnl:,.2f}")
        print(f"   • Average Win: ${avg_win:.2f}")
        print(f"   • Average Loss: ${avg_loss:.2f}")
        print(f"   • Profit Factor: {profit_factor:.2f}")
        print(f"   • Avg Trade Duration: {avg_duration}")
        
        # Monthly breakdown
        trades_df['month'] = trades_df['entry_time'].dt.to_period('M')
        monthly_pnl = trades_df.groupby('month')['pnl'].sum()
        
        print(f"\n📅 MONTHLY PERFORMANCE:")
        for month, pnl in monthly_pnl.items():
            print(f"   • {month}: ${pnl:,.2f}")
        
        return {
            'symbol': symbol,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'avg_duration': avg_duration,
            'trades_df': trades_df,
            'monthly_pnl': monthly_pnl
        }
    
    def create_visualizations(self, analysis, symbol):
        """Create performance visualizations"""
        print(f"\n📊 CREATING VISUALIZATIONS FOR {symbol}")
        
        trades_df = analysis['trades_df']
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'Scalping Strategy Performance - {symbol}\n'
                    f'Win Rate: {analysis["win_rate"]:.1%} | Total P&L: ${analysis["total_pnl"]:,.2f}', 
                    fontsize=16, fontweight='bold')
        
        # 1. P&L Distribution
        axes[0, 0].hist(trades_df['pnl'], bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0, 0].axvline(0, color='red', linestyle='--', linewidth=1)
        axes[0, 0].set_title('P&L Distribution')
        axes[0, 0].set_xlabel('P&L per Trade ($)')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Cumulative P&L
        cumulative_pnl = trades_df['pnl'].cumsum()
        axes[0, 1].plot(cumulative_pnl, color='green', linewidth=2)
        axes[0, 1].set_title('Cumulative P&L')
        axes[0, 1].set_xlabel('Trade Number')
        axes[0, 1].set_ylabel('Cumulative P&L ($)')
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].axhline(0, color='red', linestyle='--', linewidth=1)
        
        # 3. Monthly Performance
        analysis['monthly_pnl'].plot(kind='bar', ax=axes[1, 0], color='lightblue')
        axes[1, 0].set_title('Monthly P&L')
        axes[1, 0].set_xlabel('Month')
        axes[1, 0].set_ylabel('P&L ($)')
        axes[1, 0].tick_params(axis='x', rotation=45)
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Win/Loss Analysis
        win_loss_data = [analysis['avg_win'], analysis['avg_loss']]
        win_loss_labels = [f'Winners\n({analysis["win_rate"]:.1%})', f'Losers\n({1-analysis["win_rate"]:.1%})']
        colors = ['green' if x > 0 else 'red' for x in win_loss_data]
        axes[1, 1].bar(win_loss_labels, win_loss_data, color=colors, alpha=0.7)
        axes[1, 1].set_title('Average Win/Loss')
        axes[1, 1].set_ylabel('Average P&L ($)')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save the figure
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        plot_filename = f"{self.results_dir}/{symbol}_backtest_results_{timestamp}.png"
        plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"   💾 Saved visualization: {plot_filename}")
    
    def save_detailed_results(self, analysis, symbol):
        """Save detailed results to CSV"""
        trades_df = analysis['trades_df']
        
        # Save trades to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        trades_filename = f"{self.results_dir}/{symbol}_detailed_trades_{timestamp}.csv"
        trades_df.to_csv(trades_filename, index=False)
        
        # Save summary statistics
        summary = {
            'Symbol': symbol,
            'Total Trades': analysis['total_trades'],
            'Win Rate': f"{analysis['win_rate']:.1%}",
            'Total P&L': f"${analysis['total_pnl']:,.2f}",
            'Average Win': f"${analysis['avg_win']:.2f}",
            'Average Loss': f"${analysis['avg_loss']:.2f}",
            'Profit Factor': f"{analysis['profit_factor']:.2f}",
            'Average Duration': str(analysis['avg_duration']),
            'Backtest Period': f"{trades_df['entry_time'].min()} to {trades_df['entry_time'].max()}",
            'Data Points': f"{len(trades_df):,}"
        }
        
        summary_df = pd.DataFrame([summary])
        summary_filename = f"{self.results_dir}/{symbol}_summary_{timestamp}.csv"
        summary_df.to_csv(summary_filename, index=False)
        
        print(f"   💾 Saved trades: {trades_filename}")
        print(f"   💾 Saved summary: {summary_filename}")
        
        return summary
    
    def run_comprehensive_analysis(self):
        """Run complete backtesting analysis on both symbols"""
        print("🚀 COMPREHENSIVE SCALPING STRATEGY BACKTEST")
        print("=" * 60)
        print("Using 1-Year of 1-Minute Data for Robust Testing")
        print("=" * 60)
        
        symbols = ['SPY', 'QQQ']
        all_results = {}
        
        for symbol in symbols:
            print(f"\n{'='*60}")
            print(f"ANALYZING: {symbol}")
            print(f"{'='*60}")
            
            # Load data
            data = self.load_1min_data(symbol)
            if data is None:
                continue
            
            # Run backtest
            results = self.run_strategy_backtest(symbol, data)
            
            # Analyze results
            analysis = self.analyze_results(results, symbol)
            if analysis is None:
                continue
            
            # Create visualizations
            self.create_visualizations(analysis, symbol)
            
            # Save detailed results
            self.save_detailed_results(analysis, symbol)
            
            all_results[symbol] = analysis
        
        # Print final comparison
        if len(all_results) > 1:
            self.print_comparison(all_results)
        
        return all_results
    
    def print_comparison(self, all_results):
        """Print comparison between SPY and QQQ results"""
        print(f"\n{'='*60}")
        print("📊 SPY vs QQQ PERFORMANCE COMPARISON")
        print(f"{'='*60}")
        
        comparison_data = []
        
        for symbol, analysis in all_results.items():
            comparison_data.append({
                'Symbol': symbol,
                'Total Trades': analysis['total_trades'],
                'Win Rate': f"{analysis['win_rate']:.1%}",
                'Total P&L': f"${analysis['total_pnl']:,.2f}",
                'Avg Win': f"${analysis['avg_win']:.2f}",
                'Avg Loss': f"${analysis['avg_loss']:.2f}",
                'Profit Factor': f"{analysis['profit_factor']:.2f}",
                'Avg Duration': str(analysis['avg_duration']).split('.')[0]  # Remove microseconds
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        print(comparison_df.to_string(index=False))
        
        # Determine which symbol performed better
        best_symbol = max(all_results.items(), key=lambda x: x[1]['total_pnl'])
        print(f"\n🎯 BEST PERFORMER: {best_symbol[0]} (P&L: ${best_symbol[1]['total_pnl']:,.2f})")

def main():
    backtester = ComprehensiveBacktest()
    results = backtester.run_comprehensive_analysis()
    
    print(f"\n🎉 BACKTESTING COMPLETE!")
    print("=" * 60)
    print("Next steps:")
    print("1. Review the performance visualizations in /results/")
    print("2. Analyze trade details in the CSV files")
    print("3. Optimize strategy parameters if needed")
    print("4. Prepare for live paper trading")

if __name__ == "__main__":
    main()
