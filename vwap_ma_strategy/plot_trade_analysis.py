# vwap_ma_strategy/plot_trade_analysis.py
"""
Comprehensive Trade Visualization
Plot top losses, top wins, and random trades with datetime context
Identify weekend hold patterns and time-based issues
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

sys.path.append('..')

class TradeVisualizer:
    def __init__(self, config):
        self.config = config['reversal_strategy']
        self.ema_length = self.config['ema_length']
        self.hl_backcandles = self.config['hl_backcandles']
    
    def load_data(self, symbol):
        """Load historical data"""
        filename = f"../data/historical/{symbol}_IBKR_1min_1year_20251110.csv"
        df = pd.read_csv(filename)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        column_map = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}
        return df.rename(columns=column_map)[['Open', 'High', 'Low', 'Close', 'Volume']]
    
    def calculate_indicators(self, df):
        """Calculate EMA and swing points for plotting"""
        df = df.copy()
        df['EMA'] = df['Close'].ewm(span=self.ema_length, adjust=False).mean()
        df['swing_low'] = df['Low'].rolling(window=self.hl_backcandles, center=False).min()
        df['swing_high'] = df['High'].rolling(window=self.hl_backcandles, center=False).max()
        return df
    
    def is_weekend(self, timestamp):
        """Check if timestamp is on weekend"""
        return timestamp.weekday() >= 5  # 5=Saturday, 6=Sunday
    
    def get_market_session(self, timestamp):
        """Determine market session based on time"""
        hour = timestamp.hour
        if 9 <= hour < 17:  # 9am-5pm ET
            return 'Regular'
        else:
            return 'Overnight'
    
    def plot_trade(self, trade, df, symbol, category, rank):
        """Plot individual trade with full datetime context"""
        
        # Get trade timestamps
        entry_time = trade['entry_time']
        exit_time = trade['exit_time']
        
        # Determine time window for plot (2 hours before to 2 hours after)
        start_time = entry_time - timedelta(hours=2)
        end_time = exit_time + timedelta(hours=2)
        
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
                marker=dict(color='green', size=12, symbol='star'),
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
                marker=dict(color='red', size=12, symbol='x'),
                name='Exit'
            ),
            row=1, col=1
        )
        
        # Add stop loss line
        if 'sl_price' in trade and trade['sl_price'] > 0:
            fig.add_trace(
                go.Scatter(
                    x=[entry_time, exit_time],
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
                    x=[entry_time, exit_time],
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
        
        # Add overnight shading
        for single_date in pd.date_range(start_time.date(), end_time.date()):
            overnight_start = datetime.combine(single_date, datetime.min.time())
            market_open = datetime.combine(single_date, datetime.strptime('09:30', '%H:%M').time())
            market_close = datetime.combine(single_date, datetime.strptime('16:00', '%H:%M').time())
            overnight_end = datetime.combine(single_date, datetime.max.time())
            
            # Pre-market
            fig.add_vrect(
                x0=overnight_start, x1=market_open,
                fillcolor="yellow", opacity=0.1,
                layer="below", line_width=0,
                row=1, col=1
            )
            
            # After-hours
            fig.add_vrect(
                x0=market_close, x1=overnight_end,
                fillcolor="yellow", opacity=0.1,
                layer="below", line_width=0,
                row=1, col=1
            )
        
        # Update layout
        duration_days = (exit_time - entry_time).total_seconds() / (24 * 3600)
        held_over_weekend = "⚠️ WEEKEND HOLD" if duration_days > 1 else ""
        
        fig.update_layout(
            title=f"{symbol} {category} #{rank} | {trade['type']} | "
                  f"P&L: ${trade['pnl']:+.2f} | Duration: {duration_days:.2f} days {held_over_weekend}<br>"
                  f"Entry: {entry_time.strftime('%Y-%m-%d %H:%M (%A)')} | "
                  f"Exit: {exit_time.strftime('%Y-%m-%d %H:%M (%A)')} | "
                  f"Exit Reason: {trade.get('exit_reason', 'N/A')}",
            xaxis_rangeslider_visible=False,
            height=800,
            showlegend=True
        )
        
        # Add day separators
        for single_date in pd.date_range(start_time.date(), end_time.date()):
            fig.add_vline(
                x=datetime.combine(single_date, datetime.min.time()),
                line_width=1, line_dash="dash", line_color="gray"
            )
        
        return fig
    
    def analyze_trade_durations(self, trades_df, symbol):
        """Analyze trade duration patterns"""
        trades_df = trades_df.copy()
        trades_df['duration_days'] = trades_df['duration_minutes'] / (24 * 60)
        trades_df['entry_day'] = trades_df['entry_time'].dt.day_name()
        trades_df['exit_day'] = trades_df['exit_time'].dt.day_name()
        trades_df['held_over_weekend'] = trades_df['duration_days'] > 1
        
        print(f"\n📅 TRADE DURATION ANALYSIS - {symbol}:")
        print(f"   Total trades: {len(trades_df)}")
        print(f"   Weekend holds: {trades_df['held_over_weekend'].sum()} ({(trades_df['held_over_weekend'].mean()*100):.1f}%)")
        print(f"   Avg duration: {trades_df['duration_days'].mean():.2f} days")
        print(f"   Max duration: {trades_df['duration_days'].max():.2f} days")
        
        # Day of week analysis
        print(f"\n   Entry Day Distribution:")
        day_counts = trades_df['entry_day'].value_counts()
        for day, count in day_counts.items():
            print(f"     {day}: {count} trades ({(count/len(trades_df)*100):.1f}%)")
        
        # Weekend hold performance
        weekend_trades = trades_df[trades_df['held_over_weekend']]
        if len(weekend_trades) > 0:
            print(f"\n   Weekend Hold Performance:")
            print(f"     Count: {len(weekend_trades)}")
            print(f"     Avg P&L: ${weekend_trades['pnl'].mean():.2f}")
            print(f"     Win Rate: {(weekend_trades['pnl'] > 0).mean()*100:.1f}%")
        
        return trades_df

def run_comprehensive_visual_analysis():
    """Run full visual analysis of trades"""
    print("🎯 COMPREHENSIVE TRADE VISUAL ANALYSIS")
    print("Plotting top losses, wins, and random trades")
    print("=" * 60)
    
    # Load config
    config_path = "config/vwap_ma_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    visualizer = TradeVisualizer(config)
    
    # We need the detailed trades data - let's generate it first
    from main_reversal_detailed import run_detailed_backtest
    
    print("📊 Generating trade data...")
    # This would run the backtest and return detailed trades
    # For now, let's assume we have the trades data
    
    # Load data and simulate getting trades
    spy_data = visualizer.load_data('SPY')
    qqq_data = visualizer.load_data('QQQ')
    
    # For demonstration, we'll create sample trade data structure
    # In practice, you'd run the backtest first
    
    print("🔧 Note: Need to run detailed backtest first to get trade data")
    print("Run: python main_reversal_detailed.py to generate trade data")
    print("Then we can load and visualize the trades")
    
    return visualizer, spy_data, qqq_data

if __name__ == "__main__":
    visualizer, spy_data, qqq_data = run_comprehensive_visual_analysis()
    
    print(f"\n✅ Visualization setup complete!")
    print(f"Next steps:")
    print(f"1. Run detailed backtest to generate trade data")
    print(f"2. Load trade results")
    print(f"3. Generate charts for:")
    print(f"   - Top 10 worst losses") 
    print(f"   - Top 10 best wins")
    print(f"   - 10 random trades")
    print(f"4. Analyze weekend hold patterns")