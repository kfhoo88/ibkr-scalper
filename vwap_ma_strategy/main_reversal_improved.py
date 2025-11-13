# vwap_ma_strategy/main_reversal_improved.py
"""
IMPROVED Reversal Strategy - Better Entry Timing
Wait for swing point + momentum confirmation
"""

import os
import sys
import pandas as pd
import numpy as np
import yaml

sys.path.append('..')

class ImprovedReversalStrategy:
    def __init__(self, config):
        self.config = config['reversal_strategy']
        self.ema_length = self.config['ema_length']
        self.ema_backcandles = self.config['ema_backcandles']
        self.hl_backcandles = self.config['hl_backcandles']
        self.atr_multiplier = self.config['atr_multiplier']
        self.atr_period = self.config['atr_period']
        self.tp_multiplier = self.config['tp_multiplier']
        
        print("🔧 USING IMPROVED ENTRY LOGIC")
        print(f"   EMA: {self.ema_length}, HL: {self.hl_backcandles}")
        print(f"   Entry: Swing point + Next candle confirmation")
    
    def calculate_indicators(self, df):
        """Calculate EMA, ATR, and swing points"""
        df['EMA'] = df['Close'].ewm(span=self.ema_length, adjust=False).mean()
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(self.atr_period).mean()
        
        # Swing points
        df['swing_low'] = df['Low'].rolling(window=self.hl_backcandles, center=False).min()
        df['swing_high'] = df['High'].rolling(window=self.hl_backcandles, center=False).max()
        
        return df
    
    def generate_signals(self, df):
        """Generate signals with improved entry timing"""
        df = self.calculate_indicators(df)
        
        # Initialize columns
        df['EMASignal'] = 0
        df['SwingPoint'] = 0  # 2=swing low, 1=swing high
        df['FinalSignal'] = 0  # 2=long, 1=short
        df['Entry_Price'] = 0.0
        df['SL'] = 0.0
        df['TP'] = 0.0
        
        # Step 1: Identify trend and swing points
        print("Step 1: Identifying trends and swing points...")
        for i in range(self.ema_backcandles, len(df)-2):  # Leave room for confirmation candles
            # EMA trend signal
            window = df.iloc[i-self.ema_backcandles:i+1]
            above_ema = all(window['Low'] > window['EMA'])
            below_ema = all(window['High'] < window['EMA'])
            
            if above_ema:
                df.loc[df.index[i], 'EMASignal'] = 2
            elif below_ema:
                df.loc[df.index[i], 'EMASignal'] = 1
            
            # Swing points
            if df['Low'].iloc[i] <= df['swing_low'].iloc[i]:
                df.loc[df.index[i], 'SwingPoint'] = 2  # Swing low
            elif df['High'].iloc[i] >= df['swing_high'].iloc[i]:
                df.loc[df.index[i], 'SwingPoint'] = 1  # Swing high
        
        # Step 2: Look for confirmation on next candle
        print("Step 2: Looking for confirmation signals...")
        for i in range(self.ema_backcandles + 1, len(df)-1):
            current_ema = df['EMASignal'].iloc[i]
            prev_swing = df['SwingPoint'].iloc[i-1]
            current_atr = df['ATR'].iloc[i]
            
            # LONG ENTRY: Previous candle was swing low + current candle confirms
            if (current_ema == 2 and  # Bullish trend
                prev_swing == 2 and   # Previous candle was swing low
                df['Close'].iloc[i] > df['Open'].iloc[i] and  # Green candle
                df['Close'].iloc[i] > df['High'].iloc[i-1]):  # Close above previous high
                
                # Entry on next candle open
                entry_price = df['Open'].iloc[i+1] if i+1 < len(df) else df['Close'].iloc[i]
                swing_low_price = df['Low'].iloc[i-1]  # The actual swing low
                
                df.loc[df.index[i+1], 'FinalSignal'] = 2
                df.loc[df.index[i+1], 'Entry_Price'] = entry_price
                df.loc[df.index[i+1], 'SL'] = swing_low_price - (current_atr * 0.5)  # Tighter SL
                df.loc[df.index[i+1], 'TP'] = entry_price + ((entry_price - df['SL'].iloc[i+1]) * self.tp_multiplier)
            
            # SHORT ENTRY: Previous candle was swing high + current candle confirms
            elif (current_ema == 1 and  # Bearish trend
                  prev_swing == 1 and   # Previous candle was swing high
                  df['Close'].iloc[i] < df['Open'].iloc[i] and  # Red candle
                  df['Close'].iloc[i] < df['Low'].iloc[i-1]):   # Close below previous low
                
                # Entry on next candle open
                entry_price = df['Open'].iloc[i+1] if i+1 < len(df) else df['Close'].iloc[i]
                swing_high_price = df['High'].iloc[i-1]  # The actual swing high
                
                df.loc[df.index[i+1], 'FinalSignal'] = 1
                df.loc[df.index[i+1], 'Entry_Price'] = entry_price
                df.loc[df.index[i+1], 'SL'] = swing_high_price + (current_atr * 0.5)  # Tighter SL
                df.loc[df.index[i+1], 'TP'] = entry_price - ((df['SL'].iloc[i+1] - entry_price) * self.tp_multiplier)
        
        return df

