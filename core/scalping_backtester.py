# core/scalping_backtester.py
import pandas as pd
import numpy as np
from datetime import timedelta
import logging

class ScalpingBacktester:
    def __init__(self, config):
        self.config = config
        self.strategy_config = config['strategy']
        self.risk_config = config['risk'] 
        self.trading_config = config['trading']
        self.backtest_config = config['backtesting']
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def ensure_datetime_index(self, data):
        """Ensure the index is a proper datetime index"""
        if not isinstance(data.index, pd.DatetimeIndex):
            self.logger.info("Converting index to datetime...")
            data.index = pd.to_datetime(data.index, utc=True)
        
        # Remove timezone for consistent processing
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
            
        return data
        
    def calculate_heikin_ashi(self, data):
        """Calculate Heikin Ashi candles"""
        self.logger.info("Calculating Heikin Ashi...")
        
        ha_close = (data['open'] + data['high'] + data['low'] + data['close']) / 4
        
        ha_open = np.zeros(len(data))
        ha_open[0] = (data['open'].iloc[0] + data['close'].iloc[0]) / 2
        for i in range(1, len(data)):
            ha_open[i] = (ha_open[i-1] + ha_close.iloc[i-1]) / 2
        
        ha_high = np.maximum.reduce([data['high'], ha_open, ha_close])
        ha_low = np.minimum.reduce([data['low'], ha_open, ha_close])
        
        return pd.DataFrame({
            'ha_open': ha_open, 
            'ha_high': ha_high,
            'ha_low': ha_low, 
            'ha_close': ha_close
        })
    
    def precompute_indicators(self, data):
        """Precompute all technical indicators"""
        self.logger.info("Precomputing indicators...")
        
        # Ensure proper datetime index FIRST
        data = self.ensure_datetime_index(data)
        
        # Heikin Ashi
        ha_data = self.calculate_heikin_ashi(data)
        
        # Moving averages on Heikin Ashi close
        fast_period = self.strategy_config.get('ma_fast_period', 9)
        slow_period = self.strategy_config.get('ma_slow_period', 14)
        
        data['ma_fast'] = ha_data['ha_close'].rolling(window=fast_period).mean()
        data['ma_slow'] = ha_data['ha_close'].rolling(window=slow_period).mean()
        
        # Signal flags
        data['is_bullish'] = (data['ma_fast'] > data['ma_slow']) & (ha_data['ha_close'] > ha_data['ha_open'])
        data['is_bearish'] = (data['ma_fast'] < data['ma_slow']) & (ha_data['ha_close'] < ha_data['ha_open'])
        
        # Time filters - FIXED: Now with proper datetime index
        data['hour'] = data.index.hour
        data['minute'] = data.index.minute
        
        avoid_open = self.trading_config.get('avoid_open_minutes', 15)
        avoid_close = self.trading_config.get('avoid_close_minutes', 30)
        
        data['is_trading_hours'] = ~(
            ((data['hour'] == 9) & (data['minute'] < (30 + avoid_open))) |
            ((data['hour'] == 15) & (data['minute'] >= (60 - avoid_close)))
        )
        
        # Volume filter
        min_volume = self.strategy_config.get('min_volume', 1000)
        data['volume_ok'] = data['volume'] >= min_volume
        
        self.logger.info(f"Bullish signals: {data['is_bullish'].sum()}")
        self.logger.info(f"Bearish signals: {data['is_bearish'].sum()}")
        
        return data, ha_data
    
    def execute_trade(self, entry_data, entry_time, data, capital, position_size):
        """Execute a single trade with proper exit management"""
        direction = 'LONG' if entry_data['is_bullish'] else 'SHORT'
        entry_price = entry_data['close']
        
        # Calculate stop and target prices
        stop_loss_pct = self.risk_config.get('stop_loss_pct', 0.30)
        take_profit_pct = self.risk_config.get('take_profit_pct', 0.20)
        
        if direction == 'LONG':
            stop_price = entry_price * (1 - stop_loss_pct)
            target_price = entry_price * (1 + take_profit_pct)
        else:
            stop_price = entry_price * (1 + stop_loss_pct)
            target_price = entry_price * (1 - take_profit_pct)
        
        # Find exit
        max_hold_minutes = self.risk_config.get('max_hold_minutes', 20)
        max_exit_time = entry_time + timedelta(minutes=max_hold_minutes)
        
        # Get future bars within the hold period
        future_data = data[data.index > entry_time]
        future_data = future_data[future_data.index <= max_exit_time]
        
        exit_price = None
        exit_reason = "MAX_HOLD"
        exit_time = max_exit_time
        
        for idx, bar in future_data.iterrows():
            current_price = bar['close']
            
            # Check for stop loss
            if direction == 'LONG' and current_price <= stop_price:
                exit_price = current_price
                exit_reason = "STOP_LOSS"
                exit_time = idx
                break
            elif direction == 'SHORT' and current_price >= stop_price:
                exit_price = current_price
                exit_reason = "STOP_LOSS" 
                exit_time = idx
                break
            
            # Check for take profit
            if direction == 'LONG' and current_price >= target_price:
                exit_price = current_price
                exit_reason = "TAKE_PROFIT"
                exit_time = idx
                break
            elif direction == 'SHORT' and current_price <= target_price:
                exit_price = current_price
                exit_reason = "TAKE_PROFIT"
                exit_time = idx
                break
        
        # If no price-based exit, use the last price in the hold period
        if exit_price is None and len(future_data) > 0:
            exit_price = future_data.iloc[-1]['close']
            exit_time = future_data.index[-1]
        elif exit_price is None:
            # If no future data, use entry price (no trade)
            exit_price = entry_price
            exit_time = entry_time
        
        # Calculate P&L
        if direction == 'LONG':
            pnl_pct = (exit_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - exit_price) / entry_price
        
        commission = self.backtest_config.get('commission_per_trade', 0.65)
        pnl = position_size * pnl_pct - commission
        
        # Update capital
        capital += pnl
        
        trade_result = {
            'symbol': 'SPY',  # Will be set by caller
            'entry_time': entry_time,
            'exit_time': exit_time,
            'direction': direction,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'exit_reason': exit_reason,
            'hold_minutes': (exit_time - entry_time).total_seconds() / 60
        }
        
        return trade_result, capital
    
    def backtest(self, data, symbol):
        """Run the complete backtest"""
        self.logger.info(f"Starting backtest for {symbol}")
        
        # Precompute indicators
        data, ha_data = self.precompute_indicators(data)
        
        # Initialize tracking
        initial_capital = self.trading_config.get('initial_capital', 10000)
        capital = initial_capital
        position_size = self.risk_config.get('max_position_value', 200)
        trades = []
        
        # Find valid entry points
        valid_entries = (
            data['is_trading_hours'] & 
            data['volume_ok'] & 
            (data['is_bullish'] | data['is_bearish'])
        )
        
        entry_indices = data[valid_entries].index
        self.logger.info(f"Found {len(entry_indices)} potential entries")
        
        # Process each entry
        for i, entry_time in enumerate(entry_indices):
            if capital < position_size:
                self.logger.info("Insufficient capital - stopping backtest")
                break
                
            if i % 1000 == 0:
                self.logger.info(f"Processed {i}/{len(entry_indices)} entries")
            
            entry_data = data.loc[entry_time]
            
            # Execute trade
            trade_result, capital = self.execute_trade(
                entry_data, entry_time, data, capital, position_size
            )
            
            trade_result['symbol'] = symbol
            trades.append(trade_result)
        
        # Calculate results
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        total_pnl = sum(t['pnl'] for t in trades)
        
        # Analyze exit reasons
        stops = len([t for t in trades if t['exit_reason'] == "STOP_LOSS"])
        targets = len([t for t in trades if t['exit_reason'] == "TAKE_PROFIT"])
        time_exits = len([t for t in trades if t['exit_reason'] == "MAX_HOLD"])
        
        avg_hold = np.mean([t['hold_minutes'] for t in trades]) if trades else 0
        
        self.logger.info(f"Backtest completed: {total_trades} trades, {win_rate:.1%} win rate")
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'final_capital': capital,
            'stops': stops,
            'targets': targets,
            'time_exits': time_exits,
            'avg_hold_minutes': avg_hold,
            'trades': trades
        }