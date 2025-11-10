# advanced_backtester_fixed.py

import pandas as pd
import numpy as np
from datetime import datetime
import os
from typing import Dict, List
from strategies.advanced_scalper import AdvancedScalpingStrategy

class AdvancedBacktester:
    """Backtester with support for advanced features"""
    
    def __init__(self, strategy: AdvancedScalpingStrategy, initial_capital: float = 50000):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.reset()
    
    def reset(self):
        """Reset backtester state"""
        self.capital = self.initial_capital
        self.positions = []
        self.trades = []
        self.hedge_trades = []
        self.portfolio_values = []  # Track portfolio value over time
        self.timestamps = []  # Track timestamps
        
    def backtest(self, data: pd.DataFrame, symbol: str = "SPY") -> Dict:
        """Run advanced backtest"""
        print(f"🚀 ADVANCED BACKTEST: {symbol}")
        print("=" * 60)
        print(f"Features: Hedging, Delta Rolling, Portfolio Management")
        print("=" * 60)
        
        self.reset()
        trade_count = 0
        hedge_count = 0
        
        # Initialize portfolio tracking
        self.portfolio_values.append(self.initial_capital)
        self.timestamps.append(data.index[99] if len(data) > 99 else data.index[0])
        
        for i in range(100, len(data)):
            current_data = data.iloc[:i+1].copy()
            current_price = current_data['close'].iloc[-1]
            current_time = current_data.index[-1]
            
            # Generate trade signal with advanced features
            trade_signal = self.strategy.generate_trade_signal(current_data)
            
            if trade_signal['signal'] != 'HOLD':
                trade_count += 1
                print(f"\n🎯 Advanced Signal #{trade_count} at {current_time}:")
                print(f"   Signal: {trade_signal['signal']}")
                print(f"   Price: ${trade_signal['price']:.2f}")
                print(f"   Trend Strength: {trade_signal['trend_strength']:.2f}")
                print(f"   Volume Ratio: {trade_signal['volume_ratio']:.2f}")
                print(f"   Reason: {trade_signal['reason']}")
                
                # Check for hedging
                if trade_signal.get('hedge_required'):
                    hedge_count += 1
                    hedge_trade = trade_signal['hedge_trade']
                    print(f"   🛡️  HEDGE #{hedge_count}: {hedge_trade['action']} {hedge_trade['quantity']} shares")
                    print(f"      Reason: {hedge_trade['reason']}")
                    self.hedge_trades.append(hedge_trade)
                
                # Execute the main trade
                self.execute_trade(trade_signal, current_time)
            
            # Update portfolio tracking
            current_portfolio_value = self.calculate_portfolio_value(current_price)
            self.portfolio_values.append(current_portfolio_value)
            self.timestamps.append(current_time)
        
        # Generate final report
        report = self.generate_report(symbol, data, trade_count, hedge_count)
        
        print(f"\n📈 ADVANCED BACKTEST COMPLETE:")
        print(f"   Total Trades: {trade_count}")
        print(f"   Hedge Operations: {hedge_count}")
        print(f"   Final Portfolio Value: ${self.portfolio_values[-1]:,.2f}")
        print(f"   Total Return: {report['total_return_pct']:.2f}%")
        print(f"   Final Portfolio Delta: {self.strategy.portfolio_delta:.0f}")
        
        return report
    
    def calculate_portfolio_value(self, current_price: float) -> float:
        """Calculate current portfolio value"""
        # Simple calculation: capital + unrealized P&L from long positions
        unrealized_pnl = 0
        for trade in self.trades:
            if trade['signal'] == 'BUY':
                # For long positions, calculate profit based on current price
                position_value = (current_price - trade['price']) * trade.get('quantity', 100)
                unrealized_pnl += position_value
        
        return self.capital + unrealized_pnl
    
    def execute_trade(self, trade_signal: Dict, timestamp: datetime):
        """Execute trade with position tracking"""
        trade = {
            'timestamp': timestamp,
            'signal': trade_signal['signal'],
            'price': trade_signal['price'],
            'quantity': trade_signal.get('quantity', 100),
            'type': trade_signal.get('type', 'stock'),
            'trend_strength': trade_signal['trend_strength'],
            'volume_ratio': trade_signal['volume_ratio'],
            'reason': trade_signal['reason']
        }
        
        self.trades.append(trade)
        
        # Update strategy portfolio for delta calculation
        position = {
            'type': trade_signal.get('type', 'stock'),
            'quantity': trade_signal.get('quantity', 100),
            'symbol': 'SPY',
            'entry_price': trade_signal['price'],
            'entry_time': timestamp
        }
        
        # Add delta for options (simplified)
        if trade_signal.get('type') == 'call':
            position['delta'] = 0.6
        elif trade_signal.get('type') == 'put':
            position['delta'] = -0.6
        
        self.strategy.update_portfolio_greeks(position)
        
        print(f"   💰 EXECUTED: {trade_signal['signal']} {trade_signal.get('quantity', 100)} shares")
        
        # Update capital (simplified - in reality you'd track cash separately)
        if trade_signal['signal'] == 'BUY':
            self.capital -= trade_signal['price'] * trade_signal.get('quantity', 100)
        elif trade_signal['signal'] == 'SELL':
            self.capital += trade_signal['price'] * trade_signal.get('quantity', 100)
    
    def generate_report(self, symbol: str, data: pd.DataFrame, trade_count: int, hedge_count: int) -> Dict:
        """Generate comprehensive performance report"""
        if len(self.portfolio_values) == 0:
            total_return_pct = 0
        else:
            total_return_pct = ((self.portfolio_values[-1] - self.initial_capital) / self.initial_capital) * 100
        
        # Calculate additional metrics
        if len(self.portfolio_values) > 1 and len(self.timestamps) == len(self.portfolio_values):
            portfolio_series = pd.Series(self.portfolio_values, index=self.timestamps)
            returns = portfolio_series.pct_change().dropna()
            
            if len(returns) > 1:
                sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
                max_drawdown = (portfolio_series / portfolio_series.cummax() - 1).min() * 100
            else:
                sharpe_ratio = 0
                max_drawdown = 0
        else:
            sharpe_ratio = 0
            max_drawdown = 0
        
        # Calculate trade statistics
        if self.trades:
            winning_trades = [t for t in self.trades if self.calculate_trade_pnl(t, data['close'].iloc[-1]) > 0]
            win_rate = (len(winning_trades) / len(self.trades)) * 100
        else:
            win_rate = 0
        
        report = {
            'symbol': symbol,
            'initial_capital': self.initial_capital,
            'final_portfolio_value': self.portfolio_values[-1] if self.portfolio_values else self.initial_capital,
            'total_return_pct': total_return_pct,
            'total_trades': trade_count,
            'hedge_operations': hedge_count,
            'win_rate': win_rate,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_pct': max_drawdown,
            'portfolio_delta': self.strategy.portfolio_delta,
            'portfolio_vega': self.strategy.portfolio_vega,
            'portfolio_theta': self.strategy.portfolio_theta,
            'total_positions': len(self.strategy.portfolio_positions),
            'trades': self.trades[:10],  # First 10 trades for display
            'hedge_trades': self.hedge_trades[:5]  # First 5 hedge trades
        }
        
        return report
    
    def calculate_trade_pnl(self, trade: Dict, current_price: float) -> float:
        """Calculate P&L for a trade (simplified)"""
        if trade['signal'] == 'BUY':
            return (current_price - trade['price']) * trade.get('quantity', 100)
        elif trade['signal'] == 'SELL':
            return (trade['price'] - current_price) * trade.get('quantity', 100)
        return 0

