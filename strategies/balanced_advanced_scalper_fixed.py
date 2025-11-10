# strategies/balanced_advanced_scalper_fixed.py

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class BalancedAdvancedScalpingStrategyFixed:
    """
    FIXED balanced strategy with proper integrated exit logic
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {
            # Core strategy
            'ha_lookback': 2,
            'min_trend_strength': 0.6,
            'ema_fast_period': 8,
            'ema_slow_period': 21,
            
            # Risk management
            'max_portfolio_delta': 200,
            'max_position_size': 20,  # Reduced from 25
            'daily_trade_limit': 10,  # Reduced from 15
            'hedge_threshold': 100,   # More aggressive hedging
            
            # EXIT STRATEGY
            'stop_loss_pct': 0.005,   # 0.5% stop loss (tighter)
            'take_profit_pct': 0.015, # 1.5% take profit
            'max_hold_time': 20,      # 20 minutes max (shorter)
        }
        
        # Portfolio state
        self.portfolio_positions = []
        self.open_trades = []  # Track ALL open trades for exit logic
        self.portfolio_delta = 0
        self.daily_trades = 0
        self.current_date = None
        
    def reset_portfolio(self):
        """Reset portfolio state"""
        self.portfolio_positions = []
        self.open_trades = []
        self.portfolio_delta = 0
        self.daily_trades = 0
        self.current_date = None
        
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
        """Calculate conservative position size"""
        # More conservative sizing
        available_delta = self.config['max_portfolio_delta'] - abs(self.portfolio_delta)
        max_shares = min(self.config['max_position_size'], 
                        int(available_delta * 0.3))  # Use only 30% of available delta
        return max(5, max_shares)
    
    def check_exit_signals(self, current_price: float, current_time) -> List[Dict]:
        """Check ALL open trades for exit conditions"""
        exit_signals = []
        
        for trade in self.open_trades[:]:  # Copy for safe iteration
            should_exit, reason = self.should_exit_position(trade, current_price, current_time)
            if should_exit:
                # Create exit signal
                exit_signal = {
                    'signal': 'SELL' if trade['signal'] == 'BUY' else 'BUY',
                    'price': current_price,
                    'timestamp': current_time,
                    'quantity': trade['quantity'],
                    'reason': f"EXIT: {reason}",
                    'is_exit': True,
                    'original_trade': trade
                }
                exit_signals.append(exit_signal)
                
                # Remove from open trades
                self.open_trades.remove(trade)
                
                # Update portfolio delta for the exit
                if trade['signal'] == 'BUY':
                    self.portfolio_delta -= trade['quantity']
                else:  # SELL (short)
                    self.portfolio_delta += trade['quantity']
        
        return exit_signals
    
    def should_exit_position_old(self, trade: Dict, current_price: float, current_time) -> Tuple[bool, str]:
        """Check if we should exit an open position"""
        entry_price = trade['price']
        
        if trade['signal'] == 'BUY':
            # Long position
            pnl_pct = (current_price - entry_price) / entry_price
            
            if pnl_pct <= -self.config['stop_loss_pct']:
                return True, f"Stop Loss: {pnl_pct:.2%}"
            elif pnl_pct >= self.config['take_profit_pct']:
                return True, f"Take Profit: {pnl_pct:.2%}"
                
        elif trade['signal'] == 'SELL':
            # Short position
            pnl_pct = (entry_price - current_price) / entry_price
            
            if pnl_pct <= -self.config['stop_loss_pct']:
                return True, f"Stop Loss: {pnl_pct:.2%}"
            elif pnl_pct >= self.config['take_profit_pct']:
                return True, f"Take Profit: {pnl_pct:.2%}"
        
        # Time-based exit for both long and short
        hold_time = (current_time - trade['timestamp']).total_seconds() / 60
        if hold_time > self.config['max_hold_time']:
            return True, f"Time Exit: {hold_time:.0f}min"
        
        return False, "Hold"

    def should_exit_position(self, trade, current_price, current_time):
        """Enhanced exit logic with proper time handling"""
        if trade['timestamp'] is None:
            return True, "Invalid trade timestamp"
        
        # Convert timestamp to datetime if it's stored as integer/string
        if isinstance(trade['timestamp'], (int, float)):
            trade_time = pd.to_datetime(trade['timestamp'], unit='s')
        else:
            trade_time = trade['timestamp']
        
        # Calculate hold time in minutes
        hold_time = (current_time - trade_time).total_seconds() / 60
        
        # Exit conditions
        current_pnl = (current_price - trade['price']) / trade['price'] * 100
        current_pnl = current_pnl * (-1 if trade['direction'] == 'SHORT' else 1)
        
        # 1. Time-based exit (20 minutes max)
        if hold_time >= 20:
            return True, f"Max hold time reached: {hold_time:.1f} minutes"
        
        # 2. Stop loss (0.5%)
        if current_pnl <= -0.5:
            return True, f"Stop loss triggered: {current_pnl:.2f}%"
        
        # 3. Take profit (1.5%)
        if current_pnl >= 1.5:
            return True, f"Take profit reached: {current_pnl:.2f}%"
        
        return False, "Hold"
        
    def analyze_market(self, df: pd.DataFrame) -> Optional[Dict]:
        """Improved market analysis with trend filtering"""
        try:
            df_lower = df.rename(columns=str.lower)
            df_analysis = df_lower.copy()
            
            # Need minimum data
            if len(df_analysis) < 50:
                return None
            
            # Calculate Heikin Ashi
            ha_open, ha_close = self.calculate_heikin_ashi(df_analysis)
            df_analysis['ha_open'] = ha_open
            df_analysis['ha_close'] = ha_close
            
            # Calculate trends with stronger filters
            ha_trend = self.calculate_ha_trend(df_analysis)
            ema_trend = self.calculate_ema_trend(df_analysis)
            price_trend = self.calculate_price_trend(df_analysis)
            
            # Volume analysis
            recent_volume = df_analysis['volume'].tail(3).mean()
            avg_volume = df_analysis['volume'].tail(20).mean()
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
            
            # STRICTER ENTRY CONDITIONS
            signal = "HOLD"
            reason = []
            
            # Bullish entry - multiple confirmations required
            if (ha_trend == 1 and ema_trend == 1 and price_trend == 1 and 
                volume_ratio > 1.5 and self.is_uptrend_confirming(df_analysis)):
                signal = "BUY"
                reason.append("Strong bullish setup")
                
            # Bearish entry - multiple confirmations required
            elif (ha_trend == -1 and ema_trend == -1 and price_trend == -1 and 
                  volume_ratio > 1.5 and self.is_downtrend_confirming(df_analysis)):
                signal = "SELL"
                reason.append("Strong bearish setup")
            
            return {
                'signal': signal,
                'price': df_analysis['close'].iloc[-1],
                'timestamp': df_analysis.index[-1],
                'volume_ratio': volume_ratio,
                'reason': '; '.join(reason) if reason else 'No qualified setup'
            }
            
        except Exception as e:
            return None
    
    def is_uptrend_confirming(self, df_analysis) -> bool:
        """Check if uptrend has multiple confirmations"""
        # Price above 20-period MA
        ma_20 = df_analysis['close'].rolling(20).mean().iloc[-1]
        current_price = df_analysis['close'].iloc[-1]
        
        # Recent higher highs
        recent_highs = df_analysis['high'].tail(5)
        highs_rising = recent_highs.is_monotonic_increasing
        
        return current_price > ma_20 and highs_rising
    
    def is_downtrend_confirming(self, df_analysis) -> bool:
        """Check if downtrend has multiple confirmations"""
        # Price below 20-period MA
        ma_20 = df_analysis['close'].rolling(20).mean().iloc[-1]
        current_price = df_analysis['close'].iloc[-1]
        
        # Recent lower lows
        recent_lows = df_analysis['low'].tail(5)
        lows_falling = recent_lows.is_monotonic_decreasing
        
        return current_price < ma_20 and lows_falling
    
    def calculate_price_trend(self, df_analysis) -> int:
        """Calculate price trend using multiple timeframes"""
        if len(df_analysis) < 10:
            return 0
            
        # Short-term trend (5 periods)
        short_trend = 1 if df_analysis['close'].iloc[-1] > df_analysis['close'].iloc[-5] else -1
        
        # Medium-term trend (10 periods)  
        med_trend = 1 if df_analysis['close'].iloc[-1] > df_analysis['close'].iloc[-10] else -1
        
        # Combined trend
        if short_trend == 1 and med_trend == 1:
            return 1
        elif short_trend == -1 and med_trend == -1:
            return -1
        return 0
    
    def calculate_ha_trend(self, df_analysis) -> int:
        """Calculate Heikin Ashi trend"""
        if len(df_analysis) < 3:
            return 0
            
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
            delta = position['quantity'] * (1.0 if position.get('signal') == 'BUY' else -1.0)
        else:
            delta = position['quantity'] * position.get('delta', 0.5)
            
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
            
        hedge_quantity = min(self.config['max_position_size'], 
                           abs(int(self.portfolio_delta * 0.4)))  # Hedge 40%
        action = 'SELL' if self.portfolio_delta > 0 else 'BUY'
        
        return {
            'action': action,
            'quantity': hedge_quantity,
            'reason': reason
        }
    
    def generate_trade_signal(self, df: pd.DataFrame) -> Dict:
        """Generate trade signal with integrated exit logic"""
        current_price = df['close'].iloc[-1]
        current_time = df.index[-1]
        
        # FIRST: Check for exit signals on ALL open trades
        exit_signals = self.check_exit_signals(current_price, current_time)
        if exit_signals:
            return exit_signals[0]  # Return first exit signal
        
        # SECOND: Check for new entry signals
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
        
        # Update portfolio
        self.update_portfolio_greeks(trade)
        
        # Check hedging
        hedge_trade = self.generate_hedge_trade()
        if hedge_trade:
            trade['hedge_required'] = True
            trade['hedge_trade'] = hedge_trade
        
        # Increment trade count
        self.daily_trades += 1
        
        return trade