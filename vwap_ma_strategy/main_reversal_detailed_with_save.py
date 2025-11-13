# vwap_ma_strategy/main_reversal_detailed_with_save.py
"""
Detailed Reversal Strategy - Modified to SAVE trade data for visualization
"""

import os
import sys
import pandas as pd
import numpy as np
import yaml
from datetime import datetime
import pickle  # To save trade data

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

def save_trade_data(trades_df, symbol, filename):
    """Save trade data for visualization"""
    trades_df['symbol'] = symbol
    trades_df.to_pickle(filename)
    print(f"✅ Saved {len(trades_df)} {symbol} trades to {filename}")

def run_detailed_backtest_with_save():
    """Run backtest and SAVE trade data for visualization"""
    print("🎯 DETAILED TRADE ANALYSIS - SAVING DATA FOR VISUALIZATION")
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
    
    all_trades = {}  # Store trades for both symbols
    
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
            
            # Save trade data
            save_trade_data(trades_df, symbol, f'trade_data_{symbol}.pkl')
            all_trades[symbol] = trades_df
            
            return trades_df, total_pnl
        return pd.DataFrame(), 0
    
    # Run analysis and save data
    spy_data = load_data('SPY')
    qqq_data = load_data('QQQ')
    
    spy_trades, spy_pnl = backtest_detailed(spy_data, 'SPY')
    qqq_trades, qqq_pnl = backtest_detailed(qqq_data, 'QQQ')
    
    # Save combined trade data
    if not spy_trades.empty and not qqq_trades.empty:
        all_trades_df = pd.concat([spy_trades, qqq_trades], ignore_index=True)
        all_trades_df.to_pickle('trade_data_ALL.pkl')
        print(f"\n✅ Saved combined trade data: {len(all_trades_df)} trades")
    
    print(f"\n{'='*80}")
    print("🎯 TRADE DATA SAVED - READY FOR VISUALIZATION")
    print(f"{'='*80}")
    print(f"Files created:")
    print(f"  - trade_data_SPY.pkl ({len(spy_trades)} trades)")
    print(f"  - trade_data_QQQ.pkl ({len(qqq_trades)} trades)") 
    print(f"  - trade_data_ALL.pkl ({len(spy_trades) + len(qqq_trades)} total trades)")
    print(f"\nNext: Run plot_trade_analysis.py to generate charts!")

if __name__ == "__main__":
    run_detailed_backtest_with_save()