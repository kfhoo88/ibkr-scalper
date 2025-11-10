# backtester_fixed.py

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class FixedBacktester:
    def __init__(self, strategy, initial_capital: float = 10000):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.reset()
    
    def reset(self):
        """Reset backtester state"""
        self.capital = self.initial_capital
        self.position = 0
        self.entry_price = 0
        self.entry_time = None
        self.trades = []
        self.equity_curve = []
        self.signals = []
    
    def calculate_position_size(self, price: float) -> int:
        """Calculate position size based on risk management"""
        # Fixed position size for scalping - adjust based on capital
        if self.capital >= 50000:
            shares = 100
        elif self.capital >= 25000:
            shares = 50
        elif self.capital >= 10000:
            shares = 25
        else:
            shares = 10
            
        # Make sure we can afford it
        max_affordable = int(self.capital * 0.1 / price)  # Use max 10% of capital per trade
        return min(shares, max_affordable)
    
    def close_position(self, price: float, timestamp: datetime, reason: str = "Signal"):
        """Close current position with proper P&L calculation"""
        if self.position > 0:  # Long position
            pnl = (price - self.entry_price) * self.position
            proceeds = self.position * price
            self.capital += proceeds
            
            print(f"   📈 CLOSED LONG: {self.position} shares at ${price:.2f}, P&L: ${pnl:.2f}")
            
            # Update the trade record
            if self.trades:
                self.trades[-1]['exit_time'] = timestamp
                self.trades[-1]['exit_price'] = price
                self.trades[-1]['pnl'] = pnl
                self.trades[-1]['status'] = 'CLOSED'
                self.trades[-1]['exit_reason'] = reason
                self.trades[-1]['holding_time'] = (timestamp - self.entry_time).total_seconds() / 60
            
        elif self.position < 0:  # Short position  
            pnl = (self.entry_price - price) * abs(self.position)
            # For short: we get back collateral + profit
            collateral_return = abs(self.position) * self.entry_price
            profit_loss = pnl
            self.capital += collateral_return + profit_loss
            
            print(f"   📉 CLOSED SHORT: {abs(self.position)} shares at ${price:.2f}, P&L: ${pnl:.2f}")
            
            # Update the trade record
            if self.trades:
                self.trades[-1]['exit_time'] = timestamp
                self.trades[-1]['exit_price'] = price
                self.trades[-1]['pnl'] = pnl
                self.trades[-1]['status'] = 'CLOSED'
                self.trades[-1]['exit_reason'] = reason
                self.trades[-1]['holding_time'] = (timestamp - self.entry_time).total_seconds() / 60
        
        self.position = 0
        self.entry_price = 0
        self.entry_time = None
    
    def should_exit_position(self, analysis: Dict, current_price: float, current_time: datetime) -> bool:
        """Enhanced exit logic with stop loss and time-based exits"""
        if self.position == 0:
            return False
            
        # Calculate current P&L
        if self.position > 0:  # Long
            current_pnl = (current_price - self.entry_price) * self.position
            stop_loss_price = self.entry_price * 0.995  # 0.5% stop loss
            take_profit_price = self.entry_price * 1.01  # 1% take profit
        else:  # Short
            current_pnl = (self.entry_price - current_price) * abs(self.position)
            stop_loss_price = self.entry_price * 1.005  # 0.5% stop loss
            take_profit_price = self.entry_price * 0.99  # 1% take profit
        
        # Exit conditions
        exit_conditions = [
            # Stop loss
            (self.position > 0 and current_price <= stop_loss_price),
            (self.position < 0 and current_price >= stop_loss_price),
            # Take profit
            (self.position > 0 and current_price >= take_profit_price),
            (self.position < 0 and current_price <= take_profit_price),
            # Time-based exit (15 minutes max for scalping)
            (current_time - self.entry_time).total_seconds() / 60 > 15,
            # Opposite strong signal with high confidence
            (self.position > 0 and analysis['signal'] == 'SELL' and analysis['trend_strength'] > 0.7),
            (self.position < 0 and analysis['signal'] == 'BUY' and analysis['trend_strength'] > 0.7)
        ]
        
        return any(exit_conditions)
    
    def backtest(self, data: pd.DataFrame, symbol: str = "SPY") -> Dict:
        """Run backtest on historical data with proper risk management"""
        self.reset()
        
        print(f"🔧 Backtesting {symbol} with {len(data)} bars...")
        print(f"📊 Data range: {data.index[0]} to {data.index[-1]}")
        print(f"💰 Initial Capital: ${self.initial_capital:,.2f}")
        
        signal_count = 0
        trade_count = 0
        
        for i in range(100, len(data)):  # Start from bar 100 to have enough history
            current_data = data.iloc[:i+1].copy()
            current_price = current_data['close'].iloc[-1]
            current_time = current_data.index[-1]
            
            # Generate signal
            analysis = self.strategy.analyze_market(current_data)
            
            if analysis:
                self.signals.append({
                    'timestamp': analysis['timestamp'],
                    'signal': analysis['signal'],
                    'price': analysis['current_price'],
                    'trend_strength': analysis['trend_strength'],
                    'volume_ratio': analysis['volume_ratio'],
                    'dynamic_threshold': analysis['dynamic_volume_threshold'],
                    'reason': analysis['reason']
                })
                
                # Check if we should exit current position
                if self.position != 0 and self.should_exit_position(analysis, current_price, current_time):
                    exit_reason = "Stop loss/Time exit" if self.position != 0 else "Signal"
                    self.close_position(current_price, current_time, exit_reason)
                
                # Open new position if no current position and good signal
                if (analysis['signal'] != 'HOLD' and 
                    self.position == 0 and 
                    analysis['trend_strength'] > 0.5):  # Reduced threshold to capture more trades
                    
                    signal_count += 1
                    shares = self.calculate_position_size(analysis['current_price'])
                    
                    if shares > 0:  # Only trade if we can afford shares
                        print(f"\n🎯 Signal #{signal_count} at {analysis['timestamp']}:")
                        print(f"   Signal: {analysis['signal']}")
                        print(f"   Price: ${analysis['current_price']:.2f}")
                        print(f"   Trend Strength: {analysis['trend_strength']:.2f}")
                        print(f"   Volume Ratio: {analysis['volume_ratio']:.2f} (Threshold: {analysis['dynamic_volume_threshold']:.1f})")
                        print(f"   Shares: {shares}")
                        print(f"   Reason: {analysis['reason']}")
                        
                        trade_count += 1
                        self.execute_trade(analysis['signal'], analysis['current_price'], analysis['timestamp'], shares)
                    else:
                        print(f"   ⚠️  Signal skipped - cannot afford position at ${analysis['current_price']:.2f}")
        
        # Close any open positions at the end
        if self.position != 0:
            self.close_position(data['close'].iloc[-1], data.index[-1], "End of backtest")
        
        # Generate performance report
        report = self.generate_report(symbol, data)
        
        print(f"\n📈 BACKTEST COMPLETE:")
        print(f"   Total Signals: {len([s for s in self.signals if s['signal'] != 'HOLD'])}")
        print(f"   Trades Taken: {trade_count}")
        print(f"   Final Capital: ${self.capital:,.2f}")
        print(f"   Total Return: {report['total_return_pct']:.2f}%")
        print(f"   Total P&L: ${report['total_pnl']:,.2f}")
        
        return report
    
    def execute_trade(self, signal: str, price: float, timestamp: datetime, shares: int):
        """Execute a trade with specified share count"""
        if signal == "BUY" and self.position == 0:
            cost = shares * price
            if cost <= self.capital:
                self.position = shares
                self.entry_price = price
                self.entry_time = timestamp
                self.capital -= cost
                
                trade = {
                    'entry_time': timestamp,
                    'exit_time': None,
                    'side': 'LONG',
                    'entry_price': price,
                    'exit_price': None,
                    'shares': shares,
                    'pnl': 0,
                    'status': 'OPEN',
                    'investment': cost
                }
                self.trades.append(trade)
                print(f"   📈 OPENED LONG: {shares} shares at ${price:.2f} (Cost: ${cost:.2f})")
        
        elif signal == "SELL" and self.position == 0:
            # For short selling, we need collateral
            collateral_required = shares * price
            if collateral_required <= self.capital:
                self.position = -shares
                self.entry_price = price
                self.entry_time = timestamp
                # Reserve collateral (not actually deducting since it's returned on close)
                
                trade = {
                    'entry_time': timestamp,
                    'exit_time': None,
                    'side': 'SHORT',
                    'entry_price': price,
                    'exit_price': None,
                    'shares': shares,
                    'pnl': 0,
                    'status': 'OPEN',
                    'investment': collateral_required
                }
                self.trades.append(trade)
                print(f"   📉 OPENED SHORT: {shares} shares at ${price:.2f} (Collateral: ${collateral_required:.2f})")
    
    def generate_report(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Generate comprehensive performance report"""
        closed_trades = [t for t in self.trades if t['status'] == 'CLOSED']
        total_return_pct = ((self.capital - self.initial_capital) / self.initial_capital) * 100
        
        if closed_trades:
            winning_trades = [t for t in closed_trades if t['pnl'] > 0]
            losing_trades = [t for t in closed_trades if t['pnl'] < 0]
            win_rate = (len(winning_trades) / len(closed_trades)) * 100
            total_pnl = sum(t['pnl'] for t in closed_trades)
            avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
            profit_factor = abs(sum(t['pnl'] for t in winning_trades) / sum(t['pnl'] for t in losing_trades)) if losing_trades else float('inf')
            
            # Calculate additional metrics
            total_invested = sum(t['investment'] for t in closed_trades)
            roi = (total_pnl / total_invested * 100) if total_invested > 0 else 0
        else:
            win_rate = 0
            total_pnl = 0
            avg_win = 0
            avg_loss = 0
            profit_factor = 0
            roi = 0
        
        report = {
            'symbol': symbol,
            'period': f"{data.index[0].date()} to {data.index[-1].date()}",
            'initial_capital': self.initial_capital,
            'final_capital': self.capital,
            'total_return_pct': total_return_pct,
            'total_signals': len([s for s in self.signals if s['signal'] != 'HOLD']),
            'total_trades': len(self.trades),
            'closed_trades': len(closed_trades),
            'winning_trades': len(winning_trades) if closed_trades else 0,
            'losing_trades': len(losing_trades) if closed_trades else 0,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'roi': roi,
            'signals': self.signals,
            'trades': self.trades
        }
        
        return report

def run_fixed_backtest():
    """Test the fixed backtester with proper risk management"""
    print("🚀 FIXED BACKTESTER WITH PROPER POSITION SIZING")
    print("=" * 60)
    
    # Import strategy
    from strategies.scalping_strategy import ScalpingStrategy
    
    # Create strategy with dynamic volume
    strategy = ScalpingStrategy()
    
    # Create backtester with proper risk management
    backtester = FixedBacktester(strategy, initial_capital=10000)
    
    # Test files
    test_files = [
        ('SPY', 'data/historical/SPY_1min_data.csv'),
        ('QQQ', 'data/historical/QQQ_1min_data.csv'),
    ]
    
    all_reports = []
    
    for symbol, filepath in test_files:
        if os.path.exists(filepath):
            print(f"\n" + "="*60)
            print(f"📊 BACKTESTING: {symbol}")
            print(f"📁 File: {filepath}")
            print("="*60)
            
            try:
                # Load data
                data = pd.read_csv(filepath)
                
                # Handle datetime column
                datetime_col = None
                for col in data.columns:
                    if 'time' in col.lower() or 'date' in col.lower():
                        datetime_col = col
                        break
                
                if datetime_col:
                    data[datetime_col] = pd.to_datetime(data[datetime_col])
                    data = data.set_index(datetime_col)
                else:
                    data.index = pd.date_range(start='2024-01-01 09:30:00', periods=len(data), freq='1min')
                
                # Convert column names to lowercase
                data = data.rename(columns=str.lower)
                
                # Run backtest
                report = backtester.backtest(data, symbol)
                all_reports.append(report)
                
                print(f"\n📈 {symbol} RESULTS:")
                print(f"   Return: {report['total_return_pct']:.2f}%")
                print(f"   Total P&L: ${report['total_pnl']:,.2f}")
                print(f"   Trades: {report['closed_trades']} (Win Rate: {report['win_rate']:.1f}%)")
                print(f"   Profit Factor: {report['profit_factor']:.2f}")
                print(f"   ROI: {report['roi']:.1f}%")
                print(f"   Avg Win: ${report['avg_win']:.2f} | Avg Loss: ${report['avg_loss']:.2f}")
                
                # Show trade details
                if report['closed_trades'] > 0:
                    print(f"\n💰 TRADE DETAILS:")
                    for i, trade in enumerate(report['trades']):
                        if trade['status'] == 'CLOSED':
                            pnl_percent = (trade['pnl'] / trade['investment']) * 100
                            print(f"   {i+1:2d}. {trade['side']:5s} | "
                                  f"Entry: ${trade['entry_price']:7.2f} | "
                                  f"Exit: ${trade['exit_price']:7.2f} | "
                                  f"P&L: ${trade['pnl']:7.2f} ({pnl_percent:5.1f}%) | "
                                  f"Time: {trade.get('holding_time', 0):.0f}min")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"❌ File not found: {filepath}")
    
    # Summary
    if all_reports:
        print(f"\n" + "="*70)
        print("🎯 OVERALL SUMMARY")
        print("="*70)
        for report in all_reports:
            print(f"   {report['symbol']}: {report['total_return_pct']:6.1f}% | "
                  f"Trades: {report['closed_trades']:2d} | "
                  f"Win Rate: {report['win_rate']:5.1f}% | "
                  f"P&L: ${report['total_pnl']:8.2f}")
    
    return all_reports

if __name__ == "__main__":
    run_fixed_backtest()