import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from ..strategies.ha_ma_scalper import HAMAScalpingStrategy

class BacktestEngine:
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = []
        self.trade_history = []
        self.logger = logging.getLogger(__name__)
        
    def run_backtest(self, historical_data, strategy_params=None):
        """Run complete backtest on historical data"""
        self.logger.info("Starting backtest...")
        
        # Initialize strategy
        strategy = HAMAScalpingStrategy()
        if strategy_params:
            for key, value in strategy_params.items():
                setattr(strategy, key, value)
        
        # Convert historical data to DataFrame
        if not isinstance(historical_data, pd.DataFrame):
            df = self._convert_to_dataframe(historical_data)
        else:
            df = historical_data
            
        # Run simulation
        for i in range(50, len(df)):
            current_data = df.iloc[:i]
            current_price = current_data['close'].iloc[-1]
            
            # Generate signal
            signals = strategy.analyze_market_condition(current_data)
            trade_signal = strategy.generate_trade_signal(signals)
            
            # Execute trade if signal exists and no current position
            if trade_signal and not self.positions:
                self._execute_trade(trade_signal, current_price, signals, df.index[i])
                
            # Manage existing positions
            self._manage_positions(current_price, df.index[i])
            
        # Calculate performance
        performance = self._calculate_performance()
        return performance, self.trade_history
        
    def _execute_trade(self, signal, price, signals, timestamp):
        """Execute a trade in the backtest"""
        contract_size = 100  # Options are 100 shares
        option_price = price * 0.01  # Simulate 1% option price (simplified)
        quantity = 1  # Start with 1 contract
        
        cost = option_price * contract_size * quantity
        if cost > self.capital:
            return
            
        position = {
            'entry_time': timestamp,
            'signal': signal,
            'entry_price': option_price,
            'quantity': quantity,
            'signals': signals,
            'stop_loss': option_price * 0.8,  # 20% stop loss
            'take_profit': option_price * 1.15  # 15% profit target
        }
        
        self.positions.append(position)
        self.capital -= cost
        
        self.logger.info(f"Trade executed: {signal} at ${option_price:.2f}")
        
    def _manage_positions(self, current_underlying_price, timestamp):
        """Manage existing positions"""
        current_option_price = current_underlying_price * 0.01  # Simplified
        
        for position in self.positions[:]:
            pnl_ratio = (current_option_price - position['entry_price']) / position['entry_price']
            
            # Check stop loss
            if pnl_ratio <= -0.20:
                self._close_position(position, timestamp, 'stop_loss', pnl_ratio)
            # Check take profit
            elif pnl_ratio >= 0.15:
                self._close_position(position, timestamp, 'take_profit', pnl_ratio)
                
    def _close_position(self, position, timestamp, reason, pnl_ratio):
        """Close a position"""
        contract_size = 100
        pnl = pnl_ratio * position['entry_price'] * contract_size * position['quantity']
        
        trade_record = {
            'entry_time': position['entry_time'],
            'exit_time': timestamp,
            'signal': position['signal'],
            'entry_price': position['entry_price'],
            'exit_price': position['entry_price'] * (1 + pnl_ratio),
            'pnl': pnl,
            'pnl_percentage': pnl_ratio * 100,
            'reason': reason,
            'signals': position['signals']
        }
        
        self.trade_history.append(trade_record)
        self.positions.remove(position)
        self.capital += pnl  # Add PnL to capital
        
        self.logger.info(f"Position closed: {reason}, PnL: ${pnl:.2f} ({pnl_ratio*100:.1f}%)")
        
    def _calculate_performance(self):
        """Calculate backtest performance metrics"""
        if not self.trade_history:
            return {}
            
        trades = pd.DataFrame(self.trade_history)
        
        performance = {
            'total_trades': len(trades),
            'winning_trades': len(trades[trades['pnl'] > 0]),
            'losing_trades': len(trades[trades['pnl'] <= 0]),
            'total_pnl': trades['pnl'].sum(),
            'win_rate': len(trades[trades['pnl'] > 0]) / len(trades) * 100,
            'average_winner': trades[trades['pnl'] > 0]['pnl'].mean(),
            'average_loser': trades[trades['pnl'] <= 0]['pnl'].mean(),
            'largest_winner': trades['pnl'].max(),
            'largest_loser': trades['pnl'].min(),
            'profit_factor': abs(trades[trades['pnl'] > 0]['pnl'].sum() / trades[trades['pnl'] <= 0]['pnl'].sum()) if trades[trades['pnl'] <= 0]['pnl'].sum() != 0 else float('inf'),
            'final_capital': self.capital
        }
        
        return performance