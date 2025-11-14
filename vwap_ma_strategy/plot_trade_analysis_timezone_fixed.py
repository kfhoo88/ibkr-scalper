# vwap_ma_strategy/plot_trade_analysis_timezone_fixed.py
"""
Fixed Visualization - Consistent Eastern Time display
"""

import pandas as pd
import numpy as np
import yaml
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os
import sys
import pytz

sys.path.append('..')

class TimezoneFixedVisualizer:
    def __init__(self, config):
        self.config = config['reversal_strategy']
        self.ema_length = self.config['ema_length']
        self.hl_backcandles = self.config['hl_backcandles']
        self.est = pytz.timezone('US/Eastern')
    
    def load_trade_data(self, symbol):
        """Load trade data and ensure Eastern Time"""
        filename = f'trade_data_{symbol}.pkl'
        try:
            trades_df = pd.read_pickle(filename)
            print(f"✅ Loaded {len(trades_df)} {symbol} trades")
            
            # Ensure timestamps are in Eastern Time
            trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time']).dt.tz_convert(self.est)
            trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time']).dt.tz_convert(self.est)
            
            return trades_df
        except Exception as e:
            print(f"❌ Error loading {symbol} trade data: {e}")
            return None
    
    def load_price_data(self, symbol):
        """Load price data with proper Eastern Time handling"""
        filename = f"../data/historical/{symbol}_IBKR_1min_1year_20251110.csv"
        try:
            df = pd.read_csv(filename)
            # Data already has Eastern Time - keep it!
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            column_map = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}
            return df.rename(columns=column_map)[['Open', 'High', 'Low', 'Close', 'Volume']]
        except FileNotFoundError:
            print(f"❌ Price data file not found: {filename}")
            return None
    
    def calculate_indicators(self, df):
        """Calculate EMA and swing points"""
        df = df.copy()
        df['EMA'] = df['Close'].ewm(span=self.ema_length, adjust=False).mean()
        df['swing_low'] = df['Low'].rolling(window=self.hl_backcandles, center=False).min()
        df['swing_high'] = df['High'].rolling(window=self.hl_backcandles, center=False).max()
        return df
    
    def plot_trade_timezone_fixed(self, trade, price_df, symbol, category, rank):
        """Plot trade with CONSISTENT Eastern Time display"""
        
        entry_time = trade['entry_time']
        exit_time = trade['exit_time']
        entry_price = trade['entry_price']
        exit_price = trade['exit_price']
        
        print(f"   Trade {rank}: Entry={entry_time} @ ${entry_price:.2f}, Exit={exit_time} @ ${exit_price:.2f}")
        
        # Ensure price data index is in Eastern Time for proper alignment
        if price_df.index.tz is None:
            price_df.index = price_df.index.tz_localize(self.est)
        else:
            price_df.index = price_df.index.tz_convert(self.est)
        
        # Find price data around the trade (4 hours before to 4 hours after)
        start_time = entry_time - timedelta(hours=4)
        end_time = exit_time + timedelta(hours=4)
        
        mask = (price_df.index >= start_time) & (price_df.index <= end_time)
        plot_df = price_df[mask].copy()
        
        if len(plot_df) == 0:
            return None
        
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
        
        # Add entry and exit points with ACTUAL prices and times
        fig.add_trace(
            go.Scatter(
                x=[entry_time],
                y=[entry_price],
                mode='markers',
                marker=dict(color='green', size=15, symbol='star'),
                name=f'Entry (${entry_price:.2f})'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=[exit_time],
                y=[exit_price],
                mode='markers',
                marker=dict(color='red', size=15, symbol='x'),
                name=f'Exit (${exit_price:.2f})'
            ),
            row=1, col=1
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
        
        # Update layout
        duration_days = (exit_time - entry_time).total_seconds() / (24 * 3600)
        
        fig.update_layout(
            title=f"{symbol} {category} #{rank} | {trade['type']} | "
                  f"P&L: ${trade['pnl']:+.2f} | Duration: {duration_days:.2f} days<br>"
                  f"Entry: {entry_time.strftime('%Y-%m-%d %H:%M (%A) EST')} @ ${entry_price:.2f}<br>"
                  f"Exit: {exit_time.strftime('%Y-%m-%d %H:%M (%A) EST')} @ ${exit_price:.2f}",
            xaxis_rangeslider_visible=False,
            height=800,
            showlegend=True
        )
        
        return fig

def run_timezone_fixed_visualization():
    """Run visualization with consistent Eastern Time"""
    print("🎯 TIMEZONE-FIXED VISUALIZATION")
    print("All dates/times displayed in Eastern Time consistently")
    print("=" * 60)
    
    config_path = "config/vwap_ma_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    visualizer = TimezoneFixedVisualizer(config)
    
    # Create output directory
    os.makedirs('timezone_fixed_charts', exist_ok=True)
    
    for symbol in ['SPY']:  # Test with SPY first
        print(f"\n📊 Processing {symbol}...")
        
        trades_df = visualizer.load_trade_data(symbol)
        if trades_df is None:
            continue
            
        price_df = visualizer.load_price_data(symbol)
        if price_df is None:
            continue
        
        # Test with 2 charts
        test_trades = trades_df.head(2)
        for i, (idx, trade) in enumerate(test_trades.iterrows()):
            fig = visualizer.plot_trade_timezone_fixed(trade, price_df, symbol, 'Test', i+1)
            if fig:
                filename = f"timezone_fixed_charts/{symbol}_Test_{i+1:02d}_{trade['type']}_{trade['pnl']:.0f}.html"
                fig.write_html(filename)
                print(f"    ✅ {filename}")

if __name__ == "__main__":
    run_timezone_fixed_visualization()