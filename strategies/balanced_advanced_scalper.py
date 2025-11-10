# strategies/balanced_advanced_scalper.py

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class BalancedAdvancedScalpingStrategy:
    """
    Balanced strategy with proper entry AND exit logic
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {
            # Core strategy - MORE BALANCED
            'ha_lookback': 2,
            'min_trend_strength': 0.5,
            'ema_fast_period': 8,
            'ema_slow_period': 21,
            
            # Risk management
            'max_portfolio_delta': 200,
            'max_position_size': 25,
            'daily_trade_limit': 15,
            'hedge_threshold': 150,
            
            # EXIT STRATEGY - NEW
            'stop_loss_pct': 0.01,      # 1% stop loss
            'take_profit_pct': 0.02,    # 2% take profit  
            'max_hold_time': 30,        # 30 minutes max
            'use_trailing_stop': True,
        }
        
        # Portfolio state
        self.portfolio_positions = []
        self.portfolio_delta = 0
        self.daily_trades = 0
        self.current_date = None
        self.open_trades = []  # Track open trades for exit logic
        
    def reset_portfolio(self):
        """Reset portfolio state"""
        self.portfolio_positions = []
        self.portfolio_delta = 0
        self.daily_trades = 0
        self.current_date = None
        self.open_trades = []
        
    def update_date(self, timestamp):
        """Update date and reset daily counters if new day"""
        if isinstance(timestamp, (pd.Timestamp, datetime)):
            current_date = timestamp.date()
        elif isinstance(timestamp, str):
            current_date = pd.to_datetime(timestamp).date()
        else:
            current_date = datetime.now().date()
            
        if current_date != self.current_date:
            self.daily_trades = 0
            self.current_date = current_date
    
    def can_trade(self, timestamp) -> Tuple[bool, str]:
        """Check if we can trade based on risk limits"""
        self.update_date(timestamp)
        
        if self.daily_trades >= self.config['daily_trade_limit']:
            return False, f"Daily limit: {self.daily_trades}/{self.config['daily_trade_limit']}"
            
        if abs(self.portfolio_delta) >= self.config['max_portfolio_delta']:
            return False, f"Delta limit: {self.portfolio_delta}/{self.config['max_portfolio_delta']}"
            
        return True, "OK"
    
    def calculate_position_size(self, price: float) -> int:
        """Calculate position size"""
        max_shares = min(self.config['max_position_size'], 
                        int(self.config['max_portfolio_delta'] * 0.2))
        return max(5, max_shares)
    
    def should_exit_position(self, trade: Dict, current_price: float, current_time) -> Tuple[bool, str]:
        """Check if we should exit an open position"""
        if trade['signal'] == 'BUY':
            # Calculate P&L percentage
            pnl_pct = (current_price - trade['price']) / trade['price']
            
            # Stop loss check
            if pnl_pct <= -self.config['stop_loss_pct']:
                return True, f"Stop loss hit: {pnl_pct:.2%}"
                
            # Take profit check
            if pnl_pct >= self.config['take_profit_pct']:
                return True, f"Take profit: {pnl_pct:.2%}"
                
            # Time-based exit
            hold_time = (current_time - trade['timestamp']).total_seconds() / 60
            if hold_time > self.config['max_hold_time']:
                return True, f"Max hold time: {hold_time:.0f}min"
                
        elif trade['signal'] == 'SELL':  # For short positions
            pnl_pct = (trade['price'] - current_price) / trade['price']
            
            if pnl_pct <= -self.config['stop_loss_pct']:
                return True, f"Stop loss hit: {pnl_pct:.2%}"
            if pnl_pct >= self.config['take_profit_pct']:
                return True, f"Take profit: {pnl_pct:.2%}"
                
            hold_time = (current_time - trade['timestamp']).total_seconds() / 60
            if hold_time > self.config['max_hold_time']:
                return True, f"Max hold time: {hold_time:.0f}min"
        
        return False, "Hold"
    
    def analyze_market(self, df: pd.DataFrame) -> Optional[Dict]:
        """Improved market analysis with BOTH entry and exit signals"""
        try:
            df_lower = df.rename(columns=str.lower)
            df_analysis = df_lower.copy()
            
            # Calculate Heikin Ashi
            ha_open, ha_close = self.calculate_heikin_ashi(df_analysis)
            df_analysis['ha_open'] = ha_open
            df_analysis['ha_close'] = ha_close
            
            # Calculate trends
            ha_trend = self.calculate_ha_trend(df_analysis)
            ema_trend = self.calculate_ema_trend(df_analysis)
            
            # Volume analysis
            recent_volume = df_analysis['volume'].tail(3).mean()
            avg_volume = df_analysis['volume'].tail(20).mean()
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
            
            # IMPROVED SIGNAL LOGIC - More balanced
            signal = "HOLD"
            reason = []
            
            # Bullish entry - require stronger confirmation
            if (ha_trend == 1 and ema_trend == 1 and volume_ratio > 1.3 and 
                len(df_analysis) > 50 and df_analysis['close'].iloc[-1] > df_analysis['close'].iloc[-20]):
                signal = "BUY"
                reason.append("Strong bullish confirmation")
                
            # Bearish entry - also require strong confirmation  
            elif (ha_trend == -1 and ema_trend == -1 and volume_ratio > 1.3 and
                  len(df_analysis) > 50 and df_analysis['close'].iloc[-1] < df_analysis['close'].iloc[-20]):
                signal = "SELL"
                reason.append("Strong bearish confirmation")
            
            return {
                'signal': signal,
                'price': df_analysis['close'].iloc[-1],
                'timestamp': df_analysis.index[-1],
                'volume_ratio': volume_ratio,
                'reason': '; '.join(reason) if reason else 'No strong signal'
            }
            
        except Exception as e:
            print(f"Error in analyze_market: {e}")
            return None
    
    def calculate_ha_trend(self, df_analysis) -> int:
        """Calculate Heikin Ashi trend"""
        if len(df_analysis) < 3:
            return 0
            
        # 3-bar trend with confirmation
        recent_bullish = sum(1 for i in range(1, 4) 
                           if df_analysis['ha_close'].iloc[-i] > df_analysis['ha_open'].iloc[-i])
        recent_bearish = sum(1 for i in range(1, 4) 
                           if df_analysis['ha_close'].iloc[-i] < df_analysis['ha_open'].iloc[-i])
        
        if recent_bullish >= 2:
            return 1
        elif recent_bearish >= 2:
            return -1
        return 0
    
    def calculate_ema_trend(self, df_analysis) -> int:
        """Calculate EMA trend"""
        if len(df_analysis) < 2:
            return 0
            
        df_analysis['ema_fast'] = df_analysis['close'].ewm(span=8).mean()
        df_analysis['ema_slow'] = df_analysis['close'].ewm(span=21).mean()
        
        current_fast = df_analysis['ema_fast'].iloc[-1]
        current_slow = df_analysis['ema_slow'].iloc[-1]
        prev_fast = df_analysis['ema_fast'].iloc[-2]
        
        if current_fast > current_slow and current_fast > prev_fast:
            return 1
        elif current_fast < current_slow and current_fast < prev_fast:
            return -1
        return 0
    
    def calculate_heikin_ashi(self, df: pd.DataFrame) -> tuple:
        """Calculate Heikin Ashi candles"""
        df_lower = df.rename(columns=str.lower)
        
        ha_close = (df_lower['open'] + df_lower['high'] + df_lower['low'] + df_lower['close']) / 4
        ha_open = [(df_lower['open'].iloc[0] + df_lower['close'].iloc[0]) / 2]
        
        for i in range(1, len(df_lower)):
            ha_open.append((ha_open[i-1] + ha_close.iloc[i-1]) / 2)
        
        ha_open = pd.Series(ha_open, index=df_lower.index)
        return ha_open, ha_close
    
    def update_portfolio_greeks(self, position: Dict):
        """Update portfolio Greeks"""
        self.portfolio_positions.append(position)
        
        if position['type'] == 'stock':
            delta = position['quantity'] * 1.0
        elif position.get('delta'):
            delta = position['quantity'] * position['delta']
        else:
            delta = position['quantity'] * 0.5
            
        self.portfolio_delta += delta
    
    def should_hedge(self) -> Tuple[bool, str]:
        """Check if hedging is needed"""
        if abs(self.portfolio_delta) > self.config['hedge_threshold']:
            return True, f"Delta exposure: {self.portfolio_delta}"
        return False, ""
    
    def generate_hedge_trade(self) -> Optional[Dict]:
        """Generate hedge trade"""
        should_hedge, reason = self.should_hedge()
        if not should_hedge:
            return None
            
        hedge_quantity = min(25, abs(int(self.portfolio_delta * 0.3)))
        action = 'SELL' if self.portfolio_delta > 0 else 'BUY'
        
        return {
            'action': action,
            'quantity': hedge_quantity,
            'reason': reason
        }
    
    def generate_trade_signal(self, df: pd.DataFrame) -> Dict:
        """Generate trade signal with exit logic"""
        # First check if we should exit any open positions
        current_price = df['close'].iloc[-1]
        current_time = df.index[-1]
        
        exit_signals = []
        for trade in self.open_trades[:]:  # Copy for safe iteration
            should_exit, reason = self.should_exit_position(trade, current_price, current_time)
            if should_exit:
                exit_signals.append({
                    'signal': 'SELL' if trade['signal'] == 'BUY' else 'BUY',  # Opposite to close
                    'price': current_price,
                    'timestamp': current_time,
                    'quantity': trade['quantity'],
                    'reason': f"Exit: {reason}",
                    'is_exit': True,
                    'original_trade': trade
                })
                # Remove from open trades
                self.open_trades.remove(trade)
        
        # Return exit signal if we have one
        if exit_signals:
            return exit_signals[0]  # Return first exit signal
        
        # Otherwise check for new entry
        base_signal = self.analyze_market(df)
        
        if not base_signal or base_signal['signal'] == 'HOLD':
            return {'signal': 'HOLD', 'reason': base_signal['reason'] if base_signal else 'No signal'}
        
        # Check risk limits for new entry
        can_trade, reason = self.can_trade(base_signal['timestamp'])
        if not can_trade:
            return {'signal': 'HOLD', 'reason': reason}
        
        # Calculate position size
        quantity = self.calculate_position_size(base_signal['price'])
        
        trade = {
            'signal': base_signal['signal'],
            'price': base_signal['price'],
            'timestamp': base_signal['timestamp'],
            'volume_ratio': base_signal['volume_ratio'],
            'reason': base_signal['reason'],
            'quantity': quantity,
            'type': 'stock',
            'is_exit': False
        }
        
        # Add to open trades for tracking
        self.open_trades.append(trade)
        
        # Check hedging
        hedge_trade = self.generate_hedge_trade()
        if hedge_trade:
            trade['hedge_required'] = True
            trade['hedge_trade'] = hedge_trade
        
        # Increment trade count
        self.daily_trades += 1
        
        return trade

# Update the backtester to handle exit signals
def create_balanced_backtest():
    """Run balanced backtest with exit logic"""
    print("🚀 BALANCED ADVANCED BACKTEST")
    print("=" * 60)
    print("KEY IMPROVEMENTS:")
    print("• Exit Strategy: 1% stop loss, 2% take profit")
    print("• Time-based exits: 30min max hold")
    print("• Better signal confirmation")
    print("• Both long and short signals")
    print("=" * 60)
    
    from advanced_backtester_controlled import ControlledAdvancedBacktester
    strategy = BalancedAdvancedScalpingStrategy()
    backtester = ControlledAdvancedBacktester(strategy, initial_capital=50000)
    
    # Load data
    data = pd.read_csv('data/historical/SPY_1min_data.csv')
    datetime_col = None
    for col in data.columns:
        if 'time' in col.lower() or 'date' in col.lower():
            datetime_col = col
            break
    
    if datetime_col:
        data[datetime_col] = pd.to_datetime(data[datetime_col])
        data = data.set_index(datetime_col)
    
    data = data.rename(columns=str.lower)
    
    report = backtester.backtest(data, 'SPY')
    
    print(f"\n📈 BALANCED PERFORMANCE:")
    print(f"   Total Return: {report['total_return_pct']:.2f}%")
    print(f"   Max Drawdown: {report['max_drawdown_pct']:.2f}%")
    print(f"   Total Trades: {report['total_trades']}")
    print(f"   Portfolio Delta: {report['portfolio_delta']}")

if __name__ == "__main__":
    create_balanced_backtest()