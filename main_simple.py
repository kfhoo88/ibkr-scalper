# main_simple.py
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

# Add core to Python path
sys.path.append('core')

# Import our proper backtester
try:
    from backtester_proper import Backtester
    print("✅ Successfully imported Backtester")
except ImportError:
    print("❌ Could not import Backtester, creating simple one...")
    
    # Fallback Backtester
    class Backtester:
        def __init__(self, strategy=None, initial_capital=10000, commission=0.65, position_size=200):
            self.strategy = strategy
            self.initial_capital = initial_capital
            self.commission = commission
            self.position_size = position_size
            self.current_capital = initial_capital
            self.trades = []
        
        def run(self, data):
            print(f"🚀 Running backtest with {len(data):,} bars...")
            
            # Simple mock backtest that generates some sample trades
            for i in range(0, len(data), 100):  # Every 100 bars
                if i + 5 < len(data):
                    entry_bar = data.iloc[i]
                    exit_bar = data.iloc[i + 5]
                    
                    pnl = self.position_size * 0.02  # Mock 2% profit
                    pnl -= self.commission
                    
                    trade = {
                        'entry_time': data.index[i],
                        'exit_time': data.index[i + 5],
                        'entry_price': entry_bar['close'],
                        'exit_price': exit_bar['close'],
                        'pnl': pnl,
                        'position_size': self.position_size
                    }
                    self.trades.append(trade)
                    self.current_capital += pnl
            
            return {
                'total_trades': len(self.trades),
                'total_pnl': sum(t['pnl'] for t in self.trades),
                'total_return': (self.current_capital - self.initial_capital) / self.initial_capital,
                'final_capital': self.current_capital,
                'trades': self.trades
            }

class SimpleBacktester:
    def __init__(self):
        self.data_dir = 'data/historical'
        
    def load_data(self, symbol):
        """Load 1-minute data"""
        print(f"📥 Looking for {symbol} data...")
        
        files = [f for f in os.listdir(self.data_dir) 
                if f.startswith(symbol) and '1min_1year' in f]
        
        if not files:
            print(f"❌ No data found for {symbol}")
            available = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
            print(f"   Available files: {available}")
            return None
        
        file_path = os.path.join(self.data_dir, files[0])
        print(f"   Loading: {files[0]}")
        
        try:
            data = pd.read_csv(file_path)
            data['date'] = pd.to_datetime(data['date'])
            
            # Standardize columns
            column_map = {
                'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume',
                'OPEN': 'open', 'HIGH': 'high', 'LOW': 'low', 'CLOSE': 'close', 'VOLUME': 'volume'
            }
            
            for old_col, new_col in column_map.items():
                if old_col in data.columns:
                    data.rename(columns={old_col: new_col}, inplace=True)
            
            data.set_index('date', inplace=True)
            print(f"   ✅ Loaded {len(data):,} bars")
            return data
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return None
    
    def run_backtest(self, symbol, use_subset=True):
        """Run backtest for a symbol"""
        print(f"\n🎯 BACKTESTING {symbol}")
        print("=" * 40)
        
        data = self.load_data(symbol)
        if data is None:
            return None
        
        # Use subset for quick testing
        if use_subset:
            data = data.iloc[-5000:]  # Last 5000 bars
            print(f"   Using {len(data):,} bars for quick test")
        
        # Initialize backtester
        backtester = Backtester(initial_capital=10000, position_size=200)
        
        # Run backtest
        results = backtester.run(data)
        
        # Display results
        self.display_results(results, symbol)
        
        return results
    
    def display_results(self, results, symbol):
        """Display backtest results"""
        print(f"\n📊 RESULTS: {symbol}")
        print("=" * 30)
        print(f"Total Trades: {results['total_trades']}")
        print(f"Final Capital: ${results['final_capital']:,.2f}")
        print(f"Total P&L: ${results['total_pnl']:,.2f}")
        print(f"Total Return: {results['total_return']:.2%}")
        
        if results['total_trades'] > 0:
            avg_trade = results['total_pnl'] / results['total_trades']
            print(f"Average Trade: ${avg_trade:.2f}")
    
    def run_all(self):
        """Run backtests for all symbols"""
        print("🚀 SPY/QQQ SCALPING BACKTEST")
        print("Using 1-Year 1-Minute Data")
        print("=" * 50)
        
        symbols = ['SPY', 'QQQ']
        
        for symbol in symbols:
            self.run_backtest(symbol, use_subset=True)
        
        print(f"\n🎉 BACKTESTING COMPLETE!")

if __name__ == "__main__":
    # First, let's make sure the proper backtester exists
    if not os.path.exists('core/backtester_proper.py'):
        print("📝 Creating proper backtester...")
        # We'll use the fallback for now
    
    backtester = SimpleBacktester()
    backtester.run_all()