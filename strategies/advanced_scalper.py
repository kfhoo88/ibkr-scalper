# strategies/advanced_scalper.py

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AdvancedScalpingStrategy:
    """
    Comprehensive scalping strategy with advanced features:
    - Hedging mechanisms
    - Delta rolling  
    - Options awareness
    - Portfolio risk management
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {
            # Core strategy config
            'ha_lookback': 2,
            'min_trend_strength': 0.3,
            'ema_fast_period': 8,
            'ema_slow_period': 21,
            
            # Advanced features config
            'use_hedging': True,
            'use_delta_rolling': True,
            'max_portfolio_delta': 1000,
            'max_position_delta': 0.7,
            'roll_to_delta': 0.3,
            'hedge_threshold': 500,
            'volatility_adjustment': True,
            'iv_threshold': 0.4
        }
        
        # Portfolio state
        self.portfolio_positions = []
        self.portfolio_delta = 0
        self.portfolio_vega = 0
        self.portfolio_theta = 0
        
        # Risk limits
        self.delta_limit = self.config['max_portfolio_delta']
        self.vega_limit = 500
        self.theta_limit = -100  # Max theta decay per day
        
    # CORE STRATEGY METHODS (from our working strategy)
    def get_volume_threshold(self, trend_strength: float) -> float:
        """Dynamic volume threshold based on trend strength"""
        if trend_strength > 0.7:
            return 1.0
        elif trend_strength > 0.5:
            return 1.2
        else:
            return 1.5
    
    def calculate_heikin_ashi(self, df: pd.DataFrame) -> tuple:
        """Calculate Heikin Ashi candles"""
        df_lower = df.rename(columns=str.lower)
        
        ha_close = (df_lower['open'] + df_lower['high'] + df_lower['low'] + df_lower['close']) / 4
        ha_open = [(df_lower['open'].iloc[0] + df_lower['close'].iloc[0]) / 2]
        
        for i in range(1, len(df_lower)):
            ha_open.append((ha_open[i-1] + ha_close.iloc[i-1]) / 2)
        
        ha_open = pd.Series(ha_open, index=df_lower.index)
        ha_high = df_lower[['high', 'open', 'close']].max(axis=1)
        ha_low = df_lower[['low', 'open', 'close']].min(axis=1)
        
        return ha_open, ha_high, ha_low, ha_close
    
    def analyze_market(self, df: pd.DataFrame) -> Optional[Dict]:
        """Enhanced market analysis with dynamic volume thresholds"""
        try:
            # Convert to lowercase column names for consistency
            df_lower = df.rename(columns=str.lower)
            df_analysis = df_lower.copy()
            
            # Calculate Heikin Ashi
            ha_open, ha_high, ha_low, ha_close = self.calculate_heikin_ashi(df_analysis)
            df_analysis['ha_open'] = ha_open
            df_analysis['ha_close'] = ha_close
            df_analysis['ha_high'] = ha_high
            df_analysis['ha_low'] = ha_low
            
            # Calculate HA trend
            ha_trend = 0
            ha_lookback = self.config.get('ha_lookback', 2)
            if len(df_analysis) >= ha_lookback + 1:
                bullish_count = 0
                bearish_count = 0
                for i in range(1, ha_lookback + 1):
                    idx = -i
                    if df_analysis['ha_close'].iloc[idx] > df_analysis['ha_open'].iloc[idx]:
                        bullish_count += 1
                    elif df_analysis['ha_close'].iloc[idx] < df_analysis['ha_open'].iloc[idx]:
                        bearish_count += 1
                
                if bullish_count == ha_lookback:
                    ha_trend = 1
                elif bearish_count == ha_lookback:
                    ha_trend = -1
            
            # Check for HA doji
            ha_doji = abs(df_analysis['ha_close'].iloc[-1] - df_analysis['ha_open'].iloc[-1]) / (df_analysis['ha_high'].iloc[-1] - df_analysis['ha_low'].iloc[-1] + 1e-8) < 0.1
            
            # Calculate EMA trend (simplified)
            df_analysis['ema_fast'] = df_analysis['close'].ewm(span=8).mean()
            df_analysis['ema_slow'] = df_analysis['close'].ewm(span=21).mean()
            
            ema_trend = 0
            if len(df_analysis) > 1:
                current_fast = df_analysis['ema_fast'].iloc[-1]
                current_slow = df_analysis['ema_slow'].iloc[-1]
                prev_fast = df_analysis['ema_fast'].iloc[-2]
                prev_slow = df_analysis['ema_slow'].iloc[-2]
                
                if current_fast > current_slow and current_fast > prev_fast and current_slow > prev_slow:
                    ema_trend = 1
                elif current_fast < current_slow and current_fast < prev_fast and current_slow < prev_slow:
                    ema_trend = -1
            
            # Analyze volume
            recent_volume = df_analysis['volume'].tail(3).mean()
            avg_volume = df_analysis['volume'].tail(20).mean()
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Calculate trend strength (simplified)
            trend_strength = min(volume_ratio / 2.0, 1.0)  # Simplified for now
            
            # Get dynamic volume threshold
            dynamic_volume_threshold = self.get_volume_threshold(trend_strength)
            volume_ok = volume_ratio >= dynamic_volume_threshold
            
            # Generate signal
            signal = "HOLD"
            reason = []
            
            if trend_strength >= self.config['min_trend_strength']:
                bullish_conditions = [
                    ha_trend == 1,
                    ema_trend == 1,
                    trend_strength > 0.6,
                    not ha_doji,
                    volume_ok or trend_strength > 0.7
                ]
                
                bearish_conditions = [
                    ha_trend == -1,
                    ema_trend == -1,
                    trend_strength > 0.6,
                    not ha_doji,
                    volume_ok or trend_strength > 0.7
                ]
                
                if all(bullish_conditions):
                    signal = "BUY"
                elif all(bearish_conditions):
                    signal = "SELL"
            
            return {
                'signal': signal,
                'ha_trend': ha_trend,
                'ema_trend': ema_trend,
                'volume_ratio': volume_ratio,
                'trend_strength': trend_strength,
                'current_price': df_analysis['close'].iloc[-1],
                'timestamp': df_analysis.index[-1],
                'reason': '; '.join(reason) if reason else 'No clear signal'
            }
            
        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            return None
    
    # ADVANCED FEATURES
    def calculate_position_delta(self, position: Dict) -> float:
        """Calculate delta for a position"""
        if position['type'] == 'stock':
            return position['quantity'] * 1.0  # Stock delta is ~1.0
        elif position['type'] == 'call':
            return position['quantity'] * position.get('delta', 0.5)
        elif position['type'] == 'put':
            return position['quantity'] * position.get('delta', -0.5)
        elif position['type'] == 'spread':
            # For vertical spreads, calculate net delta
            return position['quantity'] * (position.get('long_delta', 0.5) - position.get('short_delta', 0.3))
        return 0.0
    
    def update_portfolio_greeks(self, new_position: Dict = None):
        """Update portfolio Greeks after position change"""
        if new_position:
            self.portfolio_positions.append(new_position)
        
        # Recalculate portfolio Greeks
        self.portfolio_delta = sum(self.calculate_position_delta(pos) for pos in self.portfolio_positions)
        # Simplified vega and theta calculations
        self.portfolio_vega = sum(pos.get('vega', 0) * pos.get('quantity', 0) for pos in self.portfolio_positions)
        self.portfolio_theta = sum(pos.get('theta', 0) * pos.get('quantity', 0) for pos in self.portfolio_positions)
    
    def should_hedge(self) -> Tuple[bool, str]:
        """Determine if hedging is needed"""
        reasons = []
        
        if abs(self.portfolio_delta) > self.config['hedge_threshold']:
            reasons.append(f"Delta exposure: {self.portfolio_delta:.0f}")
        
        if abs(self.portfolio_vega) > self.vega_limit:
            reasons.append(f"Vega exposure: {self.portfolio_vega:.0f}")
            
        if self.portfolio_theta < self.theta_limit:
            reasons.append(f"Theta decay: {self.portfolio_theta:.0f}")
        
        return len(reasons) > 0, "; ".join(reasons)
    
    def generate_hedge_trade(self) -> Optional[Dict]:
        """Generate hedge trade to manage risk"""
        should_hedge, reason = self.should_hedge()
        
        if not should_hedge:
            return None
        
        hedge_trade = {
            'type': 'hedge',
            'timestamp': datetime.now(),
            'reason': reason,
            'action': 'SELL' if self.portfolio_delta > 0 else 'BUY',
            'quantity': min(100, abs(int(self.portfolio_delta * 0.5))),  # Hedge 50% of delta
            'symbol': 'SPY'  # Use underlying for delta hedge
        }
        
        return hedge_trade
    
    def should_roll_position(self, position: Dict) -> Tuple[bool, str]:
        """Determine if position should be rolled"""
        if not self.config['use_delta_rolling']:
            return False, "Delta rolling disabled"
        
        current_delta = abs(self.calculate_position_delta(position))
        target_delta = self.config['roll_to_delta']
        
        if current_delta > self.config['max_position_delta']:
            return True, f"High delta: {current_delta:.2f} > {self.config['max_position_delta']}"
        
        # Roll based on time if close to expiration
        if position.get('dte', 365) < 7:  # Days to expiration < 7
            return True, f"Near expiration: {position.get('dte')} DTE"
            
        return False, "No roll needed"
    
    def generate_roll_instruction(self, position: Dict) -> Dict:
        """Generate roll instruction for high-delta position"""
        current_delta = self.calculate_position_delta(position)
        target_delta = self.config['roll_to_delta'] * (1 if current_delta > 0 else -1)
        
        roll_instruction = {
            'action': 'ROLL',
            'original_position': position,
            'target_delta': target_delta,
            'reason': f"Roll from delta {current_delta:.2f} to {target_delta:.2f}",
            'timestamp': datetime.now()
        }
        
        return roll_instruction
    
    def adjust_for_volatility(self, signal: Dict, current_iv: float) -> Dict:
        """Adjust trading signals based on implied volatility"""
        if not self.config['volatility_adjustment']:
            return signal
        
        iv_threshold = self.config['iv_threshold']
        
        # Reduce position size in high IV environments
        if current_iv > iv_threshold:
            adjusted_signal = signal.copy()
            if 'quantity' in adjusted_signal:
                adjusted_signal['quantity'] = int(adjusted_signal['quantity'] * 0.5)  # Reduce size by 50%
            adjusted_signal['reason'] = f"{signal.get('reason', '')} [IV adjusted: {current_iv:.2f}]"
            return adjusted_signal
        
        return signal
    
    def generate_trade_signal(self, df: pd.DataFrame, current_iv: float = 0.3) -> Dict:
        """Generate comprehensive trade signal with advanced features"""
        # Get base signal
        base_signal = self.analyze_market(df)
        
        if not base_signal or base_signal['signal'] == 'HOLD':
            return {'signal': 'HOLD', 'reason': 'No trade signal'}
        
        # Create trade structure
        trade = {
            'signal': base_signal['signal'],
            'price': base_signal['current_price'],
            'timestamp': base_signal['timestamp'],
            'trend_strength': base_signal['trend_strength'],
            'volume_ratio': base_signal['volume_ratio'],
            'reason': base_signal['reason'],
            'quantity': 100,  # Default quantity
            'type': 'stock'   # Default to stock trading
        }
        
        # Apply volatility adjustment
        trade = self.adjust_for_volatility(trade, current_iv)
        
        # Check if we need to hedge before new position
        hedge_trade = self.generate_hedge_trade()
        if hedge_trade:
            trade['hedge_required'] = True
            trade['hedge_trade'] = hedge_trade
            trade['reason'] += f" | {hedge_trade['reason']}"
        
        return trade

# Test the advanced strategy
def test_advanced_features():
    """Test the advanced features"""
    print("🧪 TESTING ADVANCED FEATURES")
    print("=" * 50)
    
    strategy = AdvancedScalpingStrategy()
    
    # Test portfolio management
    print("✅ AdvancedScalpingStrategy initialized")
    
    # Test delta calculation
    stock_position = {'type': 'stock', 'quantity': 100, 'symbol': 'SPY'}
    delta = strategy.calculate_position_delta(stock_position)
    print(f"✅ Stock delta calculation: {delta}")
    
    # Test portfolio Greeks
    strategy.update_portfolio_greeks(stock_position)
    print(f"✅ Portfolio delta: {strategy.portfolio_delta}")
    
    # Test hedging logic
    should_hedge, reason = strategy.should_hedge()
    print(f"✅ Hedging check: {should_hedge} - {reason}")
    
    # Test roll logic
    high_delta_position = {'type': 'call', 'quantity': 10, 'delta': 0.8, 'dte': 20}
    should_roll, roll_reason = strategy.should_roll_position(high_delta_position)
    print(f"✅ Roll check: {should_roll} - {roll_reason}")
    
    if should_roll:
        roll_instruction = strategy.generate_roll_instruction(high_delta_position)
        print(f"✅ Roll instruction: {roll_instruction}")

if __name__ == "__main__":
    test_advanced_features()