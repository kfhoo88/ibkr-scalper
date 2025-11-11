# First, let's check the current project structure and config
import os
import yaml
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

# Check project structure
print("Project structure:")
for root, dirs, files in os.walk('.'):
    for file in files:
        if any(x in file for x in ['.py', '.yaml', '.csv', '.md']):
            print(f"  {os.path.join(root, file)}")

# Load current config
try:
    with open('vwap_ma_strategy/config/vwap_ma_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    print("\nCurrent config structure:")
    print(yaml.dump(config, default_flow_style=False))
except FileNotFoundError:
    print("Config file not found - creating new structure")
    config = {}

# Add reversal strategy parameters to config
reversal_config = {
    'ema_length': 21,
    'ema_backcandles': 14,
    'hl_backcandles': 8,
    'atr_multiplier': 1.0,
    'atr_period': 14,
    'tp_multiplier': 1.5,
    'require_reversal_candle': True
}

# Update config
if 'reversal_strategy' not in config:
    config['reversal_strategy'] = reversal_config
else:
    config['reversal_strategy'].update(reversal_config)

print("\nUpdated config structure:")
print(yaml.dump(config, default_flow_style=False))

# Save updated config
try:
    with open('vwap_ma_strategy/config/vwap_ma_config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    print("✅ Config file updated successfully!")
except Exception as e:
    print(f"⚠️ Could not save config: {e}")

# Now implement the reversal strategy
class ReversalStrategy:
    def __init__(self, config):
        self.config = config['reversal_strategy']
        self.ema_length = self.config['ema_length']
        self.ema_backcandles = self.config['ema_backcandles']
        self.hl_backcandles = self.config['hl_backcandles']
        self.atr_multiplier = self.config['atr_multiplier']
        self.atr_period = self.config['atr_period']
        self.tp_multiplier = self.config['tp_multiplier']
        self.require_reversal_candle = self.config['require_reversal_candle']
    
    def calculate_ema(self, prices):
        return prices.ewm(span=self.ema_length, adjust=False).mean()
    
    def calculate_atr(self, high, low, close):
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(self.atr_period).mean()
    
    def ema_signal(self, df, current_index):
        """Determine if price is consistently above/below EMA"""
        sigup = 2  # Bullish - price above EMA
        sigdn = 1  # Bearish - price below EMA
        
        start_idx = current_index - self.ema_backcandles
        if start_idx < 0:
            return 0
            
        # Check last N candles for consistency
        for i in range(start_idx, current_index + 1):
            if df['Low'].iloc[i] <= df['EMA'].iloc[i]:
                sigup = 0  # Not consistently above EMA
            if df['High'].iloc[i] >= df['EMA'].iloc[i]:
                sigdn = 0  # Not consistently below EMA
                
        if sigup:
            return sigup
        elif sigdn:
            return sigdn
        else:
            return 0
    
    def calculate_swing_points(self, df):
        """Calculate rolling highs and lows"""
        df = df.copy()
        df['swing_low'] = df['Low'].rolling(window=self.hl_backcandles).min()
        df['swing_high'] = df['High'].rolling(window=self.hl_backcandles).max()
        return df
    
    def is_reversal_candle(self, df, current_index, direction):
        """Check for reversal candle confirmation"""
        if current_index < 1:
            return False
            
        current_candle = df.iloc[current_index]
        prev_candle = df.iloc[current_index - 1]
        
        if direction == 'long':
            # Green candle that closes higher than previous close
            return (current_candle['Close'] > current_candle['Open'] and
                    current_candle['Close'] > prev_candle['Close'])
        elif direction == 'short':
            # Red candle that closes lower than previous close
            return (current_candle['Close'] < current_candle['Open'] and
                    current_candle['Close'] < prev_candle['Close'])
        return False
    
    def generate_signals(self, df):
        """Generate complete trading signals"""
        df = df.copy()
        
        # Calculate indicators
        df['EMA'] = self.calculate_ema(df['Close'])
        df['ATR'] = self.calculate_atr(df['High'], df['Low'], df['Close'])
        df = self.calculate_swing_points(df)
        
        # Initialize signals
        df['EMASignal'] = 0
        df['HLSignal'] = 0
        df['FinalSignal'] = 0
        df['SL'] = 0.0
        df['TP'] = 0.0
        
        # Generate signals
        for i in range(self.ema_backcandles, len(df)):
            # EMA trend signal
            ema_sig = self.ema_signal(df, i)
            df.loc[df.index[i], 'EMASignal'] = ema_sig
            
            # Entry signal based on swing points
            if ema_sig == 2 and df['Low'].iloc[i] <= df['swing_low'].iloc[i]:
                # Long setup: in uptrend, price at swing low
                if not self.require_reversal_candle or self.is_reversal_candle(df, i, 'long'):
                    df.loc[df.index[i], 'HLSignal'] = 2
                    df.loc[df.index[i], 'FinalSignal'] = 2  # Buy signal
                    # Calculate SL and TP
                    atr_val = df['ATR'].iloc[i]
                    entry_price = df['Close'].iloc[i]
                    df.loc[df.index[i], 'SL'] = entry_price - (atr_val * self.atr_multiplier)
                    df.loc[df.index[i], 'TP'] = entry_price + (atr_val * self.atr_multiplier * self.tp_multiplier)
                    
            elif ema_sig == 1 and df['High'].iloc[i] >= df['swing_high'].iloc[i]:
                # Short setup: in downtrend, price at swing high
                if not self.require_reversal_candle or self.is_reversal_candle(df, i, 'short'):
                    df.loc[df.index[i], 'HLSignal'] = 1
                    df.loc[df.index[i], 'FinalSignal'] = 1  # Sell signal
                    # Calculate SL and TP
                    atr_val = df['ATR'].iloc[i]
                    entry_price = df['Close'].iloc[i]
                    df.loc[df.index[i], 'SL'] = entry_price + (atr_val * self.atr_multiplier)
                    df.loc[df.index[i], 'TP'] = entry_price - (atr_val * self.atr_multiplier * self.tp_multiplier)
        
        return df

# Load historical data for testing
def load_historical_data(symbol):
    filename = f"data/historical/{symbol}_IBKR_1min_1year_20251110.csv"
    try:
        df = pd.read_csv(filename)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime')
        print(f"✅ Loaded {symbol}: {len(df)} rows, {df.index.min()} to {df.index.max()}")
        return df
    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
        return None

# Test with sample data first
print("\n🔧 Testing strategy implementation...")

# Create sample data for quick test
def create_test_data():
    dates = pd.date_range('2024-01-01', periods=100, freq='1min')
    np.random.seed(42)
    price = 450 + np.cumsum(np.random.normal(0, 0.1, 100))
    
    test_df = pd.DataFrame({
        'Open': price + np.random.normal(0, 0.05, 100),
        'High': price + np.random.normal(0.1, 0.05, 100),
        'Low': price + np.random.normal(-0.1, 0.05, 100),
        'Close': price,
        'Volume': np.random.randint(1000000, 5000000, 100)
    }, index=dates)
    
    return test_df

# Quick test
test_data = create_test_data()
strategy = ReversalStrategy(config)
test_results = strategy.generate_signals(test_data)

print(f"✅ Strategy test completed:")
print(f"   Signals generated: {len(test_results[test_results['FinalSignal'] != 0])}")
print(f"   Buy signals: {len(test_results[test_results['FinalSignal'] == 2])}")
print(f"   Sell signals: {len(test_results[test_results['FinalSignal'] == 1])}")

# Now let's create the backtesting engine
class ReversalBacktester:
    def __init__(self, config, initial_capital=10000):
        self.config = config
        self.strategy = ReversalStrategy(config)
        self.initial_capital = initial_capital
        
    def backtest(self, df, symbol='SPY'):
        print(f"\n📊 BACKTESTING {symbol} WITH REVERSAL STRATEGY")
        
        # Generate signals
        df = self.strategy.generate_signals(df)
        
        # Trading simulation
        capital = self.initial_capital
        position = 0
        entry_price = 0
        trades = []
        equity_curve = []
        
        for i, (idx, row) in enumerate(df.iterrows()):
            current_price = row['Close']
            
            # Calculate current equity
            if position != 0:
                unrealized_pnl = (current_price - entry_price) * position
                current_equity = capital + unrealized_pnl
            else:
                current_equity = capital
                
            equity_curve.append(current_equity)
            
            # Check exit conditions
            if position > 0:  # Long position
                if current_price <= row['SL'] or current_price >= row['TP']:
                    pnl = (current_price - entry_price) * position
                    capital += pnl
                    trades.append({
                        'symbol': symbol,
                        'entry_time': entry_time,
                        'exit_time': idx,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'position': position,
                        'pnl': pnl,
                        'type': 'LONG',
                        'duration': (idx - entry_time).total_seconds() / 60
                    })
                    position = 0
                    
            elif position < 0:  # Short position
                if current_price >= row['SL'] or current_price <= row['TP']:
                    pnl = (entry_price - current_price) * abs(position)
                    capital += pnl
                    trades.append({
                        'symbol': symbol,
                        'entry_time': entry_time,
                        'exit_time': idx,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'position': position,
                        'pnl': pnl,
                        'type': 'SHORT', 
                        'duration': (idx - entry_time).total_seconds() / 60
                    })
                    position = 0
            
            # Enter new positions
            if position == 0 and row['FinalSignal'] != 0:
                # Simple position sizing - 100 shares per trade
                position_size = 100
                entry_price = current_price
                entry_time = idx
                
                if row['FinalSignal'] == 2:  # Buy
                    position = position_size
                elif row['FinalSignal'] == 1:  # Sell
                    position = -position_size
        
        # Analyze results
        if trades:
            trades_df = pd.DataFrame(trades)
            total_pnl = trades_df['pnl'].sum()
            win_rate = (trades_df['pnl'] > 0).mean() * 100
            avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean()
            avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean()
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
            
            print(f"📈 {symbol} RESULTS:")
            print(f"   Total Trades: {len(trades_df)}")
            print(f"   Win Rate: {win_rate:.2f}%")
            print(f"   Total P&L: ${total_pnl:.2f}")
            print(f"   Average Win: ${avg_win:.2f}")
            print(f"   Average Loss: ${avg_loss:.2f}")
            print(f"   Profit Factor: {profit_factor:.2f}")
            print(f"   Final Capital: ${capital:.2f}")
            
            return trades_df, equity_curve, df
        else:
            print(f"   No trades executed for {symbol}")
            return pd.DataFrame(), equity_curve, df

# Ready to run on actual data
print("\n🎯 READY FOR BACKTESTING")
print("Strategy Parameters:")
print(f"  EMA Length: {config['reversal_strategy']['ema_length']}")
print(f"  EMA Backcandles: {config['reversal_strategy']['ema_backcandles']}")
print(f"  HL Backcandles: {config['reversal_strategy']['hl_backcandles']}")
print(f"  ATR Multiplier: {config['reversal_strategy']['atr_multiplier']}")
print(f"  TP Multiplier: {config['reversal_strategy']['tp_multiplier']}")
print(f"  Require Reversal Candle: {config['reversal_strategy']['require_reversal_candle']}")

# Load and test with actual data
print("\n📁 LOADING HISTORICAL DATA...")
spy_data = load_historical_data('SPY')
qqq_data = load_historical_data('QQQ')

backtester = ReversalBacktester(config)

if spy_data is not None:
    spy_trades, spy_equity, spy_signals = backtester.backtest(spy_data, 'SPY')

if qqq_data is not None:
    qqq_trades, qqq_equity, qqq_signals = backtester.backtest(qqq_data, 'QQQ')

# Compare performance
if spy_data is not None and qqq_data is not None:
    if len(spy_trades) > 0 and len(qqq_trades) > 0:
        print(f"\n📊 STRATEGY COMPARISON")
        print(f"SPY Win Rate: {(spy_trades['pnl'] > 0).mean()*100:.2f}%")
        print(f"QQQ Win Rate: {(qqq_trades['pnl'] > 0).mean()*100:.2f}%")
        print(f"SPY Total P&L: ${spy_trades['pnl'].sum():.2f}")
        print(f"QQQ Total P&L: ${qqq_trades['pnl'].sum():.2f}")

print("\n✅ IMPLEMENTATION COMPLETE!")
print("Next: Analyze results and fine-tune parameters in config file")