# advanced_backtester_controlled.py

import pandas as pd
import numpy as np
from datetime import datetime
import os
from typing import Dict, List, Optional, Tuple

class ControlledAdvancedScalpingStrategy:
    """
    Advanced scalping strategy with strict risk controls
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {
            # Core strategy
            'ha_lookback': 2,
            'min_trend_strength': 0.6,  # Higher threshold for better signals
            'ema_fast_period': 8,
            'ema_slow_period': 21,
            
            # STRICT Risk management
            'max_portfolio_delta': 200,   # Very conservative
            'max_position_size': 25,      # Small positions
            'daily_trade_limit': 10,      # Few trades per day
            'hedge_threshold': 150,       # Early hedging
        }
        
        # Portfolio state
        self.portfolio_positions = []
        self.portfolio_delta = 0
        self.daily_trades = 0
        self.current_date = None
        
    def reset_portfolio(self):
        """Reset portfolio state"""
        self.portfolio_positions = []
        self.portfolio_delta = 0
        self.daily_trades = 0
        self.current_date = None
        
    def update_date(self, timestamp):
        """Update date and reset daily counters if new day"""
        # Handle both datetime and string timestamps
        if isinstance(timestamp, (pd.Timestamp, datetime)):
            current_date = timestamp.date()
        elif isinstance(timestamp, str):
            current_date = pd.to_datetime(timestamp).date()
        else:
            # If it's an integer or other type, use a fixed date for testing
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
        max_shares = min(self.config['max_position_size'], 
                        int(self.config['max_portfolio_delta'] * 0.2))  # Use only 20% of delta limit
        return max(5, max_shares)  # Minimum 5 shares
    
    def calculate_heikin_ashi(self, df: pd.DataFrame) -> tuple:
        """Calculate Heikin Ashi candles"""
        df_lower = df.rename(columns=str.lower)
        
        ha_close = (df_lower['open'] + df_lower['high'] + df_lower['low'] + df_lower['close']) / 4
        ha_open = [(df_lower['open'].iloc[0] + df_lower['close'].iloc[0]) / 2]
        
        for i in range(1, len(df_lower)):
            ha_open.append((ha_open[i-1] + ha_close.iloc[i-1]) / 2)
        
        ha_open = pd.Series(ha_open, index=df_lower.index)
        return ha_open, ha_close
    
    def analyze_market(self, df: pd.DataFrame) -> Optional[Dict]:
        """Market analysis with higher quality signals"""
        try:
            df_lower = df.rename(columns=str.lower)
            df_analysis = df_lower.copy()
            
            # Calculate Heikin Ashi
            ha_open, ha_close = self.calculate_heikin_ashi(df_analysis)
            df_analysis['ha_open'] = ha_open
            df_analysis['ha_close'] = ha_close
            
            # Calculate HA trend (more conservative)
            ha_trend = 0
            if len(df_analysis) >= 3:  # 3-bar confirmation
                recent_ha = [df_analysis['ha_close'].iloc[-i] > df_analysis['ha_open'].iloc[-i] for i in range(1, 4)]
                if all(recent_ha):
                    ha_trend = 1
                elif not any(recent_ha):
                    ha_trend = -1
            
            # Calculate EMA trend
            df_analysis['ema_fast'] = df_analysis['close'].ewm(span=8).mean()
            df_analysis['ema_slow'] = df_analysis['close'].ewm(span=21).mean()
            
            ema_trend = 0
            if len(df_analysis) > 1:
                current_fast = df_analysis['ema_fast'].iloc[-1]
                current_slow = df_analysis['ema_slow'].iloc[-1]
                if current_fast > current_slow and current_fast > df_analysis['ema_fast'].iloc[-2]:
                    ema_trend = 1
                elif current_fast < current_slow and current_fast < df_analysis['ema_fast'].iloc[-2]:
                    ema_trend = -1
            
            # Volume analysis
            recent_volume = df_analysis['volume'].tail(3).mean()
            avg_volume = df_analysis['volume'].tail(20).mean()
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Stronger signal requirements
            signal = "HOLD"
            reason = []
            
            if ha_trend == 1 and ema_trend == 1 and volume_ratio > 1.2:
                signal = "BUY"
                reason.append("Strong bullish trend with volume")
            elif ha_trend == -1 and ema_trend == -1 and volume_ratio > 1.2:
                signal = "SELL" 
                reason.append("Strong bearish trend with volume")
            
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
    
    def update_portfolio_greeks(self, position: Dict):
        """Update portfolio Greeks"""
        self.portfolio_positions.append(position)
        
        # Calculate delta (simplified)
        if position['type'] == 'stock':
            delta = position['quantity'] * 1.0
        elif position.get('delta'):
            delta = position['quantity'] * position['delta']
        else:
            delta = position['quantity'] * 0.5  # Default for options
            
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
            
        hedge_quantity = min(25, abs(int(self.portfolio_delta * 0.3)))  # Hedge 30%
        action = 'SELL' if self.portfolio_delta > 0 else 'BUY'
        
        return {
            'action': action,
            'quantity': hedge_quantity,
            'reason': reason
        }
    
    def generate_trade_signal(self, df: pd.DataFrame) -> Dict:
        """Generate trade signal with strict risk controls"""
        base_signal = self.analyze_market(df)
        
        if not base_signal or base_signal['signal'] == 'HOLD':
            return {'signal': 'HOLD', 'reason': base_signal['reason'] if base_signal else 'No signal'}
        
        # Check risk limits
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
            'type': 'stock'
        }
        
        # Check hedging
        hedge_trade = self.generate_hedge_trade()
        if hedge_trade:
            trade['hedge_required'] = True
            trade['hedge_trade'] = hedge_trade
        
        # Increment trade count
        self.daily_trades += 1
        
        return trade

class ControlledAdvancedBacktester:
    """Backtester with strict risk controls"""
    
    def __init__(self, strategy: ControlledAdvancedScalpingStrategy, initial_capital: float = 50000):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.reset()
    
    def reset(self):
        self.capital = self.initial_capital
        self.trades = []
        self.hedge_trades = []
        self.portfolio_values = []
        self.timestamps = []
        
    def backtest(self, data: pd.DataFrame, symbol: str = "SPY") -> Dict:
        print(f"🚀 CONTROLLED ADVANCED BACKTEST: {symbol}")
        print("=" * 60)
        print("STRICT RISK CONTROLS:")
        print(f"• Max Portfolio Delta: {self.strategy.config['max_portfolio_delta']}")
        print(f"• Max Position Size: {self.strategy.config['max_position_size']} shares")
        print(f"• Daily Trade Limit: {self.strategy.config['daily_trade_limit']}")
        print(f"• Hedge Threshold: {self.strategy.config['hedge_threshold']}")
        print("=" * 60)
        
        self.reset()
        self.strategy.reset_portfolio()
        
        # Initialize tracking
        self.portfolio_values.append(self.initial_capital)
        self.timestamps.append(data.index[99] if len(data) > 99 else data.index[0])
        
        trade_count = 0
        hedge_count = 0
        
        for i in range(100, len(data)):
            current_data = data.iloc[:i+1].copy()
            current_price = current_data['close'].iloc[-1]
            current_time = current_data.index[-1]
            
            # Generate trade signal
            trade_signal = self.strategy.generate_trade_signal(current_data)
            
            if trade_signal['signal'] != 'HOLD':
                trade_count += 1
                print(f"\n🎯 Controlled Signal #{trade_count} at {current_time}:")
                print(f"   Signal: {trade_signal['signal']}")
                print(f"   Price: ${trade_signal['price']:.2f}")
                print(f"   Quantity: {trade_signal['quantity']} shares")
                print(f"   Reason: {trade_signal['reason']}")
                print(f"   Daily Trades: {self.strategy.daily_trades}/{self.strategy.config['daily_trade_limit']}")
                print(f"   Portfolio Delta: {self.strategy.portfolio_delta}")
                
                if trade_signal.get('hedge_required'):
                    hedge_count += 1
                    hedge_trade = trade_signal['hedge_trade']
                    print(f"   🛡️  HEDGE #{hedge_count}: {hedge_trade['action']} {hedge_trade['quantity']} shares")
                    self.hedge_trades.append(hedge_trade)
                
                # Execute trade
                self.execute_trade(trade_signal, current_time)
            
            # Update portfolio value
            current_value = self.calculate_portfolio_value(current_price)
            self.portfolio_values.append(current_value)
            self.timestamps.append(current_time)
        
        report = self.generate_report(symbol, trade_count, hedge_count)
        
        print(f"\n📈 CONTROLLED BACKTEST COMPLETE:")
        print(f"   Total Trades: {trade_count}")
        print(f"   Hedge Operations: {hedge_count}")
        print(f"   Final Portfolio Value: ${self.portfolio_values[-1]:,.2f}")
        print(f"   Total Return: {report['total_return_pct']:.2f}%")
        print(f"   Final Portfolio Delta: {self.strategy.portfolio_delta}")
        
        return report
    
    def execute_trade(self, trade_signal: Dict, timestamp):
        """Execute trade"""
        trade = {
            'timestamp': timestamp,
            'signal': trade_signal['signal'],
            'price': trade_signal['price'],
            'quantity': trade_signal['quantity'],
            'reason': trade_signal['reason']
        }
        self.trades.append(trade)
        
        # Update strategy portfolio
        position = {
            'type': 'stock',
            'quantity': trade_signal['quantity'],
            'entry_price': trade_signal['price'],
            'entry_time': timestamp
        }
        self.strategy.update_portfolio_greeks(position)
        
        # Update capital
        if trade_signal['signal'] == 'BUY':
            self.capital -= trade_signal['price'] * trade_signal['quantity']
        else:
            self.capital += trade_signal['price'] * trade_signal['quantity']
    
    def calculate_portfolio_value(self, current_price: float) -> float:
        """Calculate portfolio value"""
        unrealized_pnl = 0
        for trade in self.trades:
            if trade['signal'] == 'BUY':
                unrealized_pnl += (current_price - trade['price']) * trade['quantity']
        return self.capital + unrealized_pnl
    
    def generate_report(self, symbol: str, trade_count: int, hedge_count: int) -> Dict:
        """Generate performance report"""
        if not self.portfolio_values:
            total_return_pct = 0
        else:
            total_return_pct = ((self.portfolio_values[-1] - self.initial_capital) / self.initial_capital) * 100
        
        # Calculate metrics
        if len(self.portfolio_values) > 1:
            portfolio_series = pd.Series(self.portfolio_values, index=self.timestamps)
            returns = portfolio_series.pct_change().dropna()
            
            if len(returns) > 1 and returns.std() > 0:
                sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)
                max_drawdown = (portfolio_series / portfolio_series.cummax() - 1).min() * 100
            else:
                sharpe_ratio = 0
                max_drawdown = 0
        else:
            sharpe_ratio = 0
            max_drawdown = 0
        
        return {
            'symbol': symbol,
            'total_return_pct': total_return_pct,
            'total_trades': trade_count,
            'hedge_operations': hedge_count,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_pct': max_drawdown,
            'portfolio_delta': self.strategy.portfolio_delta,
            'final_portfolio_value': self.portfolio_values[-1] if self.portfolio_values else self.initial_capital
        }

def main():
    """Run controlled backtest"""
    print("🚀 RUNNING CONTROLLED ADVANCED BACKTEST")
    print("=" * 60)
    
    # Create controlled strategy
    strategy = ControlledAdvancedScalpingStrategy()
    backtester = ControlledAdvancedBacktester(strategy, initial_capital=50000)
    
    # Load data
    data = pd.read_csv('data/historical/SPY_1min_data.csv')
    
    # Handle datetime
    datetime_col = None
    for col in data.columns:
        if 'time' in col.lower() or 'date' in col.lower():
            datetime_col = col
            break
    
    if datetime_col:
        data[datetime_col] = pd.to_datetime(data[datetime_col])
        data = data.set_index(datetime_col)
    else:
        # Create datetime index if no datetime column
        data.index = pd.date_range(start='2024-01-01 09:30:00', periods=len(data), freq='1min')
    
    data = data.rename(columns=str.lower)
    
    print(f"📊 Data loaded: {len(data)} bars, {data.index[0]} to {data.index[-1]}")
    
    # Run backtest
    report = backtester.backtest(data, 'SPY')
    
    print(f"\n📈 CONTROLLED PERFORMANCE:")
    print(f"   Total Return: {report['total_return_pct']:.2f}%")
    print(f"   Max Drawdown: {report['max_drawdown_pct']:.2f}%")
    print(f"   Sharpe Ratio: {report['sharpe_ratio']:.2f}")
    print(f"   Total Trades: {report['total_trades']}")
    print(f"   Hedge Operations: {report['hedge_operations']}")
    print(f"   Portfolio Delta: {report['portfolio_delta']}")

if __name__ == "__main__":
    main()