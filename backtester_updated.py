# backtester_updated.py

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self, strategy, initial_capital: float = 10000):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.reset()
    
    def reset(self):
        """Reset backtester state"""
        self.capital = self.initial_capital
        self.position = 0
        self.entry_price = 0
        self.trades = []
        self.equity_curve = []
        self.signals = []
    
    def close_position(self, price: float, timestamp: datetime, reason: str = "Signal"):
        """Close current position"""
        if self.position > 0:  # Long position
            pnl = (price - self.entry_price) * self.position
            self.capital += self.position * price
            print(f"   📈 CLOSED LONG: {self.position} shares at ${price:.2f}, P&L: ${pnl:.2f}")
            
            # Update the trade record
            if self.trades:
                self.trades[-1]['exit_time'] = timestamp
                self.trades[-1]['exit_price'] = price
                self.trades[-1]['pnl'] = pnl
                self.trades[-1]['status'] = 'CLOSED'
                self.trades[-1]['exit_reason'] = reason
            
        elif self.position < 0:  # Short position  
            pnl = (self.entry_price - price) * abs(self.position)
            self.capital += abs(self.position) * (2 * self.entry_price - price)  # Return collateral + profit
            print(f"   📉 CLOSED SHORT: {abs(self.position)} shares at ${price:.2f}, P&L: ${pnl:.2f}")
            
            # Update the trade record
            if self.trades:
                self.trades[-1]['exit_time'] = timestamp
                self.trades[-1]['exit_price'] = price
                self.trades[-1]['pnl'] = pnl
                self.trades[-1]['status'] = 'CLOSED'
                self.trades[-1]['exit_reason'] = reason
        
        self.position = 0
        self.entry_price = 0
    
    def backtest(self, data: pd.DataFrame, symbol: str = "SPY") -> Dict:
        """Run backtest on historical data"""
        self.reset()
        
        print(f"🔧 Backtesting {symbol} with {len(data)} bars...")
        print(f"📊 Data range: {data.index[0]} to {data.index[-1]}")
        
        signal_count = 0
        trade_count = 0
        
        for i in range(100, len(data)):  # Start from bar 100 to have enough history
            current_data = data.iloc[:i+1].copy()
            current_price = current_data['close'].iloc[-1]  # Get current price
            
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
                
                # Close position logic
                if self.position != 0:
                    # Simple exit strategy: close on opposite signal
                    if (self.position > 0 and analysis['signal'] == 'SELL') or \
                       (self.position < 0 and analysis['signal'] == 'BUY'):
                        self.close_position(current_price, analysis['timestamp'], "Opposite signal")
                
                # Open position logic (only if no position)
                if analysis['signal'] != 'HOLD' and self.position == 0:
                    signal_count += 1
                    print(f"\n🎯 Signal #{signal_count} at {analysis['timestamp']}:")
                    print(f"   Signal: {analysis['signal']}")
                    print(f"   Price: ${analysis['current_price']:.2f}")
                    print(f"   Trend Strength: {analysis['trend_strength']:.2f}")
                    print(f"   Volume Ratio: {analysis['volume_ratio']:.2f} (Threshold: {analysis['dynamic_volume_threshold']:.1f})")
                    print(f"   Reason: {analysis['reason']}")
                    
                    trade_count += 1
                    self.execute_trade(analysis['signal'], analysis['current_price'], analysis['timestamp'])
        
        # Close any open positions at the end
        if self.position != 0:
            self.close_position(data['close'].iloc[-1], data.index[-1], "End of backtest")
        
        # Generate performance report
        report = self.generate_report(symbol, data)
        
        print(f"\n📈 BACKTEST COMPLETE:")
        print(f"   Total Signals: {signal_count}")
        print(f"   Total Trades: {trade_count}")
        print(f"   Final Capital: ${self.capital:.2f}")
        print(f"   Return: {((self.capital - self.initial_capital) / self.initial_capital * 100):.2f}%")
        
        return report
    
    def execute_trade(self, signal: str, price: float, timestamp: datetime):
        """Execute a trade (simplified version)"""
        if signal == "BUY" and self.position == 0:
            # Buy 100 shares
            shares = 100
            cost = shares * price
            if cost <= self.capital:
                self.position = shares
                self.entry_price = price
                self.capital -= cost
                
                trade = {
                    'entry_time': timestamp,
                    'exit_time': None,
                    'side': 'LONG',
                    'entry_price': price,
                    'exit_price': None,
                    'shares': shares,
                    'pnl': 0,
                    'status': 'OPEN'
                }
                self.trades.append(trade)
                print(f"   📈 OPENED LONG: {shares} shares at ${price:.2f}")
        
        elif signal == "SELL" and self.position == 0:
            # Sell 100 shares (short)
            shares = 100
            self.position = -shares
            self.entry_price = price
            self.capital += shares * price  # Credit from short sale
            
            trade = {
                'entry_time': timestamp,
                'exit_time': None,
                'side': 'SHORT',
                'entry_price': price,
                'exit_price': None,
                'shares': shares,
                'pnl': 0,
                'status': 'OPEN'
            }
            self.trades.append(trade)
            print(f"   📉 OPENED SHORT: {shares} shares at ${price:.2f}")
    
    def generate_report(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Generate backtest performance report"""
        # Calculate basic metrics
        total_return = (self.capital - self.initial_capital) / self.initial_capital * 100
        closed_trades = [t for t in self.trades if t['status'] == 'CLOSED']
        
        report = {
            'symbol': symbol,
            'period': f"{data.index[0].date()} to {data.index[-1].date()}",
            'initial_capital': self.initial_capital,
            'final_capital': self.capital,
            'total_return_pct': total_return,
            'total_signals': len([s for s in self.signals if s['signal'] != 'HOLD']),
            'total_trades': len(self.trades),
            'closed_trades': len(closed_trades),
            'winning_trades': len([t for t in closed_trades if t['pnl'] > 0]),
            'losing_trades': len([t for t in closed_trades if t['pnl'] < 0]),
            'signals': self.signals,
            'trades': self.trades
        }
        
        if closed_trades:
            report['win_rate'] = (len([t for t in closed_trades if t['pnl'] > 0]) / len(closed_trades)) * 100
            report['avg_trade_pnl'] = np.mean([t['pnl'] for t in closed_trades])
            report['total_pnl'] = sum([t['pnl'] for t in closed_trades])
            report['best_trade'] = max([t['pnl'] for t in closed_trades]) if closed_trades else 0
            report['worst_trade'] = min([t['pnl'] for t in closed_trades]) if closed_trades else 0
        else:
            report['win_rate'] = 0
            report['avg_trade_pnl'] = 0
            report['total_pnl'] = 0
            report['best_trade'] = 0
            report['worst_trade'] = 0
        
        return report

def run_backtest_test():
    """Test the updated backtester with dynamic volume"""
    print("🚀 TESTING UPDATED STRATEGY WITH DYNAMIC VOLUME")
    print("=" * 50)
    
    # Import strategy
    from strategies.scalping_strategy import ScalpingStrategy
    
    # Create strategy with dynamic volume
    strategy = ScalpingStrategy()
    
    # Create backtester
    backtester = Backtester(strategy)
    
    # Test with your real data files
    test_files = [
        ('SPY', 'data/historical/SPY_1min_data.csv'),  # Your real data
        ('QQQ', 'data/historical/QQQ_1min_data.csv'),  # Your real data
    ]
    
    all_reports = []
    
    for symbol, filepath in test_files:
        if os.path.exists(filepath):
            print(f"\n" + "="*60)
            print(f"📊 BACKTESTING: {symbol}")
            print(f"📁 File: {filepath}")
            print("="*60)
            
            try:
                # Load your real data
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
                
                # Convert column names to lowercase for consistency
                data = data.rename(columns=str.lower)
                
                # Run backtest
                report = backtester.backtest(data, symbol)
                all_reports.append(report)
                
                print(f"\n📈 {symbol} BACKTEST RESULTS:")
                print(f"   Total Return: {report['total_return_pct']:.2f}%")
                print(f"   Signals Generated: {report['total_signals']}")
                print(f"   Trades Executed: {report['total_trades']}")
                print(f"   Closed Trades: {report['closed_trades']}")
                print(f"   Win Rate: {report['win_rate']:.1f}%")
                print(f"   Total P&L: ${report['total_pnl']:.2f}")
                print(f"   Final Capital: ${report['final_capital']:.2f}")
                
                # Show trade details
                if report['closed_trades'] > 0:
                    print(f"\n💰 TRADE DETAILS:")
                    for i, trade in enumerate(report['trades']):
                        if trade['status'] == 'CLOSED':
                            print(f"   Trade {i+1}: {trade['side']} | Entry: ${trade['entry_price']:.2f} | "
                                  f"Exit: ${trade['exit_price']:.2f} | P&L: ${trade['pnl']:.2f}")
                
            except Exception as e:
                print(f"❌ Error backtesting {symbol}: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"❌ File not found: {filepath}")
    
    # Summary report
    if all_reports:
        print(f"\n" + "="*70)
        print("🎯 OVERALL BACKTEST SUMMARY")
        print("="*70)
        
        for report in all_reports:
            print(f"\n📊 {report['symbol']}:")
            print(f"   Return: {report['total_return_pct']:.2f}%")
            print(f"   Trades: {report['closed_trades']} (Win Rate: {report['win_rate']:.1f}%)")
            print(f"   Total P&L: ${report['total_pnl']:.2f}")
            print(f"   Final Capital: ${report['final_capital']:.2f}")

if __name__ == "__main__":
    run_backtest_test()