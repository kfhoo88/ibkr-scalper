# vwap_ma_strategy/main_reversal_detailed.py
"""
Detailed Reversal Strategy - With Trade Analysis
"""

import os
import sys
import pandas as pd
import numpy as np
import yaml
from datetime import datetime

sys.path.append('..')

class DetailedReversalStrategy:
    def __init__(self, config):
        self.config = config['reversal_strategy']
        self.ema_length = self.config['ema_length']
        self.ema_backcandles = self.config['ema_backcandles']
        self.hl_backcandles = self.config['hl_backcandles']
        self.atr_multiplier = self.config['atr_multiplier']
        self.atr_period = self.config['atr_period']
        self.tp_multiplier = self.config['tp_multiplier']
    
    def calculate_indicators(self, df):
        df['EMA'] = df['Close'].ewm(span=self.ema_length, adjust=False).mean()
        
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(self.atr_period).mean()
        
        df['swing_low'] = df['Low'].rolling(window=self.hl_backcandles, center=False).min()
        df['swing_high'] = df['High'].rolling(window=self.hl_backcandles, center=False).max()
        
        return df
    
    def generate_signals(self, df):
        df = self.calculate_indicators(df)
        df['EMASignal'] = 0
        df['SwingPoint'] = 0
        df['FinalSignal'] = 0
        df['Entry_Price'] = 0.0
        df['SL'] = 0.0
        df['TP'] = 0.0
        
        # Step 1: Identify trends and swing points
        for i in range(self.ema_backcandles, len(df)-2):
            window = df.iloc[i-self.ema_backcandles:i+1]
            above_ema = all(window['Low'] > window['EMA'])
            below_ema = all(window['High'] < window['EMA'])
            
            if above_ema:
                df.loc[df.index[i], 'EMASignal'] = 2
            elif below_ema:
                df.loc[df.index[i], 'EMASignal'] = 1
            
            if df['Low'].iloc[i] <= df['swing_low'].iloc[i]:
                df.loc[df.index[i], 'SwingPoint'] = 2
            elif df['High'].iloc[i] >= df['swing_high'].iloc[i]:
                df.loc[df.index[i], 'SwingPoint'] = 1
        
        # Step 2: Confirmation signals
        for i in range(self.ema_backcandles + 1, len(df)-1):
            current_ema = df['EMASignal'].iloc[i]
            prev_swing = df['SwingPoint'].iloc[i-1]
            current_atr = df['ATR'].iloc[i]
            
            # LONG ENTRY
            if (current_ema == 2 and 
                prev_swing == 2 and 
                df['Close'].iloc[i] > df['Open'].iloc[i] and 
                df['Close'].iloc[i] > df['High'].iloc[i-1]):
                
                entry_price = df['Open'].iloc[i+1] if i+1 < len(df) else df['Close'].iloc[i]
                swing_low_price = df['Low'].iloc[i-1]
                
                df.loc[df.index[i+1], 'FinalSignal'] = 2
                df.loc[df.index[i+1], 'Entry_Price'] = entry_price
                df.loc[df.index[i+1], 'SL'] = swing_low_price - (current_atr * 0.5)
                df.loc[df.index[i+1], 'TP'] = entry_price + ((entry_price - df['SL'].iloc[i+1]) * self.tp_multiplier)
            
            # SHORT ENTRY
            elif (current_ema == 1 and
                  prev_swing == 1 and
                  df['Close'].iloc[i] < df['Open'].iloc[i] and
                  df['Close'].iloc[i] < df['Low'].iloc[i-1]):
                
                entry_price = df['Open'].iloc[i+1] if i+1 < len(df) else df['Close'].iloc[i]
                swing_high_price = df['High'].iloc[i-1]
                
                df.loc[df.index[i+1], 'FinalSignal'] = 1
                df.loc[df.index[i+1], 'Entry_Price'] = entry_price
                df.loc[df.index[i+1], 'SL'] = swing_high_price + (current_atr * 0.5)
                df.loc[df.index[i+1], 'TP'] = entry_price - ((df['SL'].iloc[i+1] - entry_price) * self.tp_multiplier)
        
        return df

