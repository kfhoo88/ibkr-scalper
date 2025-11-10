# strategies/advanced_scalper_optimized.py

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class OptimizedAdvancedScalpingStrategy:
    """
    Optimized advanced scalping strategy with proper risk controls
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {
            # Core strategy
            'ha_lookback': 2,
            'min_trend_strength': 0.5,  # Increased for better signals
            'ema_fast_period': 8,
            'ema_slow_period': 21,
            
            # Risk management
            'use_hedging': True,
            'max_portfolio_delta': 500,  # Drastically reduced
            'max_position_size': 50,     # Maximum shares per trade
            'daily_trade_limit': 20,     # Max trades per day
            'hedge_threshold': 300,      # Lower hedging threshold
            
            # Advanced features
            'use_delta_rolling': True,
            'max_position_delta': 0.6,
            'roll_to_delta': 0.3,
            'volatility_adjustment': True,
            'iv_threshold': 0.4
        }
        
        # Portfolio state with better controls
        self.portfolio_positions = []
        self.portfolio_delta = 0
        self.portfolio_vega = 0
        self.portfolio_theta = 0
        self.daily_trade_count = 0
        self.last_trade_date = None
        
        # Risk limits
        self.delta_limit = self.config['max_portfolio_delta']
        self.vega_limit = 200
        self.theta_limit = -50
        
    def reset_portfolio(self):
        """Reset portfolio state"""
        self.portfolio_positions = []
        self.portfolio_delta = 0
        self.portfolio_vega = 0
        self.portfolio_theta = 0
        self.daily_trade_count = 0
        
    def can_trade_today(self) -> Tuple[bool, str]:
        """Check if we can execute more trades today"""
        if self.last_trade_date != datetime.now().date():
            self.daily_trade_count = 0
            self.last_trade_date = datetime.now().date()
            
        if self.daily_trade_count >= self.config['daily_trade_limit']:
            return False, f"Daily trade limit reached: {self.daily_trade_count}"
            
        return True, "OK"
    
    def calculate_position_size(self, price: float, trend_strength: float) -> int:
        """Calculate position size with risk controls"""
        base_size = min(self.config['max_position_size'], 
                       int(self.config['max_portfolio_delta'] * 0.1 / price))
        
        # Adjust based on trend strength
        if trend_strength > 0.7:
            size = base_size
        elif trend_strength > 0.5:
            size = int(base_size * 0.7)
        else:
            size = int(base_size * 0.3)
            
        return max(5, size)  # Minimum 5 shares
    
    # ... (keep all the existing methods from AdvancedScalpingStrategy but add risk controls)
    
    def generate_trade_signal(self, df: pd.DataFrame, current_iv: float = 0.3) -> Dict:
        """Generate trade signal with comprehensive risk controls"""
        # Check daily trade limit
        can_trade, reason = self.can_trade_today()
        if not can_trade:
            return {'signal': 'HOLD', 'reason': reason}
        
        # Get base signal
        base_signal = self.analyze_market(df)
        
        if not base_signal or base_signal['signal'] == 'HOLD':
            return {'signal': 'HOLD', 'reason': 'No trade signal'}
        
        # Check portfolio risk before new position
        if abs(self.portfolio_delta) > self.config['max_portfolio_delta'] * 0.8:
            return {'signal': 'HOLD', 'reason': f"High portfolio delta: {self.portfolio_delta}"}
        
        # Calculate position size
        quantity = self.calculate_position_size(
            base_signal['current_price'], 
            base_signal['trend_strength']
        )
        
        # Create trade
        trade = {
            'signal': base_signal['signal'],
            'price': base_signal['current_price'],
            'timestamp': base_signal['timestamp'],
            'trend_strength': base_signal['trend_strength'],
            'volume_ratio': base_signal['volume_ratio'],
            'reason': base_signal['reason'],
            'quantity': quantity,
            'type': 'stock'
        }
        
        # Apply volatility adjustment
        trade = self.adjust_for_volatility(trade, current_iv)
        
        # Check if we need to hedge
        hedge_trade = self.generate_hedge_trade()
        if hedge_trade:
            trade['hedge_required'] = True
            trade['hedge_trade'] = hedge_trade
            trade['reason'] += f" | {hedge_trade['reason']}"
        
        # Increment daily trade count
        self.daily_trade_count += 1
        
        return trade

# Create optimized backtester
def create_optimized_backtest():
    """Run optimized backtest with proper risk controls"""
    print("🚀 OPTIMIZED ADVANCED BACKTEST")
    print("=" * 60)
    print("Key Improvements:")
    print("• Max Portfolio Delta: 500 (was unlimited)")
    print("• Max Position Size: 50 shares") 
    print("• Daily Trade Limit: 20 trades")
    print("• Better Position Sizing")
    print("=" * 60)
    
    from advanced_backtester_fixed import AdvancedBacktester
    strategy = OptimizedAdvancedScalpingStrategy()
    backtester = AdvancedBacktester(strategy, initial_capital=50000)
    
    # Load and run with same data
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
    
    print(f"\n📈 OPTIMIZED PERFORMANCE:")
    print(f"   Total Return: {report['total_return_pct']:.2f}%")
    print(f"   Max Drawdown: {report['max_drawdown_pct']:.2f}%")
    print(f"   Total Trades: {report['total_trades']}")
    print(f"   Hedge Operations: {report['hedge_operations']}")
    print(f"   Portfolio Delta: {report['portfolio_delta']:.0f}")

if __name__ == "__main__":
    create_optimized_backtest()