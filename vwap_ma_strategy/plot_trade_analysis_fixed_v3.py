# vwap_ma_strategy/plot_trade_analysis_fixed_v3.py
"""
Fixed Trade Visualization - Handle mixed timezone timestamps
"""

import pandas as pd
import numpy as np
import yaml
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os
import sys

sys.path.append('..')

class TradeVisualizerFixedV3:
    def __init__(self, config):
        self.config = config['reversal_strategy']
        self.ema_length = self.config['ema_length']
        self.hl_backcandles = self.config['hl_backcandles']
    
    def load_trade_data(self, symbol):
        """Load saved trade data and handle mixed timezones"""
        filename = f'trade_data_{symbol}.pkl'
        try:
            # Load with explicit UTC conversion to handle mixed timezones
            trades_df = pd.read_pickle(filename)
            print(f"✅ Loaded {len(trades_df)} {symbol} trades")
            
            # Convert to UTC first, then remove timezone
            trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'], utc=True).dt.tz_localize(None)
            trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'], utc=True).dt.tz_localize(None)
            
            print(f"   First entry: {trades_df['entry_time'].iloc[0]}")
            print(f"   First exit: {trades_df['exit_time'].iloc[0]}")
            
            return trades_df
        except FileNotFoundError:
            print(f"❌ Trade data file not found: {filename}")
            return None
        except Exception as e:
            print(f"❌ Error loading trade data: {e}")
            # Try alternative approach
            return self.load_trade_data_alternative(symbol)
    
    def load_trade_data_alternative(self, symbol):
        """Alternative method to load trade data"""
        filename = f'trade_data_{symbol}.pkl'
        try:
            trades_df = pd.read_pickle(filename)
            print(f"✅ Loaded {len(trades_df)} {symbol} trades (alternative method)")
            
            # Convert each timestamp individually
            entry_times = []
            exit_times = []
            
            for idx, row in trades_df.iterrows():
                try:
                    entry_time = pd.to_datetime(row['entry_time'], utc=True).tz_localize(None)
                    exit_time = pd.to_datetime(row['exit_time'], utc=True).tz_localize(None)
                    entry_times.append(entry_time)
                    exit_times.append(exit_time)
                except:
                    # If conversion fails, use original
                    entry_times.append(row['entry_time'])
                    exit_times.append(row['exit_time'])
            
            trades_df['entry_time'] = entry_times
            trades_df['exit_time'] = exit_times
            
            return trades_df
        except Exception as e:
            print(f"❌ Alternative method also failed: {e}")
            return None
    
    def load_price_data(self, symbol):
        """Load historical price data with proper timezone handling"""
        filename = f"../data/historical/{symbol}_IBKR_1min_1year_20251110.csv"
        try:
            df = pd.read_csv(filename)
            
            # Handle timezone properly - convert to UTC then remove timezone
            df['date'] = pd.to_datetime(df['date'], utc=True).dt.tz_localize(None)
            df = df.set_index('date')
            
            column_map = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}
            df = df.rename(columns=column_map)[['Open', 'High', 'Low', 'Close', 'Volume']]
            
            print(f"✅ Loaded {len(df)} price bars for {symbol}")
            print(f"   Date range: {df.index.min()} to {df.index.max()}")
            
            return df
        except FileNotFoundError:
            print(f"❌ Price data file not found: {filename}")
            return None
    
    def calculate_indicators(self, df):
        """Calculate EMA and swing points for plotting"""
        df = df.copy()
        df['EMA'] = df['Close'].ewm(span=self.ema_length, adjust=False).mean()
        df['swing_low'] = df['Low'].rolling(window=self.hl_backcandles, center=False).min()
        df['swing_high'] = df['High'].rolling(window=self.hl_backcandles, center=False).max()
        return df
    
    def find_nearest_price_data(self, trade_time, price_df, window_hours=6):
        """Find the actual price data around the trade time"""
        start_time = trade_time - timedelta(hours=window_hours)
        end_time = trade_time + timedelta(hours=window_hours)
        
        mask = (price_df.index >= start_time) & (price_df.index <= end_time)
        plot_df = price_df[mask].copy()
        
        if len(plot_df) == 0:
            # Try to find the closest available data
            time_diff = abs(price_df.index - trade_time)
            closest_idx = time_diff.argmin()
            closest_time = price_df.index[closest_idx]
            print(f"   ⚠️ No data at exact trade time {trade_time}, using closest: {closest_time}")
            
            # Get data around the closest time
            start_time = closest_time - timedelta(hours=window_hours)
            end_time = closest_time + timedelta(hours=window_hours)
            mask = (price_df.index >= start_time) & (price_df.index <= end_time)
            plot_df = price_df[mask].copy()
        
        return plot_df
    
    def plot_trade_fixed(self, trade, price_df, symbol, category, rank):
        """Plot individual trade with proper time alignment"""
        
        # Get trade timestamps
        entry_time = trade['entry_time']
        exit_time = trade['exit_time']
        
        print(f"   Trade {rank}: Entry={entry_time}, Exit={exit_time}")
        
        # Find price data around the trade
        plot_df = self.find_nearest_price_data(entry_time, price_df, window_hours=6)
        
        if len(plot_df) == 0:
            print(f"   ❌ No price data found for trade {rank}")
            return None
        
        print(f"   Price data: {len(plot_df)} bars from {plot_df.index.min()} to {plot_df.index.max()}")
        
        # Calculate indicators
        plot_df = self.calculate_indicators(plot_df)
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=(
                f"{symbol} - {category} #{rank} | {trade['type']} | P&L: ${trade['pnl']:+.2f}",
                "Volume"
            ),
            row_heights=[0.7, 0.3]
        )
        
        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=plot_df.index,
                open=plot_df['Open'],
                high=plot_df['High'],
                low=plot_df['Low'],
                close=plot_df['Close'],
                name='Price'
            ),
            row=1, col=1
        )
        
        # Add EMA
        fig.add_trace(
            go.Scatter(
                x=plot_df.index,
                y=plot_df['EMA'],
                line=dict(color='orange', width=2),
                name=f'EMA {self.ema_length}'
            ),
            row=1, col=1
        )
        
        # Add entry point - find the closest actual candle to entry time
        entry_mask = abs(plot_df.index - entry_time) <= timedelta(minutes=5)
        if entry_mask.any():
            entry_candle_time = plot_df.index[entry_mask][0]
            entry_candle_price = plot_df.loc[entry_candle_time, 'Close']
        else:
            # Use the closest available candle
            time_diff = abs(plot_df.index - entry_time)
            entry_candle_time = plot_df.index[time_diff.argmin()]
            entry_candle_price = plot_df.loc[entry_candle_time, 'Close']
            print(f"   ⚠️ Using nearest candle for entry: {entry_candle_time}")
        
        fig.add_trace(
            go.Scatter(
                x=[entry_candle_time],
                y=[entry_candle_price],
                mode='markers',
                marker=dict(color='green', size=15, symbol='star'),
                name=f'Entry (${trade["entry_price"]:.2f})'
            ),
            row=1, col=1
        )
        
        # Add exit point - find the closest actual candle to exit time
        exit_mask = abs(plot_df.index - exit_time) <= timedelta(minutes=5)
        if exit_mask.any():
            exit_candle_time = plot_df.index[exit_mask][0]
            exit_candle_price = plot_df.loc[exit_candle_time, 'Close']
        else:
            # Use the closest available candle
            time_diff = abs(plot_df.index - exit_time)
            exit_candle_time = plot_df.index[time_diff.argmin()]
            exit_candle_price = plot_df.loc[exit_candle_time, 'Close']
            print(f"   ⚠️ Using nearest candle for exit: {exit_candle_time}")
        
        fig.add_trace(
            go.Scatter(
                x=[exit_candle_time],
                y=[exit_candle_price],
                mode='markers',
                marker=dict(color='red', size=15, symbol='x'),
                name=f'Exit (${trade["exit_price"]:.2f})'
            ),
            row=1, col=1
        )
        
        # Update layout
        duration_days = (exit_time - entry_time).total_seconds() / (24 * 3600)
        held_over_weekend = " ⚠️ WEEKEND HOLD" if duration_days > 1 else ""
        
        fig.update_layout(
            title=f"{symbol} {category} #{rank} | {trade['type']} | "
                  f"P&L: ${trade['pnl']:+.2f} | Duration: {duration_days:.2f} days{held_over_weekend}<br>"
                  f"Trade Entry: {entry_time.strftime('%Y-%m-%d %H:%M (%A)')} | "
                  f"Trade Exit: {exit_time.strftime('%Y-%m-%d %H:%M (%A)')}<br>"
                  f"Chart Entry: {entry_candle_time.strftime('%Y-%m-%d %H:%M')} | "
                  f"Chart Exit: {exit_candle_time.strftime('%Y-%m-%d %H:%M')}",
            xaxis_rangeslider_visible=False,
            height=800,
            showlegend=True
        )
        
        # Add volume
        fig.add_trace(
            go.Bar(
                x=plot_df.index,
                y=plot_df['Volume'],
                name='Volume',
                marker_color='lightblue',
                opacity=0.7
            ),
            row=2, col=1
        )
        
        return fig
    
    def generate_fixed_charts(self, max_trades=2):
        """Generate fixed charts with proper time alignment"""
        print("🎯 GENERATING FIXED TRADE VISUALIZATIONS")
        print("=" * 60)
        
        # Create output directory
        os.makedirs('fixed_charts', exist_ok=True)
        
        for symbol in ['SPY']:  # Start with just SPY for testing
            print(f"\n📊 Processing {symbol}...")
            
            # Load trade data
            trades_df = self.load_trade_data(symbol)
            if trades_df is None:
                continue
            
            # Load price data
            price_df = self.load_price_data(symbol)
            if price_df is None:
                continue
            
            # Test with just 2 trades first
            test_trades = trades_df.head(max_trades)
            print(f"  Testing with {len(test_trades)} trades...")
            
            for i, (idx, trade) in enumerate(test_trades.iterrows()):
                print(f"  Creating chart for trade {i+1}...")
                fig = self.plot_trade_fixed(trade, price_df, symbol, 'Test', i+1)
                if fig:
                    filename = f"fixed_charts/{symbol}_Test_{i+1:02d}_{trade['type']}_{trade['pnl']:.0f}.html"
                    fig.write_html(filename)
                    print(f"    ✅ Saved: {filename}")
                else:
                    print(f"    ❌ Failed to create chart for trade {i+1}")

def run_fixed_visualization_v3():
    """Run the fixed visualization with robust timezone handling"""
    print("🎯 FIXED TRADE VISUALIZATION V3 - ROBUST TIMEZONE HANDLING")
    print("Handling mixed timezone timestamps with UTC conversion")
    print("=" * 60)
    
    # Load config
    config_path = "config/vwap_ma_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    visualizer = TradeVisualizerFixedV3(config)
    visualizer.generate_fixed_charts(max_trades=2)

if __name__ == "__main__":
    run_fixed_visualization_v3()