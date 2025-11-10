# core/backtester_enhanced.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yaml
import math

class EnhancedOptionsBacktester:
    def __init__(self, config_path="config/scalping_config.yaml"):
        self.config = self.load_config(config_path)
        self.active_trades = []
        self.trade_history = []
        
    def load_config(self, config_path):
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"❌ Config load error: {e}")
            # Return default config
            return {
                'backtesting': {'initial_capital': 10000},
                'trading': {'max_position_value': 200},
                'options': {'strike_selection': '1_OTM'},
                'strategy': {
                    'ma_fast_period': 9,
                    'ma_slow_period': 14
                },
                'risk': {
                    'stop_loss_pct': 30,
                    'take_profit_pct': 20,
                    'hedge_activation_pct': 20
                }
            }
    
    def prepare_data(self, data):
        """Prepare data for backtesting - ensure proper structure"""
        # Make a copy to avoid modifying original
        prepared_data = data.copy()
        
        # Ensure we have a datetime index
        if not isinstance(prepared_data.index, pd.DatetimeIndex):
            if 'date' in prepared_data.columns:
                prepared_data['date'] = pd.to_datetime(prepared_data['date'])
                prepared_data.set_index('date', inplace=True)
            else:
                # Create a datetime index
                prepared_data.index = pd.date_range(
                    start='2024-01-01', 
                    periods=len(prepared_data), 
                    freq='1min'
                )
        
        # Ensure required columns exist
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        column_mapping = {
            'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume',
            'OPEN': 'open', 'HIGH': 'high', 'LOW': 'low', 'CLOSE': 'close', 'VOLUME': 'volume'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in prepared_data.columns and new_col not in prepared_data.columns:
                prepared_data[new_col] = prepared_data[old_col]
        
        # Fill any missing required columns
        for col in required_columns:
            if col not in prepared_data.columns:
                if col == 'volume':
                    prepared_data[col] = 1000  # Default volume
                else:
                    # Use close price for missing OHLC
                    prepared_data[col] = prepared_data.get('close', 100)
        
        return prepared_data
    
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
    
    def generate_trade_signal(self, data, current_index):
        """Generate trading signals based on strategy"""
        if current_index < 20:  # Need enough data for indicators
            return None
        
        current_data = data.iloc[:current_index+1]
        
        # Simple strategy: Use Heikin Ashi and moving averages
        ha_data = self.calculate_heikin_ashi(current_data)
        
        if len(ha_data) < 20:
            return None
        
        # Calculate indicators
        ma_fast = ha_data['ha_close'].rolling(window=9).mean().iloc[-1]
        ma_slow = ha_data['ha_close'].rolling(window=14).mean().iloc[-1]
        current_ha_close = ha_data['ha_close'].iloc[-1]
        current_ha_open = ha_data['ha_open'].iloc[-1]
        
        # Generate signal
        signal = {
            'timestamp': current_data.index[-1],
            'price': current_data['close'].iloc[-1]
        }
        
        # Bullish signal: Fast MA above Slow MA and green HA candle
        if ma_fast > ma_slow and current_ha_close > current_ha_open:
            signal.update({
                'action': 'BUY_CALL',
                'strength': min(1.0, (current_ha_close - current_ha_open) / current_ha_open * 10),
                'type': 'CALL'
            })
            return signal
        
        # Bearish signal: Fast MA below Slow MA and red HA candle  
        elif ma_fast < ma_slow and current_ha_close < current_ha_open:
            signal.update({
                'action': 'BUY_PUT', 
                'strength': min(1.0, (current_ha_open - current_ha_close) / current_ha_open * 10),
                'type': 'PUT'
            })
            return signal
        
        return None
    
    def backtest(self, data, symbol="SPY"):
        """Enhanced backtest method with proper data handling"""
        print(f"🚀 ENHANCED BACKTEST: {symbol} Options Scalping")
        
        # Prepare the data
        prepared_data = self.prepare_data(data)
        print(f"📊 Data: {len(prepared_data)} bars | Period: {prepared_data.index[0]} to {prepared_data.index[-1]}")
        print("=" * 60)
        
        portfolio_value = self.config['backtesting']['initial_capital']
        initial_capital = portfolio_value
        max_position_value = self.config['trading']['max_position_value']
        
        trades = []
        equity_curve = []
        
        # Main backtest loop
        for i in range(20, len(prepared_data)):  # Start from 20 for indicators
            current_time = prepared_data.index[i]
            
            # Generate signal
            signal = self.generate_trade_signal(prepared_data, i)
            
            if signal and signal['action'] in ['BUY_CALL', 'BUY_PUT']:
                # Check if we have enough capital
                if portfolio_value >= max_position_value:
                    # Simulate trade
                    entry_price = signal['price']
                    
                    # Simple exit: after 5 bars or 2% move
                    exit_bars = min(5, len(prepared_data) - i - 1)
                    if exit_bars > 0:
                        exit_data = prepared_data.iloc[i + exit_bars]
                        exit_price = exit_data['close']
                        exit_time = prepared_data.index[i + exit_bars]
                        
                        # Calculate P&L
                        if signal['action'] == 'BUY_CALL':
                            pnl_pct = (exit_price - entry_price) / entry_price
                        else:  # BUY_PUT
                            pnl_pct = (entry_price - exit_price) / entry_price
                        
                        # Apply position size and commission
                        pnl = max_position_value * pnl_pct
                        pnl -= 0.65  # Commission
                        
                        # Update portfolio
                        portfolio_value += pnl
                        
                        # Record trade
                        trade = {
                            'entry_time': current_time,
                            'exit_time': exit_time,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'direction': signal['action'],
                            'pnl': pnl,
                            'portfolio_value': portfolio_value,
                            'symbol': symbol
                        }
                        trades.append(trade)
            
            # Record equity curve
            equity_curve.append({
                'timestamp': current_time,
                'equity': portfolio_value
            })
        
        # Calculate results
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = len([t for t in trades if t['pnl'] < 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        total_pnl = sum(t['pnl'] for t in trades)
        total_return = (portfolio_value - initial_capital) / initial_capital
        
        print(f"✅ BACKTEST COMPLETE")
        print(f"📈 Total Trades: {total_trades}")
        print(f"🎯 Win Rate: {win_rate:.1%}")
        print(f"💰 Total P&L: ${total_pnl:,.2f}")
        print(f"📊 Total Return: {total_return:.2%}")
        print(f"💵 Final Capital: ${portfolio_value:,.2f}")
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_return': total_return,
            'final_capital': portfolio_value,
            'trades': trades,
            'equity_curve': equity_curve
        }

# Test function
def test_enhanced_backtester():
    """Test the enhanced backtester"""
    print("🧪 TESTING ENHANCED BACKTESTER...")
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=1000, freq='1min')
    sample_data = pd.DataFrame({
        'open': np.random.normal(100, 1, 1000),
        'high': np.random.normal(101, 1, 1000),
        'low': np.random.normal(99, 1, 1000),
        'close': np.random.normal(100, 1, 1000),
        'volume': np.random.randint(1000, 10000, 1000)
    }, index=dates)
    
    backtester = EnhancedOptionsBacktester()
    results = backtester.backtest(sample_data, "TEST")
    
    return results

if __name__ == "__main__":
    test_enhanced_backtester()