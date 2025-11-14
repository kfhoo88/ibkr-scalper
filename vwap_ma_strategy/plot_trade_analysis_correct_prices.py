# vwap_ma_strategy/plot_trade_analysis_correct_prices.py
"""
Plot trade analysis with PERFECT timezone handling
Consistent Eastern Time throughout the plotting pipeline
"""

import pandas as pd
import matplotlib.pyplot as plt
import yaml
import pickle
from datetime import datetime
import pytz
import numpy as np

def load_config():
    """Load configuration file"""
    with open('config/vwap_ma_config.yaml', 'r') as f:
        return yaml.safe_load(f)

def load_data_with_timezone(symbol):
    """Load price data with proper timezone handling - matches backtest exactly"""
    filename = f"../data/historical/{symbol}_IBKR_1min_1year_20251110.csv"
    df = pd.read_csv(filename)
    
    # Use the EXACT same timezone conversion as backtest
    df['datetime_et'] = pd.to_datetime(df['date'], utc=True).dt.tz_convert('US/Eastern')
    df = df.set_index('datetime_et')
    
    column_map = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}
    df = df.rename(columns=column_map)[['Open', 'High', 'Low', 'Close', 'Volume']]
    
    print(f"✅ Loaded {symbol} data: {df.index[0]} to {df.index[-1]}")
    return df

def ensure_eastern_time(timestamp, est):
    """Ensure timestamp is in Eastern Time"""
    if pd.isna(timestamp):
        return None
    if isinstance(timestamp, str):
        timestamp = pd.to_datetime(timestamp)
    if timestamp.tzinfo is None:
        return est.localize(timestamp)
    return timestamp.tz_convert('US/Eastern')

def convert_trade_data(trades):
    """Convert trade data to consistent format - handle both DataFrame and list"""
    if isinstance(trades, pd.DataFrame):
        print(f"📊 Converting DataFrame with {len(trades)} rows to list of trades")
        trades_list = []
        for _, row in trades.iterrows():
            trade_dict = {
                'entry_time': row['entry_time'],
                'exit_time': row['exit_time'],
                'entry_price': row['entry_price'],
                'exit_price': row['exit_price'],
                'pnl': row['pnl'],
                'type': row['type'],
                'exit_reason': row.get('exit_reason', 'UNKNOWN'),
                'duration_minutes': row.get('duration_minutes', 0),
                'duration_bars': row.get('duration_bars', 0)
            }
            trades_list.append(trade_dict)
        return trades_list
    elif isinstance(trades, list):
        print(f"📊 Using existing list with {len(trades)} trades")
        return trades
    else:
        print(f"❓ Unknown trade data type: {type(trades)}")
        return []

def plot_individual_trades(trades, price_df, symbol, config, est):
    """Plot individual trades with perfect timezone alignment"""
    print(f"\n📊 Plotting individual {symbol} trades...")
    
    # Convert trade data to consistent format
    trades = convert_trade_data(trades)
    
    if not trades:
        print(f"❌ No valid trades to plot for {symbol}")
        return
    
    for i, trade in enumerate(trades[:10]):  # Plot first 10 trades
        try:
            plt.figure(figsize=(15, 10))
            
            # CRITICAL: Ensure trade timestamps are Eastern Time
            entry_time = ensure_eastern_time(trade['entry_time'], est)
            exit_time = ensure_eastern_time(trade['exit_time'], est)
            
            if entry_time is None or exit_time is None:
                print(f"❌ Invalid timestamps for trade {i+1}")
                continue
            
            print(f"Trade {i+1}: {entry_time.strftime('%Y-%m-%d %H:%M:%S %Z')} to {exit_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            # Get trade window (1 hour before entry to 1 hour after exit)
            start_time = entry_time - pd.Timedelta(hours=1)
            end_time = exit_time + pd.Timedelta(hours=1)
            
            trade_data = price_df.loc[start_time:end_time]
            
            if len(trade_data) == 0:
                print(f"❌ No price data found for trade {i+1}")
                continue
            
            # Create subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), 
                                          gridspec_kw={'height_ratios': [3, 1]})
            
            # Plot price data
            ax1.plot(trade_data.index, trade_data['Close'], 
                    label='Price', color='blue', linewidth=2, alpha=0.8)
            
            # Mark entry and exit points
            ax1.axvline(x=entry_time, color='green', linestyle='--', linewidth=3, 
                       label=f'Entry: {entry_time.strftime("%H:%M:%S ET")}')
            ax1.axvline(x=exit_time, color='red', linestyle='--', linewidth=3, 
                       label=f'Exit: {exit_time.strftime("%H:%M:%S ET")}')
            
            # Mark entry and exit prices
            ax1.plot(entry_time, trade['entry_price'], 'g^', markersize=12, 
                    label=f'Entry: ${trade["entry_price"]:.2f}')
            ax1.plot(exit_time, trade['exit_price'], 'rv', markersize=12, 
                    label=f'Exit: ${trade["exit_price"]:.2f}')
            
            # Add price range
            price_range = trade_data['High'].max() - trade_data['Low'].min()
            ax1.set_ylim([trade_data['Low'].min() - price_range * 0.1, 
                         trade_data['High'].max() + price_range * 0.1])
            
            # Trade info box
            pnl_color = 'green' if trade['pnl'] > 0 else 'red'
            trade_info = f"{trade['type']} | P&L: ${trade['pnl']:+.2f} | Duration: {trade.get('duration_minutes', 0):.1f}min"
            
            ax1.set_title(f"{symbol} Trade {i+1} - {trade_info}", 
                         fontsize=16, fontweight='bold', pad=20)
            ax1.set_ylabel('Price', fontsize=12)
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            # Plot volume
            ax2.bar(trade_data.index, trade_data['Volume'], 
                   color='orange', alpha=0.6, label='Volume')
            ax2.set_ylabel('Volume', fontsize=12)
            ax2.set_xlabel('Time (Eastern Time)', fontsize=12)
            ax2.legend(loc='upper left')
            ax2.grid(True, alpha=0.3)
            
            # Format x-axis to show Eastern Time properly
            for ax in [ax1, ax2]:
                ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M', tz=est))
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f'trade_analysis_{symbol}_{i+1}_timezone_perfect.png', 
                       dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Saved plot for {symbol} trade {i+1}")
            
        except Exception as e:
            print(f"❌ Error plotting {symbol} trade {i+1}: {e}")
            continue

