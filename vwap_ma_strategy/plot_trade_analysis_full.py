import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import os
from datetime import datetime, timedelta
import pytz

def load_trade_data(file_path):
    """Load trade data and convert to proper datetime index"""
    if file_path.endswith('.pkl'):
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
    else:
        data = pd.read_csv(file_path)
    
    # Your data has entry_time column but uses RangeIndex
    # Convert entry_time to proper datetime index
    if 'entry_time' in data.columns:
        data['entry_time'] = pd.to_datetime(data['entry_time'])
        # Set entry_time as the index for time-based analysis
        data = data.set_index('entry_time')
    
    return data

def plot_trade_analysis(ticker, data_dir='.'):
    """Plot comprehensive trade analysis"""
    
    # Load trade results - using your actual .pkl files
    trade_file = os.path.join(data_dir, f'trade_data_{ticker}.pkl')
    if not os.path.exists(trade_file):
        print(f"Trade file not found: {trade_file}")
        return
    
    trades_df = load_trade_data(trade_file)
    
    print(f"Analyzing {len(trades_df)} trades for {ticker}")
    print(f"Date range: {trades_df.index.min()} to {trades_df.index.max()}")
    print(f"Index type: {type(trades_df.index)}")
    
    # Create subplots
    fig, axes = plt.subplots(3, 2, figsize=(20, 15))
    fig.suptitle(f'Trade Analysis - {ticker}', fontsize=16)
    
    # Plot 1: Equity Curve
    if 'pnl' in trades_df.columns:
        cumulative_pnl = trades_df['pnl'].cumsum()
        axes[0, 0].plot(trades_df.index, cumulative_pnl, linewidth=2)
        axes[0, 0].set_title('Equity Curve')
        axes[0, 0].set_ylabel('Cumulative PnL ($)')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].axhline(y=0, color='r', linestyle='--', alpha=0.5)
    
    # Plot 2: Daily PnL
    if 'pnl' in trades_df.columns:
        daily_pnl = trades_df['pnl'].resample('D').sum()
        axes[0, 1].bar(daily_pnl.index, daily_pnl.values, alpha=0.7)
        axes[0, 1].set_title('Daily PnL')
        axes[0, 1].set_ylabel('Daily PnL ($)')
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].axhline(y=0, color='r', linestyle='--', alpha=0.5)
    
    # Plot 3: Trade Duration Distribution
    if 'duration_minutes' in trades_df.columns:
        axes[1, 0].hist(trades_df['duration_minutes'], bins=20, alpha=0.7, edgecolor='black')
        axes[1, 0].set_title('Trade Duration Distribution')
        axes[1, 0].set_xlabel('Duration (minutes)')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].grid(True, alpha=0.3)
    
    # Plot 4: PnL Distribution
    if 'pnl' in trades_df.columns:
        axes[1, 1].hist(trades_df['pnl'], bins=30, alpha=0.7, edgecolor='black')
        axes[1, 1].set_title('PnL Distribution')
        axes[1, 1].set_xlabel('PnL ($)')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].axvline(x=0, color='r', linestyle='--', alpha=0.5)
    
    # Plot 5: Simple trade visualization
    sample_trades = trades_df.head(6)
    
    for i, (idx, trade) in enumerate(sample_trades.iterrows()):
        ax = axes[2, 0] if i < 3 else axes[2, 1]
        
        entry_price = trade['entry_price']
        exit_price = trade['exit_price']
        
        # Simple visualization - just show entry and exit
        ax.axhline(y=entry_price, color='g', linestyle='-', alpha=0.7, label='Entry')
        ax.axhline(y=exit_price, color='b' if trade['pnl'] > 0 else 'r', 
                  linestyle='-', alpha=0.7, label='Exit')
        
        # Add synthetic TP/SL for visualization
        tp_price = entry_price * 1.005  # 0.5% take profit
        sl_price = entry_price * 0.995  # 0.5% stop loss
        
        ax.axhline(y=tp_price, color='blue', linestyle='--', alpha=0.5, label='TP')
        ax.axhline(y=sl_price, color='red', linestyle='--', alpha=0.5, label='SL')
        
        ax.set_title(f'Trade {i+1} - PnL: ${trade["pnl"]:.2f}')
        ax.set_ylabel('Price')
        ax.grid(True, alpha=0.3)
        if i == 0:
            ax.legend()
    
    # Plot 6: Win rate by entry hour
    if 'pnl' in trades_df.columns:
        trades_df['hour'] = trades_df.index.hour
        trades_df['win'] = trades_df['pnl'] > 0
        hour_win_rate = trades_df.groupby('hour')['win'].mean() * 100
        
        axes[2, 1].bar(hour_win_rate.index, hour_win_rate.values, alpha=0.7)
        axes[2, 1].set_title('Win Rate by Hour of Day')
        axes[2, 1].set_xlabel('Hour of Day')
        axes[2, 1].set_ylabel('Win Rate (%)')
        axes[2, 1].grid(True, alpha=0.3)
        axes[2, 1].axhline(y=50, color='r', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(f'{ticker}_trade_analysis_comprehensive.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Print summary statistics
    print(f"\n--- {ticker} Trade Analysis Summary ---")
    print(f"Total Trades: {len(trades_df)}")
    
    if 'pnl' in trades_df.columns:
        win_rate = (trades_df['pnl'] > 0).mean() * 100
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Total PnL: ${trades_df['pnl'].sum():.2f}")
        print(f"Average PnL: ${trades_df['pnl'].mean():.2f}")
        
        # Calculate Profit Factor
        winning_trades = trades_df[trades_df['pnl'] > 0]['pnl'].sum()
        losing_trades = abs(trades_df[trades_df['pnl'] < 0]['pnl'].sum())
        profit_factor = winning_trades / losing_trades if losing_trades != 0 else float('inf')
        print(f"Profit Factor: {profit_factor:.2f}")
    
    if 'duration_minutes' in trades_df.columns:
        print(f"Average Duration: {trades_df['duration_minutes'].mean():.1f} minutes")

if __name__ == "__main__":
    # Analyze both tickers
    for ticker in ['SPY', 'QQQ']:
        try:
            print(f"\n{'='*50}")
            print(f"Analyzing {ticker}...")
            print(f"{'='*50}")
            plot_trade_analysis(ticker, '.')
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            import traceback
            traceback.print_exc()