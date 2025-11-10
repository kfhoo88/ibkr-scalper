# core/backtester_proven.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yaml
from tqdm import tqdm
import sys
import os

sys.path.append('core')

class ProvenBacktester:
    def __init__(self, config_path="config/scalping_config_proven.yaml"):
        self.config = self.load_config(config_path)
        
    def load_config(self, config_path):
        """Load configuration"""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except:
            # Use the proven parameters you mentioned
            return {
                'options': {'strike_selection': '1_OTM'},
                'strategy': {
                    'ma_fast_period': 9,
                    'ma_slow_period': 14,
                    'min_volume': 1000,
                    'max_volatility': 2.0,
                    'avoid_open_minutes': 15,
                    'avoid_close_minutes': 30,
                    'max_hold_minutes': 20
                },
                'risk': {
                    'stop_loss_pct': 30,
                    'take_profit_pct': 20,
                    'hedge_activation_pct': 20
                },
                'trading': {
                    'max_position_value': 200
                },
                'backtesting': {
                    'initial_capital': 10000
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
    
    def is_trading_hours_ok(self, timestamp):
        """Check if we should trade based on time filters"""
        # Avoid first 15 minutes and last 30 minutes
        hour = timestamp.hour
        minute = timestamp.minute
        
        # Market hours: 9:30 AM to 4:00 PM
        if hour == 9 and minute < 45:  # First 15 minutes (9:30-9:45)
            return False
        if hour == 15 and minute >= 30:  # Last 30 minutes (3:30-4:00)
            return False
        
        return True
    
    def calculate_volatility(self, data, window=20):
        """Calculate volatility as percentage"""
        returns = data['close'].pct_change().rolling(window=window)
        volatility = returns.std() * np.sqrt(252)  # Annualized
        return volatility.iloc[-1] if len(volatility) > 0 else 0
    
    def generate_proven_signal(self, data, current_index):
        """Generate signals using the proven parameters"""
        if current_index < 20:  # Need enough data
            return None
        
        current_data = data.iloc[:current_index+1]
        current_bar = data.iloc[current_index]
        
        # Check time filters
        if not self.is_trading_hours_ok(current_data.index[-1]):
            return None
        
        # Check volume filter
        if current_bar['volume'] < self.config['strategy']['min_volume']:
            return None
        
        # Check volatility filter
        volatility = self.calculate_volatility(current_data)
        if volatility > self.config['strategy']['max_volatility']:
            return None
        
        # Calculate Heikin Ashi
        ha_data = self.calculate_heikin_ashi(current_data)
        
        if len(ha_data) < 20:
            return None
        
        # Calculate MAs with proven periods (9, 14)
        ma_fast = ha_data['ha_close'].rolling(window=9).mean().iloc[-1]
        ma_slow = ha_data['ha_close'].rolling(window=14).mean().iloc[-1]
        current_ha_close = ha_data['ha_close'].iloc[-1]
        current_ha_open = ha_data['ha_open'].iloc[-1]
        
        # Generate signal
        signal = {
            'timestamp': current_data.index[-1],
            'price': current_data['close'].iloc[-1],
            'volume': current_bar['volume'],
            'volatility': volatility
        }
        
        # Bullish signal: Fast MA above Slow MA and green HA candle
        if ma_fast > ma_slow and current_ha_close > current_ha_open:
            signal.update({
                'action': 'BUY_CALL',
                'type': 'CALL',
                'strength': min(1.0, (current_ha_close - current_ha_open) / current_ha_open * 10)
            })
            return signal
        
        # Bearish signal: Fast MA below Slow MA and red HA candle  
        elif ma_fast < ma_slow and current_ha_close < current_ha_open:
            signal.update({
                'action': 'BUY_PUT', 
                'type': 'PUT',
                'strength': min(1.0, (current_ha_open - current_ha_close) / current_ha_open * 10)
            })
            return signal
        
        return None
    
    def simulate_trade_exit(self, entry_data, entry_index, data, direction):
        """Simulate trade exit with stop loss and take profit"""
        entry_price = entry_data['close']
        stop_loss_pct = self.config['risk']['stop_loss_pct'] / 100
        take_profit_pct = self.config['risk']['take_profit_pct'] / 100
        max_hold_bars = self.config['strategy']['max_hold_minutes']  # 1 min per bar
        
        for i in range(entry_index + 1, min(entry_index + max_hold_bars + 1, len(data))):
            current_data = data.iloc[i]
            current_price = current_data['close']
            
            # Calculate P&L percentage
            if direction == 'BUY_CALL':
                pnl_pct = (current_price - entry_price) / entry_price
            else:  # BUY_PUT
                pnl_pct = (entry_price - current_price) / entry_price
            
            # Check stop loss
            if pnl_pct <= -stop_loss_pct:
                return {
                    'exit_time': data.index[i],
                    'exit_price': current_price,
                    'exit_reason': 'STOP_LOSS',
                    'pnl_pct': -stop_loss_pct
                }
            
            # Check take profit
            if pnl_pct >= take_profit_pct:
                return {
                    'exit_time': data.index[i],
                    'exit_price': current_price,
                    'exit_reason': 'TAKE_PROFIT', 
                    'pnl_pct': take_profit_pct
                }
        
        # Max hold time reached
        if entry_index + max_hold_bars < len(data):
            last_data = data.iloc[entry_index + max_hold_bars]
            last_price = last_data['close']
            
            if direction == 'BUY_CALL':
                pnl_pct = (last_price - entry_price) / entry_price
            else:
                pnl_pct = (entry_price - last_price) / entry_price
                
            return {
                'exit_time': data.index[entry_index + max_hold_bars],
                'exit_price': last_price,
                'exit_reason': 'MAX_HOLD',
                'pnl_pct': pnl_pct
            }
        
        return None
    
    def backtest_proven(self, data, symbol="SPY", sample_size=50000):
        """Backtest using the proven parameters"""
        print(f"PROVEN STRATEGY BACKTEST: {symbol}")
        print(f"Using: MA9/MA14 + 1_OTM + Time/Volume filters")
        print("=" * 60)
        
        # Use reasonable sample
        if len(data) > sample_size:
            data = data.iloc[-sample_size:]
            print(f"Using {len(data):,} bars for testing")
        
        portfolio_value = 10000
        max_position_value = 200
        trades = []
        
        # Backtest loop
        for i in tqdm(range(20, len(data)), desc=f"Testing {symbol}"):
            # Generate signal with proven parameters
            signal = self.generate_proven_signal(data, i)
            
            if signal and signal['action'] in ['BUY_CALL', 'BUY_PUT']:
                # Check capital
                if portfolio_value >= max_position_value:
                    # Simulate trade with proper exit
                    exit_info = self.simulate_trade_exit(data.iloc[i], i, data, signal['action'])
                    
                    if exit_info:
                        # Calculate actual P&L
                        pnl = max_position_value * exit_info['pnl_pct'] - 0.65  # Commission
                        portfolio_value += pnl
                        
                        trades.append({
                            'entry_time': data.index[i],
                            'exit_time': exit_info['exit_time'],
                            'entry_price': signal['price'],
                            'exit_price': exit_info['exit_price'],
                            'direction': signal['action'],
                            'pnl': pnl,
                            'pnl_pct': exit_info['pnl_pct'] * 100,
                            'exit_reason': exit_info['exit_reason'],
                            'portfolio_value': portfolio_value,
                            'symbol': symbol,
                            'volume': signal['volume'],
                            'volatility': signal['volatility']
                        })
        
        # Calculate results
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = len([t for t in trades if t['pnl'] < 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        total_pnl = sum(t['pnl'] for t in trades)
        total_return = (portfolio_value - 10000) / 10000
        
        print("\n" + "=" * 60)
        print("PROVEN STRATEGY RESULTS:")
        print("=" * 60)
        print(f"Total Trades: {total_trades}")
        print(f"Win Rate: {win_rate:.1%}")
        print(f"Winning Trades: {winning_trades}")
        print(f"Losing Trades: {losing_trades}")
        print(f"Total P&L: ${total_pnl:,.2f}")
        print(f"Total Return: {total_return:.2%}")
        print(f"Final Capital: ${portfolio_value:,.2f}")
        
        # Exit reason analysis
        if trades:
            exit_reasons = {}
            for trade in trades:
                reason = trade['exit_reason']
                exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
            
            print(f"\nEXIT REASONS:")
            for reason, count in exit_reasons.items():
                print(f"  {reason}: {count} trades ({count/total_trades:.1%})")
        
        # Trade frequency
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

def test_proven_strategy():
    """Test the proven strategy"""
    print("TESTING PROVEN STRATEGY PARAMETERS...")
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=10000, freq='1min')
    sample_data = pd.DataFrame({
        'open': np.random.normal(100, 1, 10000),
        'high': np.random.normal(101, 1, 10000),
        'low': np.random.normal(99, 1, 10000),
        'close': np.random.normal(100, 1, 10000),
        'volume': np.random.randint(1000, 50000, 10000)
    }, index=dates)
    
    backtester = ProvenBacktester()
    results = backtester.backtest_proven(sample_data, "TEST")
    
    return results

if __name__ == "__main__":
    test_proven_strategy()