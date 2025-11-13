# vwap_ma_strategy/plot_trade_analysis_working.py
"""
Working Trade Visualization - Loads saved trade data and creates interactive charts
"""

import pandas as pd
import numpy as np
import yaml
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
import random
import os
import sys
import pickle

sys.path.append('..')

class TradeVisualizerWorking:
    def __init__(self, config):
        self.config = config['reversal_strategy']
        self.ema_length = self.config['ema_length']
        self.hl_backcandles = self.config['hl_backcandles']
    
    def load_trade_data(self, symbol):
        """Load saved trade data from pickle files"""
        filename = f'trade_data_{symbol}.pkl'
        try:
            trades_df = pd.read_pickle(filename)
            print(f"✅ Loaded {len(trades_df)} {symbol} trades from {filename}")
            return trades_df
        except FileNotFoundError:
            print(f"❌ Trade data file not found: {filename}")
            return None
    
    def load_price_data(self, symbol):
        """Load historical price data"""
        filename = f"../data/historical/{symbol}_IBKR_1min_1year_20251110.csv"
        try:
            df = pd.read_csv(filename)
            df['date'] = pd.to_datetime(df['date'], utc=True)  # Fix timezone warning
            df = df.set_index('date')
            column_map = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}
            return df.rename(columns=column_map)[['Open', 'High', 'Low', 'Close', 'Volume']]
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
    
    def is_weekend(self, timestamp):
        """Check if timestamp is on weekend"""
        return timestamp.weekday() >= 5
    
    def plot_trade_interactive(self, trade, df, symbol, category, rank):
        """Plot individual trade with full datetime context"""
        
        # Get trade timestamps
        entry_time = trade['entry_time']
        exit_time = trade['exit_time']
        
        # Determine time window for plot (4 hours before to 4 hours after)
        start_time = entry_time - timedelta(hours=4)
        end_time = exit_time + timedelta(hours=4)
        
        # Filter data for the time window
        mask = (df.index >= start_time) & (df.index <= end_time)
        plot_df = df[mask].copy()
        
        if len(plot_df) == 0:
            print(f"⚠️ No data for trade {rank} in {category}")
            return None
        
        # Calculate indicators for plot period
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
        
        # Add swing points
        swing_lows = plot_df[plot_df['Low'] == plot_df['swing_low']]
        swing_highs = plot_df[plot_df['High'] == plot_df['swing_high']]
        
        if len(swing_lows) > 0:
            fig.add_trace(
                go.Scatter(
                    x=swing_lows.index,
                    y=swing_lows['Low'],
                    mode='markers',
                    marker=dict(color='blue', size=8, symbol='triangle-up'),
                    name='Swing Low'
                ),
                row=1, col=1
            )
        
        if len(swing_highs) > 0:
            fig.add_trace(
                go.Scatter(
                    x=swing_highs.index,
                    y=swing_highs['High'],
                    mode='markers',
                    marker=dict(color='red', size=8, symbol='triangle-down'),
                    name='Swing High'
                ),
                row=1, col=1
            )
        
        # Add entry point
        fig.add_trace(
            go.Scatter(
                x=[entry_time],
                y=[trade['entry_price']],
                mode='markers',
                marker=dict(color='green', size=15, symbol='star'),
                name='Entry'
            ),
            row=1, col=1
        )
        
        # Add exit point
        fig.add_trace(
            go.Scatter(
                x=[exit_time],
                y=[trade['exit_price']],
                mode='markers',
                marker=dict(color='red', size=15, symbol='x'),
                name='Exit'
            ),
            row=1, col=1
        )
        
        # Add stop loss line
        if 'sl_price' in trade and trade['sl_price'] > 0:
            fig.add_trace(
                go.Scatter(
                    x=[start_time, end_time],
                    y=[trade['sl_price'], trade['sl_price']],
                    mode='lines',
                    line=dict(color='red', width=2, dash='dash'),
                    name='Stop Loss'
                ),
                row=1, col=1
            )
        
        # Add take profit line
        if 'tp_price' in trade and trade['tp_price'] > 0:
            fig.add_trace(
                go.Scatter(
                    x=[start_time, end_time],
                    y=[trade['tp_price'], trade['tp_price']],
                    mode='lines',
                    line=dict(color='green', width=2, dash='dash'),
                    name='Take Profit'
                ),
                row=1, col=1
            )
        
        # Add volume
        fig.add_trace(
            go.Bar(
                x=plot_df.index,
                y=plot_df['Volume'],
                name='Volume',
                marker_color='lightblue'
            ),
            row=2, col=1
        )
        
        # Add weekend shading
        weekend_periods = []
        current_date = start_time.date()
        end_date = end_time.date()
        
        while current_date <= end_date:
            if current_date.weekday() >= 5:  # Weekend
                weekend_start = datetime.combine(current_date, datetime.min.time())
                weekend_end = datetime.combine(current_date, datetime.max.time())
                weekend_periods.append((weekend_start, weekend_end))
            current_date += timedelta(days=1)
        
        for weekend_start, weekend_end in weekend_periods:
            fig.add_vrect(
                x0=weekend_start, x1=weekend_end,
                fillcolor="lightgray", opacity=0.3,
                layer="below", line_width=0,
                row=1, col=1
            )
            fig.add_vrect(
                x0=weekend_start, x1=weekend_end,
                fillcolor="lightgray", opacity=0.3,
                layer="below", line_width=0,
                row=2, col=1
            )
        
        # Update layout
        duration_days = (exit_time - entry_time).total_seconds() / (24 * 3600)
        held_over_weekend = " ⚠️ WEEKEND HOLD" if duration_days > 1 else ""
        
        fig.update_layout(
            title=f"{symbol} {category} #{rank} | {trade['type']} | "
                  f"P&L: ${trade['pnl']:+.2f} | Duration: {duration_days:.2f} days{held_over_weekend}<br>"
                  f"Entry: {entry_time.strftime('%Y-%m-%d %H:%M (%A)')} | "
                  f"Exit: {exit_time.strftime('%Y-%m-%d %H:%M (%A)')} | "
                  f"Exit Reason: {trade.get('exit_reason', 'N/A')}",
            xaxis_rangeslider_visible=False,
            height=800,
            showlegend=True
        )
        
        return fig
    
    def generate_all_interactive_charts(self, max_trades=10):
        """Generate interactive charts for worst losses, best wins, and random trades"""
        print("🎯 GENERATING INTERACTIVE TRADE VISUALIZATIONS")
        print("=" * 60)
        
        # Create output directory
        os.makedirs('interactive_charts', exist_ok=True)
        
        for symbol in ['SPY', 'QQQ']:
            print(f"\n📊 Processing {symbol}...")
            
            # Load trade data
            trades_df = self.load_trade_data(symbol)
            if trades_df is None or len(trades_df) == 0:
                continue
            
            # Load price data
            price_df = self.load_price_data(symbol)
            if price_df is None:
                continue
            
            # Top Worst Losses
            worst_losses = trades_df.nsmallest(max_trades, 'pnl')
            print(f"  Creating {len(worst_losses)} worst loss charts...")
            for i, (idx, trade) in enumerate(worst_losses.iterrows()):
                fig = self.plot_trade_interactive(trade, price_df, symbol, 'Worst_Loss', i+1)
                if fig:
                    filename = f"interactive_charts/{symbol}_Worst_Loss_{i+1:02d}_{trade['type']}_{trade['pnl']:.0f}.html"
                    fig.write_html(filename)
                    print(f"    ✅ Saved: {filename}")
            
            # Top Best Wins
            best_wins = trades_df.nlargest(max_trades, 'pnl')
            print(f"  Creating {len(best_wins)} best win charts...")
            for i, (idx, trade) in enumerate(best_wins.iterrows()):
                fig = self.plot_trade_interactive(trade, price_df, symbol, 'Best_Win', i+1)
                if fig:
                    filename = f"interactive_charts/{symbol}_Best_Win_{i+1:02d}_{trade['type']}_{trade['pnl']:.0f}.html"
                    fig.write_html(filename)
                    print(f"    ✅ Saved: {filename}")
            
            # Random Trades
            if len(trades_df) > max_trades:
                random_trades = trades_df.sample(max_trades)
                print(f"  Creating {len(random_trades)} random trade charts...")
                for i, (idx, trade) in enumerate(random_trades.iterrows()):
                    fig = self.plot_trade_interactive(trade, price_df, symbol, 'Random', i+1)
                    if fig:
                        filename = f"interactive_charts/{symbol}_Random_{i+1:02d}_{trade['type']}_{trade['pnl']:.0f}.html"
                        fig.write_html(filename)
                        print(f"    ✅ Saved: {filename}")
        
        print(f"\n🎉 INTERACTIVE CHARTS COMPLETE!")
        print(f"📁 Files saved in 'interactive_charts' folder")
        print(f"📊 Total: ~60 interactive HTML charts")
        print(f"🖱️  Open any .html file in your browser to analyze trades!")

def run_working_visualization():
    """Run the working visualization that loads saved trade data"""
    print("🎯 INTERACTIVE TRADE VISUALIZATION")
    print("Loading saved trade data and creating interactive charts")
    print("=" * 60)
    
    # Load config
    config_path = "config/vwap_ma_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    visualizer = TradeVisualizerWorking(config)
    visualizer.generate_all_interactive_charts(max_trades=10)

if __name__ == "__main__":
    run_working_visualization()