def main():
    """Test the advanced backtester"""
    print("🚀 TESTING ADVANCED BACKTESTER WITH REAL DATA")
    print("=" * 60)
    
    # Create advanced strategy
    strategy = AdvancedScalpingStrategy()
    backtester = AdvancedBacktester(strategy, initial_capital=50000)
    
    # Test with your data
    try:
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
        
        print(f"\n📈 ADVANCED STRATEGY PERFORMANCE:")
        print(f"   Total Return: {report['total_return_pct']:.2f}%")
        print(f"   Sharpe Ratio: {report['sharpe_ratio']:.2f}")
        print(f"   Max Drawdown: {report['max_drawdown_pct']:.2f}%")
        print(f"   Win Rate: {report['win_rate']:.1f}%")
        print(f"   Total Trades: {report['total_trades']}")
        print(f"   Hedge Operations: {report['hedge_operations']}")
        print(f"   Portfolio Delta: {report['portfolio_delta']:.0f}")
        print(f"   Total Positions: {report['total_positions']}")
        
        # Show some trade examples
        if report['trades']:
            print(f"\n💰 SAMPLE TRADES:")
            for i, trade in enumerate(report['trades'][:3]):
                print(f"   {i+1}. {trade['signal']} at ${trade['price']:.2f} - {trade['reason']}")
        
        # Show hedge examples
        if report['hedge_trades']:
            print(f"\n🛡️  SAMPLE HEDGES:")
            for i, hedge in enumerate(report['hedge_trades'][:3]):
                print(f"   {i+1}. {hedge['action']} {hedge['quantity']} shares - {hedge['reason']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()