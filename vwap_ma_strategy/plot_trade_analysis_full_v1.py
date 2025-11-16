# vwap_ma_strategy/plot_trade_analysis_full.py
"""
Full Trade Visualization - Generate all 30 charts for analysis
Worst losses, best wins, and random trades for both SPY and QQQ
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

class TradeVisualizerFull:
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
    
    def plot_trade_full(self, trade, price_df, symbol, category, rank):
        """Plot individual trade with full analysis context"""
        
        entry_time = trade['entry_time']
        exit_time = trade['exit_time']
        
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
        
        # Find closest candles for entry/exit
        entry_mask = abs(plot_df.index - entry_time) <= timedelta(minutes=5)
        if entry_mask.any():
            entry_candle_time = plot_df.index[entry_mask][0]
            entry_candle_price = plot_df.loc[entry_candle_time, 'Close']
        else:
            time_diff = abs(plot_df.index - entry_time)
            entry_candle_time = plot_df.index[time_diff.argmin()]
            entry_candle_price = plot_df.loc[entry_candle_time, 'Close']
        
        exit_mask = abs(plot_df.index - exit_time) <= timedelta(minutes=5)
        if exit_mask.any():
            exit_candle_time = plot_df.index[exit_mask][0]
            exit_candle_price = plot_df.loc[exit_candle_time, 'Close']
        else:
            time_diff = abs(plot_df.index - exit_time)
            exit_candle_time = plot_df.index[time_diff.argmin()]
            exit_candle_price = plot_df.loc[exit_candle_time, 'Close']
        
        # Add entry and exit points
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
        
        # Add stop loss and take profit lines
        if 'sl_price' in trade and trade['sl_price'] > 0:
            fig.add_hline(
                y=trade['sl_price'],
                line_dash="dash", line_color="red",
                annotation_text="Stop Loss", 
                annotation_position="bottom right",
                row=1, col=1
            )
        
        if 'tp_price' in trade and trade['tp_price'] > 0:
            fig.add_hline(
                y=trade['tp_price'],
                line_dash="dash", line_color="green",
                annotation_text="Take Profit",
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
    
    def generate_all_charts(self, charts_per_category=10):
        """Generate all 30 charts: worst losses, best wins, and random trades for both SPY and QQQ"""
        print("🎯 GENERATING ALL 30 TRADE ANALYSIS CHARTS")
        print("=" * 60)
        
        # Create output directory
        os.makedirs('analysis_charts', exist_ok=True)
        
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
            
            # 1. Top Worst Losses
            print(f"  📉 Creating {charts_per_category} worst loss charts...")
            worst_losses = trades_df.nsmallest(charts_per_category, 'pnl')
            for i, (idx, trade) in enumerate(worst_losses.iterrows()):
                fig = self.plot_trade_full(trade, price_df, symbol, 'Worst_Loss', i+1)
                if fig:
                    filename = f"analysis_charts/{symbol}_Worst_Loss_{i+1:02d}_{trade['type']}_{trade['pnl']:.0f}.html"
                    fig.write_html(filename)
                    total_charts += 1
                    print(f"    ✅ {filename}")
            
            # 2. Top Best Wins
            print(f"  📈 Creating {charts_per_category} best win charts...")
            best_wins = trades_df.nlargest(charts_per_category, 'pnl')
            for i, (idx, trade) in enumerate(best_wins.iterrows()):
                fig = self.plot_trade_full(trade, price_df, symbol, 'Best_Win', i+1)
                if fig:
                    filename = f"analysis_charts/{symbol}_Best_Win_{i+1:02d}_{trade['type']}_{trade['pnl']:.0f}.html"
                    fig.write_html(filename)
                    total_charts += 1
                    print(f"    ✅ {filename}")
            
            # 3. Random Trades
            print(f"  🎲 Creating {charts_per_category} random trade charts...")
            if len(trades_df) > charts_per_category:
                random_trades = trades_df.sample(charts_per_category, random_state=42)
                for i, (idx, trade) in enumerate(random_trades.iterrows()):
                    fig = self.plot_trade_full(trade, price_df, symbol, 'Random', i+1)
                    if fig:
                        filename = f"analysis_charts/{symbol}_Random_{i+1:02d}_{trade['type']}_{trade['pnl']:.0f}.html"
                        fig.write_html(filename)
                        total_charts += 1
                        print(f"    ✅ {filename}")
        
        print(f"\n🎉 ALL CHARTS COMPLETED!")
        print(f"📁 Location: 'analysis_charts' folder")
        print(f"📊 Total: {total_charts} interactive HTML charts")
        print(f"🖱️  Open any .html file in your browser to analyze")
        print(f"\n📋 BREAKDOWN:")
        print(f"   - 10 worst losses for SPY")
        print(f"   - 10 best wins for SPY") 
        print(f"   - 10 random trades for SPY")
        print(f"   - 10 worst losses for QQQ")
        print(f"   - 10 best wins for QQQ")
        print(f"   - 10 random trades for QQQ")

def run_full_visualization():
    """Run the full visualization with all 30 charts"""
    print("🎯 COMPREHENSIVE TRADE ANALYSIS - 30 CHARTS")
    print("Generating worst losses, best wins, and random trades for SPY & QQQ")
    print("=" * 60)
    
    # Load config
    config_path = "config/vwap_ma_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    visualizer = TradeVisualizerFull(config)
    visualizer.generate_all_charts(charts_per_category=10)

if __name__ == "__main__":
    run_full_visualization()