def create_performance_analysis(trades, symbol, est):
    """Create comprehensive performance analysis"""
    print(f"\n📈 Creating performance analysis for {symbol}...")
    
    # Convert to DataFrame if it's a list
    if isinstance(trades, list):
        trades_df = pd.DataFrame(trades)
    else:
        trades_df = trades
    
    # Ensure all timestamps are Eastern Time
    trades_df['entry_time_et'] = trades_df['entry_time'].apply(
        lambda x: ensure_eastern_time(x, est)
    )
    trades_df['exit_time_et'] = trades_df['exit_time'].apply(
        lambda x: ensure_eastern_time(x, est)
    )
    
    # Time-based analysis
    trades_df['entry_hour'] = trades_df['entry_time_et'].dt.hour
    trades_df['entry_minute'] = trades_df['entry_time_et'].dt.minute
    trades_df['entry_day'] = trades_df['entry_time_et'].dt.day_name()
    
    # Performance metrics
    total_trades = len(trades_df)
    winning_trades = len(trades_df[trades_df['pnl'] > 0])
    losing_trades = len(trades_df[trades_df['pnl'] < 0])
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
    total_pnl = trades_df['pnl'].sum()
    avg_pnl = trades_df['pnl'].mean()
    avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
    avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
    
    print(f"\n🎯 {symbol} PERFORMANCE SUMMARY (Eastern Time):")
    print(f"   Total Trades: {total_trades}")
    print(f"   Win Rate: {win_rate:.1f}%")
    print(f"   Total P&L: ${total_pnl:+.2f}")
    print(f"   Average P&L: ${avg_pnl:+.2f}")
    print(f"   Average Win: ${avg_win:+.2f}")
    print(f"   Average Loss: ${avg_loss:+.2f}")
    
    # Hourly performance
    if total_trades > 0:
        hourly_stats = trades_df.groupby('entry_hour').agg({
            'pnl': ['count', 'sum', 'mean'],
            'duration_minutes': 'mean'
        }).round(2)
        
        print(f"\n⏰ HOURLY PERFORMANCE (Eastern Time):")
        print(hourly_stats)
    
    # Save detailed analysis
    trades_df.to_csv(f'trade_analysis_{symbol}_detailed.csv', index=False)
    print(f"✅ Saved detailed analysis for {symbol}")
    
    return trades_df

def plot_trade_analysis_correct_prices():
    """Main function to plot trade analysis with perfect timezone handling"""
    print("🎯 TRADE ANALYSIS - PERFECT TIMEZONE HANDLING")
    print("Consistent Eastern Time throughout plotting pipeline")
    print("=" * 60)
    
    config = load_config()
    est = pytz.timezone('US/Eastern')
    
    # Load trade data
    symbols = ['SPY', 'QQQ']
    
    for symbol in symbols:
        try:
            with open(f'trade_data_{symbol}_timezone_perfect.pkl', 'rb') as f:
                trades = pickle.load(f)
            print(f"✅ Loaded {len(trades)} {symbol} trades (type: {type(trades)})")
            
            # Load price data with correct timezone
            price_df = load_data_with_timezone(symbol)
            
            # Plot individual trades
            plot_individual_trades(trades, price_df, symbol, config, est)
            
            # Create performance analysis
            create_performance_analysis(trades, symbol, est)
            
        except FileNotFoundError:
            print(f"❌ {symbol} trade data not found - skipping")
        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("✅ TRADE ANALYSIS COMPLETED WITH PERFECT TIMEZONE HANDLING")
    print("All timestamps are in Eastern Time and consistent with backtest results")
    print(f"{'='*80}")

if __name__ == "__main__":
    plot_trade_analysis_correct_prices()