def analyze_losing_trades(trades_df, symbol, num_samples=10):
    """Analyze losing trades in detail"""
    losing_trades = trades_df[trades_df['pnl'] < 0].copy()
    
    if len(losing_trades) == 0:
        print(f"   No losing trades to analyze for {symbol}!")
        return
    
    print(f"\n🔍 ANALYZING {len(losing_trades)} LOSING TRADES FOR {symbol}:")
    print("=" * 80)
    
    # Sort by worst losses
    losing_trades = losing_trades.sort_values('pnl')
    
    print(f"Top {min(num_samples, len(losing_trades))} Worst Losses:")
    print("-" * 80)
    
    for i, (idx, trade) in enumerate(losing_trades.head(num_samples).iterrows()):
        loss_pct = (trade['pnl'] / (trade['entry_price'] * 100)) * 100
        print(f"#{i+1}: {trade['type']} | Entry: ${trade['entry_price']:.2f} | "
              f"Exit: ${trade['exit_price']:.2f} | Loss: ${trade['pnl']:.2f} ({loss_pct:.2f}%) | "
              f"Exit: {trade['exit_reason']} | Duration: {trade['duration_minutes']:.1f}min")
    
    # Analyze patterns in losing trades
    print(f"\n📊 LOSING TRADE PATTERNS:")
    print(f"   Average Loss: ${losing_trades['pnl'].mean():.2f}")
    print(f"   Median Loss: ${losing_trades['pnl'].median():.2f}")
    print(f"   Stop Loss Exits: {(losing_trades['exit_reason'] == 'SL').sum()} ({(losing_trades['exit_reason'] == 'SL').mean()*100:.1f}%)")
    print(f"   Take Profit Exits: {(losing_trades['exit_reason'] == 'TP').sum()} ({(losing_trades['exit_reason'] == 'TP').mean()*100:.1f}%)")
    print(f"   Avg Duration: {losing_trades['duration_minutes'].mean():.1f} minutes")
    
    # Long vs Short performance
    long_losses = losing_trades[losing_trades['type'] == 'LONG']
    short_losses = losing_trades[losing_trades['type'] == 'SHORT']
    
    print(f"   Long Trades Losses: {len(long_losses)} (avg ${long_losses['pnl'].mean():.2f})")
    print(f"   Short Trades Losses: {len(short_losses)} (avg ${short_losses['pnl'].mean():.2f})")

def run_detailed_backtest():
    """Run backtest with detailed trade analysis"""
    print("🎯 DETAILED TRADE ANALYSIS")
    print("Identifying patterns in losing trades")
    print("=" * 60)
    
    config_path = "config/vwap_ma_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    strategy = DetailedReversalStrategy(config)
    
    def load_data(symbol):
        filename = f"../data/historical/{symbol}_IBKR_1min_1year_20251110.csv"
        df = pd.read_csv(filename)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        column_map = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}
        return df.rename(columns=column_map)[['Open', 'High', 'Low', 'Close', 'Volume']]
    
    def backtest_detailed(df, symbol):
        print(f"\n📊 BACKTESTING {symbol}...")
        df = strategy.generate_signals(df)
        
        buy_signals = (df['FinalSignal'] == 2).sum()
        sell_signals = (df['FinalSignal'] == 1).sum()
        print(f"   Signals: {buy_signals} buys, {sell_signals} sells")
        
        capital = 10000
        position = 0
        entry_price = 0
        entry_time = None
        sl_price = 0
        tp_price = 0
        trades = []
        
        for i, (idx, row) in enumerate(df.iterrows()):
            current_price = row['Close']
            
            if row['FinalSignal'] != 0 and position == 0:
                # Enter position
                position = 100 if row['FinalSignal'] == 2 else -100
                entry_price = row['Entry_Price']
                sl_price = row['SL']
                tp_price = row['TP']
                entry_time = idx
                trade_type = 'LONG' if position > 0 else 'SHORT'
                
            elif position != 0:
                # Check exit conditions
                exit_trade = False
                exit_reason = ""
                
                if position > 0:  # Long
                    if current_price <= sl_price:
                        exit_trade = True
                        exit_reason = "SL"
                    elif current_price >= tp_price:
                        exit_trade = True
                        exit_reason = "TP"
                else:  # Short
                    if current_price >= sl_price:
                        exit_trade = True
                        exit_reason = "SL"
                    elif current_price <= tp_price:
                        exit_trade = True
                        exit_reason = "TP"
                
                if exit_trade:
                    if position > 0:
                        pnl = (current_price - entry_price) * position
                    else:
                        pnl = (entry_price - current_price) * abs(position)
                    
                    duration = (idx - entry_time).total_seconds() / 60 if entry_time else 0
                    
                    capital += pnl
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': idx,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'sl_price': sl_price,
                        'tp_price': tp_price,
                        'pnl': pnl,
                        'type': trade_type,
                        'exit_reason': exit_reason,
                        'duration_minutes': duration
                    })
                    position = 0
        
        if trades:
            trades_df = pd.DataFrame(trades)
            total_pnl = trades_df['pnl'].sum()
            win_rate = (trades_df['pnl'] > 0).mean() * 100
            
            print(f"📈 {symbol} SUMMARY:")
            print(f"   Trades: {len(trades_df)}, Win Rate: {win_rate:.1f}%, P&L: ${total_pnl:+.2f}")
            
            # Detailed analysis
            analyze_losing_trades(trades_df, symbol)
            
            return trades_df, total_pnl
        return pd.DataFrame(), 0
    
    # Run analysis
    spy_data = load_data('SPY')
    qqq_data = load_data('QQQ')
    
    spy_trades, spy_pnl = backtest_detailed(spy_data, 'SPY')
    qqq_trades, qqq_pnl = backtest_detailed(qqq_data, 'QQQ')
    
    # Final summary
    print(f"\n{'='*80}")
    print("🎯 FINAL STRATEGY SUMMARY")
    print(f"{'='*80}")
    print(f"TOTAL P&L: ${spy_pnl + qqq_pnl:+.2f}")
    print(f"SPY: ${spy_pnl:+.2f}, QQQ: ${qqq_pnl:+.2f}")

if __name__ == "__main__":
    run_detailed_backtest()