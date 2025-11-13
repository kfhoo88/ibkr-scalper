# vwap_ma_strategy/plot_trade_analysis_correct_prices.py
"""
Corrected Trade Visualization - Show actual entry/exit prices and times
"""

import pandas as pd
import numpy as np
import yaml
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os
import sys
import random

sys.path.append('..')

class TradeVisualizerCorrected:
    def __init__(self, config):
        self.config = config['reversal_strategy']
        self.ema_length = self.config['ema_length']
        self.hl_backcandles = self.config['hl_backcandles']
    
    def load_trade_data(self, symbol):
        """Load saved trade data and handle mixed timezones"""
        filename = f'trade_data_{symbol}.pkl'
        try:
            trades_df = pd.read_pickle(filename)
            print(f"✅ Loaded {len(trades_df)} {symbol} trades")
            
            # Convert to UTC first, then remove timezone
            trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'], utc=True).dt.tz_localize(None)
            trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'], utc=True).dt.tz_localize(None)
            
            return trades_df
        except Exception as e:
            print(f"❌ Error loading {symbol} trade data: {e}")
            return None
    
    def load_price_data(self, symbol):
        """Load historical price data with proper timezone handling"""
        filename = f"../data/historical/{symbol}_IBKR_1min_1year_20251110.csv"
        try:
            df = pd.read_csv(filename)
            df['date'] = pd.to_datetime(df['date'], utc=True).dt.tz_localize(None)
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
    
    def find_nearest_price_data(self, trade_time, price_df, window_hours=6):
        """Find the actual price data around the trade time"""
        start_time = trade_time - timedelta(hours=window_hours)
        end_time = trade_time + timedelta(hours=window_hours)
        
        mask = (price_df.index >= start_time) & (price_df.index <= end_time)
        plot_df = price_df[mask].copy()
        
        if len(plot_df) == 0:
            time_diff = abs(price_df.index - trade_time)
            closest_idx = time_diff.argmin()
            closest_time = price_df.index[closest_idx]
            start_time = closest_time - timedelta(hours=window_hours)
            end_time = closest_time + timedelta(hours=window_hours)
            mask = (price_df.index >= start_time) & (price_df.index <= end_time)
            plot_df = price_df[mask].copy()
        
        return plot_df
    
    def plot_trade_corrected(self, trade, price_df, symbol, category, rank):
        """Plot trade with CORRECT entry/exit prices and times"""
        
        entry_time = trade['entry_time']
        exit_time = trade['exit_time']
        entry_price = trade['entry_price']
        exit_price = trade['exit_price']
        
        print(f"   Trade {rank}: Entry={entry_time} @ ${entry_price:.2f}, Exit={exit_time} @ ${exit_price:.2f}")
        
        # Find price data around the trade
        plot_df = self.find_nearest_price_data(entry_time, price_df, window_hours=6)
        
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
        
        # **FIXED: Use ACTUAL entry/exit prices and times from trade data**
        fig.add_trace(
            go.Scatter(
                x=[entry_time],
                y=[entry_price],  # Use actual entry price from trade
                mode='markers',
                marker=dict(color='green', size=15, symbol='star'),
                name=f'Entry (${entry_price:.2f})'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=[exit_time],
                y=[exit_price],  # Use actual exit price from trade
                mode='markers',
                marker=dict(color='red', size=15, symbol='x'),
                name=f'Exit (${exit_price:.2f})'
            ),
            row=1, col=1
        )
        
        # Add stop loss and take profit lines at ACTUAL levels
        if 'sl_price' in trade and trade['sl_price'] > 0:
            fig.add_hline(
                y=trade['sl_price'],
                line_dash="dash", line_color="red",
                annotation_text=f"SL: ${trade['sl_price']:.2f}", 
                annotation_position="bottom right",
                row=1, col=1
            )
        
        if 'tp_price' in trade and trade['tp_price'] > 0:
            fig.add_hline(
                y=trade['tp_price'],
                line_dash="dash", line_color="green",
                annotation_text=f"TP: ${trade['tp_price']:.2f}",
                annotation_position="top right",
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
        
        # Add weekend shading
        weekend_periods = []
        start_date = plot_df.index.min().date()
        end_date = plot_df.index.max().date()
        
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() >= 5:
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
        
        # Update layout with CORRECT prices
        duration_days = (exit_time - entry_time).total_seconds() / (24 * 3600)
        held_over_weekend = " ⚠️ WEEKEND HOLD" if duration_days > 1 else ""
        
        price_move_pct = ((exit_price - entry_price) / entry_price * 100) if trade['type'] == 'LONG' else ((entry_price - exit_price) / entry_price * 100)
        
        fig.update_layout(
            title=f"{symbol} {category} #{rank} | {trade['type']} | "
                  f"P&L: ${trade['pnl']:+.2f} ({price_move_pct:+.2f}%)<br>"
                  f"Entry: {entry_time.strftime('%Y-%m-%d %H:%M (%A)')} @ ${entry_price:.2f}<br>"
                  f"Exit: {exit_time.strftime('%Y-%m-%d %H:%M (%A)')} @ ${exit_price:.2f}<br>"
                  f"Duration: {duration_days:.2f} days{held_over_weekend} | "
                  f"Exit Reason: {trade.get('exit_reason', 'N/A')}",
            xaxis_rangeslider_visible=False,
            height=800,
            showlegend=True
        )
        
        return fig
    
    def generate_corrected_charts(self, charts_per_category=5):
        """Generate charts with CORRECT entry/exit prices"""
        print("🎯 GENERATING CORRECTED TRADE CHARTS")
        print("Using actual entry/exit prices from trade data")
        print("=" * 60)
        
        # Create output directory
        os.makedirs('corrected_charts', exist_ok=True)
        
        total_charts = 0
        
        for symbol in ['SPY', 'QQQ']:
            print(f"\n📊 Processing {symbol}...")
            
            # Load trade data
            trades_df = self.load_trade_data(symbol)
            if trades_df is None:
                continue
            
            # Load price data
            price_df = self.load_price_data(symbol)
            if price_df is None:
                continue
            
            # Test with fewer charts first to verify
            print(f"  📉 Creating {charts_per_category} worst loss charts...")
            worst_losses = trades_df.nsmallest(charts_per_category, 'pnl')
            for i, (idx, trade) in enumerate(worst_losses.iterrows()):
                fig = self.plot_trade_corrected(trade, price_df, symbol, 'Worst_Loss', i+1)
                if fig:
                    filename = f"corrected_charts/{symbol}_Worst_Loss_{i+1:02d}_{trade['type']}_{trade['pnl']:.0f}.html"
                    fig.write_html(filename)
                    total_charts += 1
                    print(f"    ✅ {filename}")
            
            print(f"  📈 Creating {charts_per_category} best win charts...")
            best_wins = trades_df.nlargest(charts_per_category, 'pnl')
            for i, (idx, trade) in enumerate(best_wins.iterrows()):
                fig = self.plot_trade_corrected(trade, price_df, symbol, 'Best_Win', i+1)
                if fig:
                    filename = f"corrected_charts/{symbol}_Best_Win_{i+1:02d}_{trade['type']}_{trade['pnl']:.0f}.html"
                    fig.write_html(filename)
                    total_charts += 1
                    print(f"    ✅ {filename}")
        
        print(f"\n🎉 CORRECTED CHARTS COMPLETED!")
        print(f"📁 Location: 'corrected_charts' folder")
        print(f"📊 Total: {total_charts} charts with correct prices")
        print(f"🖱️  Open any .html file to verify entry/exit accuracy")

def run_corrected_visualization():
    """Run the corrected visualization with proper prices"""
    print("🎯 CORRECTED TRADE VISUALIZATION")
    print("Using actual entry/exit prices instead of candle close prices")
    print("=" * 60)
    
    # Load config
    config_path = "config/vwap_ma_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    visualizer = TradeVisualizerCorrected(config)
    visualizer.generate_corrected_charts(charts_per_category=5)

if __name__ == "__main__":
    run_corrected_visualization()