def run_improved_backtest():
    """Run backtest with improved entry logic"""
    print("🎯 IMPROVED REVERSAL STRATEGY")
    print("Entry: Swing point + Momentum confirmation")
    print("=" * 60)
    
    # Load config
    config_path = "config/vwap_ma_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    strategy = ImprovedReversalStrategy(config)
    
    # Load data
    def load_data(symbol):
        filename = f"../data/historical/{symbol}_IBKR_1min_1year_20251110.csv"
        df = pd.read_csv(filename)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        column_map = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}
        return df.rename(columns=column_map)[['Open', 'High', 'Low', 'Close', 'Volume']]
    
    # Backtest function
    def backtest(df, symbol):
        print(f"\n📊 BACKTESTING {symbol}...")
        df = strategy.generate_signals(df)
        
        # Count signals
        buy_signals = (df['FinalSignal'] == 2).sum()
        sell_signals = (df['FinalSignal'] == 1).sum()
        print(f"   Buy signals: {buy_signals}, Sell signals: {sell_signals}")
        
        if buy_signals == 0 and sell_signals == 0:
            print("   ⚠️ No signals generated")
            return 0, 0, 0
        
        capital = 10000
        position = 0
        entry_price = 0
        trades = []
        
        print("   Running backtest...")
        for i, (idx, row) in enumerate(df.iterrows()):
            if row['FinalSignal'] != 0 and position == 0:
                # Enter position
                position = 100 if row['FinalSignal'] == 2 else -100
                entry_price = row['Entry_Price']
                sl_price = row['SL']
                tp_price = row['TP']
                entry_time = idx
                
            elif position != 0:
                current_price = row['Close']
                
                # Check exit conditions
                exit_trade = False
                if position > 0:  # Long
                    if current_price <= sl_price or current_price >= tp_price:
                        exit_trade = True
                else:  # Short
                    if current_price >= sl_price or current_price <= tp_price:
                        exit_trade = True
                
                if exit_trade:
                    if position > 0:
                        pnl = (current_price - entry_price) * position
                    else:
                        pnl = (entry_price - current_price) * abs(position)
                    
                    capital += pnl
                    trades.append({
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'pnl': pnl,
                        'type': 'LONG' if position > 0 else 'SHORT'
                    })
                    position = 0
        
        if trades:
            trades_df = pd.DataFrame(trades)
            total_pnl = trades_df['pnl'].sum()
            win_rate = (trades_df['pnl'] > 0).mean() * 100
            avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean()
            avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean()
            rr_ratio = abs(avg_win/avg_loss) if avg_loss != 0 else 0
            
            print(f"📈 {symbol} RESULTS:")
            print(f"   Trades: {len(trades_df)}, Win Rate: {win_rate:.1f}%")
            print(f"   Total P&L: ${total_pnl:+.2f}")
            print(f"   Avg Win: ${avg_win:.2f}, Avg Loss: ${avg_loss:.2f}")
            print(f"   R:R Ratio: {rr_ratio:.2f}")
            
            return total_pnl, win_rate, len(trades_df)
        return 0, 0, 0
    
    # Run backtests
    spy_data = load_data('SPY')
    qqq_data = load_data('QQQ')
    
    spy_pnl, spy_win_rate, spy_trades = backtest(spy_data, 'SPY')
    qqq_pnl, qqq_win_rate, qqq_trades = backtest(qqq_data, 'QQQ')
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 IMPROVED STRATEGY SUMMARY")
    print(f"{'='*60}")
    print(f"SPY: {spy_trades} trades, {spy_win_rate:.1f}% win rate, ${spy_pnl:+.2f}")
    print(f"QQQ: {qqq_trades} trades, {qqq_win_rate:.1f}% win rate, ${qqq_pnl:+.2f}")
    print(f"TOTAL: ${spy_pnl + qqq_pnl:+.2f}")
    
    print(f"\n💡 COMPARISON WITH PREVIOUS:")
    print(f"Previous Reversal: -$2281.00 (44.7% win rate)")
    print(f"Improved Logic: ${spy_pnl + qqq_pnl:+.2f} ({((spy_win_rate + qqq_win_rate)/2):.1f}% win rate)")

if __name__ == "__main__":
    run_improved_backtest()