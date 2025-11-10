# core/backtester_fast.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yaml
from tqdm import tqdm
import sys
import os

sys.path.append('core')

class FastBacktester:
    def __init__(self, config_path="config/scalping_config_optimized.yaml"):
        self.config = self.load_config(config_path)
        
    def load_config(self, config_path):
        """Load configuration"""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except:
            return {
                'backtesting': {'initial_capital': 10000},
                'trading': {'max_position_value': 200},
                'strategy': {
                    'ma_fast_period': 12,
                    'ma_slow_period': 20,
                    'min_signal_strength': 0.3
                }
            }
    
    def calculate_heikin_ashi(self, df):
        """Calculate Heikin Ashi candles"""
        ha_df = df.copy()
        
        if len(ha_df) == 0:
            return ha_df
            
        # Heikin Ashi Close
        ha_df['ha_close'] = (ha_df['open'] + ha_df['high'] + ha_df['low'] + ha_df['close']) / 4
        
        # Heikin Ashi Open
        ha_df['ha_open'] = 0.0
        ha_df.iloc[0, ha_df.columns.get_loc('ha_open')] = (ha_df['open'].iloc[0] + ha_df['close'].iloc[0]) / 2
        
        for i in range(1, len(ha_df)):
            ha_open = (ha_df['ha_open'].iloc[i-1] + ha_df['ha_close'].iloc[i-1]) / 2
            ha_df.iloc[i, ha_df.columns.get_loc('ha_open')] = ha_open
        
        # Heikin Ashi High and Low
        ha_df['ha_high'] = ha_df[['high', 'ha_open', 'ha_close']].max(axis=1)
        ha_df['ha_low'] = ha_df[['low', 'ha_open', 'ha_close']].min(axis=1)
        
        return ha_df
    
    def generate_signal_selective(self, data, current_index):
        """Generate more selective trading signals"""
        if current_index < 50:  # Need more data for longer MAs
            return None
        
        current_data = data.iloc[:current_index+1]
        ha_data = self.calculate_heikin_ashi(current_data)
        
        if len(ha_data) < 50:
            return None
        
        # Get config parameters
        ma_fast = self.config['strategy']['ma_fast_period']
        ma_slow = self.config['strategy']['ma_slow_period']
        min_strength = self.config['strategy']['min_signal_strength']
        
        # Calculate indicators with longer periods
        fast_ma = ha_data['ha_close'].rolling(window=ma_fast).mean().iloc[-1]
        slow_ma = ha_data['ha_close'].rolling(window=ma_slow).mean().iloc[-1]
        current_ha_close = ha_data['ha_close'].iloc[-1]
        current_ha_open = ha_data['ha_open'].iloc[-1]
        
        # Calculate signal strength
        ma_spread = abs(fast_ma - slow_ma) / slow_ma
        candle_strength = abs(current_ha_close - current_ha_open) / current_ha_open
        
        # Only trade if signals are strong enough
        if ma_spread < 0.001 or candle_strength < 0.001:  # Too weak
            return None
        
        signal_strength = min(1.0, (ma_spread + candle_strength) * 10)
        
        if signal_strength < min_strength:
            return None  # Filter out weak signals
        
        # Generate signal
        signal = {
            'timestamp': current_data.index[-1],
            'price': current_data['close'].iloc[-1],
            'strength': signal_strength
        }
        
        # Bullish signal
        if fast_ma > slow_ma and current_ha_close > current_ha_open:
            signal.update({
                'action': 'BUY_CALL',
                'type': 'CALL'
            })
            return signal
        
        # Bearish signal  
        elif fast_ma < slow_ma and current_ha_close < current_ha_open:
            signal.update({
                'action': 'BUY_PUT',
                'type': 'PUT'
            })
            return signal
        
        return None
    
    def backtest_fast(self, data, symbol="SPY", sample_size=30000):
        """Fast backtest with selective trading"""
        print(f"FAST BACKTEST: {symbol}")
        
        # Use reasonable sample for speed
        if len(data) > sample_size:
            data = data.iloc[-sample_size:]
            print(f"Using {len(data):,} bars for fast test")
        
        portfolio_value = 10000
        max_position_value = 200
        trades = []
        daily_trades = {}
        
        # Fast backtest loop
        for i in tqdm(range(50, len(data)), desc=f"Testing {symbol}"):
            current_date = data.index[i].date()
            
            # Check daily trade limit
            if current_date not in daily_trades:
                daily_trades[current_date] = 0
            
            if daily_trades[current_date] >= 10:  # Max 10 trades per day
                continue
            
            # Generate selective signal
            signal = self.generate_signal_selective(data, i)
            
            if signal and signal['action'] in ['BUY_CALL', 'BUY_PUT']:
                # Check capital and daily limits
                if portfolio_value >= max_position_value and daily_trades[current_date] < 10:
                    entry_price = signal['price']
                    
                    # Exit after 3-8 bars (shorter for scalping)
                    exit_bars = min(np.random.randint(3, 8), len(data) - i - 1)
                    
                    if exit_bars > 0:
                        exit_data = data.iloc[i + exit_bars]
                        exit_price = exit_data['close']
                        exit_time = data.index[i + exit_bars]
                        
                        # Calculate P&L
                        if signal['action'] == 'BUY_CALL':
                            pnl_pct = (exit_price - entry_price) / entry_price
                        else:  # BUY_PUT
                            pnl_pct = (entry_price - exit_price) / entry_price
                        
                        pnl = max_position_value * pnl_pct - 0.65
                        portfolio_value += pnl
                        
                        trades.append({
                            'entry_time': data.index[i],
                            'exit_time': exit_time,
                            'direction': signal['action'],
                            'pnl': pnl,
                            'portfolio_value': portfolio_value,
                            'symbol': symbol
                        })
                        
                        daily_trades[current_date] += 1
        
        # Calculate results
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = len([t for t in trades if t['pnl'] < 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        total_pnl = sum(t['pnl'] for t in trades)
        total_return = (portfolio_value - 10000) / 10000
        
        print("BACKTEST COMPLETE")
        print(f"Total Trades: {total_trades}")
        print(f"Win Rate: {win_rate:.1%}")
        print(f"Total P&L: ${total_pnl:,.2f}")
        print(f"Total Return: {total_return:.2%}")
        print(f"Final Capital: ${portfolio_value:,.2f}")
        
        # Trade frequency analysis
        trades_per_bar = total_trades / len(data) if len(data) > 0 else 0
        print(f"Trade Frequency: {trades_per_bar*100:.1f}% of bars")
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_return': total_return,
            'final_capital': portfolio_value,
            'trades': trades
        }

def test_fast_backtester():
    """Test the fast backtester"""
    print("TESTING FAST BACKTESTER...")
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=5000, freq='1min')
    sample_data = pd.DataFrame({
        'open': np.random.normal(100, 1, 5000),
        'high': np.random.normal(101, 1, 5000),
        'low': np.random.normal(99, 1, 5000),
        'close': np.random.normal(100, 1, 5000),
        'volume': np.random.randint(1000, 10000, 5000)
    }, index=dates)
    
    backtester = FastBacktester()
    results = backtester.backtest_fast(sample_data, "TEST")
    
    return results

if __name__ == "__main__":
    test_fast_backtester()
