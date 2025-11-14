# vwap_ma_strategy/main_reversal_detailed_with_analysis.py
"""
Reversal Strategy - COMPLETE VERSION
Combines detailed trade analysis with data saving for visualization
"""

import os
import sys
import pandas as pd
import numpy as np
import yaml
from datetime import datetime, timedelta
import pytz
import pickle

sys.path.append('..')

class ReversalStrategyDetailed:
    def __init__(self, config):
        self.config = config
        
        # Reversal strategy parameters
        reversal_config = config['reversal_strategy']
        self.ema_length = reversal_config['ema_length']
        self.ema_backcandles = reversal_config['ema_backcandles']
        self.hl_backcandles = reversal_config['hl_backcandles']
        self.atr_multiplier = reversal_config['atr_multiplier']
        self.atr_period = reversal_config['atr_period']
        self.tp_multiplier = reversal_config['tp_multiplier']
        self.require_reversal_candle = reversal_config['require_reversal_candle']
        
        # Time filters from config
        self.trading_hours = config['trading_hours']
        self.exit_rules = config['exit_rules']
        
        # Timezone setup - use Eastern Time consistently
        self.est = pytz.timezone('US/Eastern')
        
        print("🔧 REVERSAL STRATEGY - DETAILED ANALYSIS & DATA SAVING")
        print(f"   Complete trade analysis + Data saving for visualization")
    
    def load_data_proper(self, symbol):
        """Load data with proper timezone handling"""
        filename = f"../data/historical/{symbol}_IBKR_1min_1year_20251110.csv"
        df = pd.read_csv(filename)
        
        # Convert to proper timezone-aware datetime and set as index
        df['datetime_et'] = pd.to_datetime(df['date'], utc=True).dt.tz_convert('US/Eastern')
        df = df.set_index('datetime_et')
        
        column_map = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}
        df = df.rename(columns=column_map)[['Open', 'High', 'Low', 'Close', 'Volume']]
        
        print(f"✅ Loaded {symbol} data:")
        print(f"   First: {df.index[0]} (TZ: {df.index[0].tz})")
        print(f"   Last: {df.index[-1]} (TZ: {df.index[-1].tz})")
        
        return df
    
    def is_valid_trading_time(self, timestamp):
        """Check if current time is valid for trading - using Eastern Time"""
        time_only = timestamp.tz_convert(self.est).tz_localize(None).time()
        day_of_week = timestamp.weekday()
        
        # No trading on weekends
        if day_of_week >= 5:
            return False
        
        # Market hours: 9:30 AM - 4:00 PM Eastern
        market_open = datetime.strptime('09:30', '%H:%M').time()
        market_close = datetime.strptime('16:00', '%H:%M').time()
        
        if not (market_open <= time_only <= market_close):
            return False
        
        # Avoid first X minutes after open
        market_open_dt = datetime.combine(timestamp.date(), market_open)
        market_open_dt = self.est.localize(market_open_dt)
        minutes_after_open = (timestamp - market_open_dt).total_seconds() / 60
        if minutes_after_open < self.trading_hours['avoid_first_minutes']:
            return False
        
        # Avoid last X minutes before close  
        market_close_dt = datetime.combine(timestamp.date(), market_close)
        market_close_dt = self.est.localize(market_close_dt)
        minutes_before_close = (market_close_dt - timestamp).total_seconds() / 60
        if minutes_before_close < self.trading_hours['avoid_last_minutes']:
            return False
        
        return True
    
    def should_force_exit(self, timestamp, entry_time, current_bar):
        """Check if we should force exit - using Eastern Time"""
        time_only = timestamp.tz_convert(self.est).tz_localize(None).time()
        
        # Market hours
        market_open = datetime.strptime('09:30', '%H:%M').time()
        market_close = datetime.strptime('16:00', '%H:%M').time()
        
        # Force exit at market close
        if self.exit_rules['market_close_exit'] and time_only >= market_close:
            return True, 'MARKET_CLOSE'
        
        # Force exit after max hold bars
        if current_bar >= self.exit_rules['max_hold_bars']:
            return True, 'MAX_HOLD_BARS'
        
        # Force exit if approaching market close (last X minutes)
        market_close_dt = datetime.combine(timestamp.date(), market_close)
        market_close_dt = self.est.localize(market_close_dt)
        minutes_before_close = (market_close_dt - timestamp).total_seconds() / 60
        if minutes_before_close < self.trading_hours['avoid_last_minutes']:
            return True, 'APPROACHING_CLOSE'
        
        return False, None
    
    def calculate_indicators(self, df):
        """Calculate EMA and swing points"""
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
        """Generate signals with perfect timezone handling"""
        df = self.calculate_indicators(df)
        df['EMASignal'] = 0
        df['SwingPoint'] = 0
        df['FinalSignal'] = 0
        df['Entry_Price'] = 0.0
        df['SL'] = 0.0
        df['TP'] = 0.0
        df['ValidTradingTime'] = False
        
        # Step 1: Identify trends and swing points (only during valid times)
        for i in range(self.ema_backcandles, len(df)-2):
            current_time = df.index[i]
            valid_time = self.is_valid_trading_time(current_time)
            df.loc[df.index[i], 'ValidTradingTime'] = valid_time
            
            if not valid_time:
                continue
            
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
        
        # Step 2: Confirmation signals (only during valid times)
        for i in range(self.ema_backcandles + 1, len(df)-1):
            current_time = df.index[i]
            if not self.is_valid_trading_time(current_time):
                continue
                
            current_ema = df['EMASignal'].iloc[i]
            prev_swing = df['SwingPoint'].iloc[i-1]
            current_atr = df['ATR'].iloc[i]
            current_price = df['Close'].iloc[i]
            current_ema_value = df['EMA'].iloc[i]
            
            # LONG ENTRY
            if (current_ema == 2 and 
                prev_swing == 2 and 
                df['Close'].iloc[i] > df['Open'].iloc[i] and 
                df['Close'].iloc[i] > df['High'].iloc[i-1] and
                current_price > current_ema_value):
                
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
                  df['Close'].iloc[i] < df['Low'].iloc[i-1] and
                  current_price < current_ema_value):
                
                entry_price = df['Open'].iloc[i+1] if i+1 < len(df) else df['Close'].iloc[i]
                swing_high_price = df['High'].iloc[i-1]
                
                df.loc[df.index[i+1], 'FinalSignal'] = 1
                df.loc[df.index[i+1], 'Entry_Price'] = entry_price
                df.loc[df.index[i+1], 'SL'] = swing_high_price + (current_atr * 0.5)
                df.loc[df.index[i+1], 'TP'] = entry_price - ((df['SL'].iloc[i+1] - entry_price) * self.tp_multiplier)
        
        return df

    def analyze_losing_trades(self, trades_df, symbol):
        """COMPLETE LOSING TRADE ANALYSIS - Your preferred format"""
        losing_trades = trades_df[trades_df['pnl'] < 0]
        
        if len(losing_trades) == 0:
            print(f"🎉 No losing trades for {symbol}!")
            return
        
        print(f"\n🔍 ANALYZING {len(losing_trades)} LOSING TRADES FOR {symbol}:")
        print("=" * 80)
        print("Top 10 Worst Losses:")
        print("-" * 80)
        
        # Sort by worst losses
        worst_losses = losing_trades.nsmallest(10, 'pnl')
        
        for i, (idx, trade) in enumerate(worst_losses.iterrows(), 1):
            loss_pct = (trade['pnl'] / (trade['entry_price'] * 100)) * 100
            print(f"#{i}: {trade['type']} | Entry: ${trade['entry_price']:.2f} | "
                  f"Exit: ${trade['exit_price']:.2f} | Loss: ${trade['pnl']:+.2f} "
                  f"({loss_pct:+.2f}%) | Exit: {trade['exit_reason']} | "
                  f"Duration: {trade['duration_minutes']:.1f}min")
        
        print(f"\n📊 LOSING TRADE PATTERNS:")
        print(f"   Average Loss: ${losing_trades['pnl'].mean():.2f}")
        print(f"   Median Loss: ${losing_trades['pnl'].median():.2f}")
        
        # Exit reason analysis
        sl_exits = len(losing_trades[losing_trades['exit_reason'] == 'SL'])
        tp_exits = len(losing_trades[losing_trades['exit_reason'] == 'TP'])
        other_exits = len(losing_trades) - sl_exits - tp_exits
        
        print(f"   Stop Loss Exits: {sl_exits} ({sl_exits/len(losing_trades)*100:.1f}%)")
        print(f"   Take Profit Exits: {tp_exits} ({tp_exits/len(losing_trades)*100:.1f}%)")
        if other_exits > 0:
            print(f"   Other Exits: {other_exits} ({other_exits/len(losing_trades)*100:.1f}%)")
        
        print(f"   Avg Duration: {losing_trades['duration_minutes'].mean():.1f} minutes")
        
        # Long vs Short analysis
        long_losses = losing_trades[losing_trades['type'] == 'LONG']
        short_losses = losing_trades[losing_trades['type'] == 'SHORT']
        
        if len(long_losses) > 0:
            print(f"   Long Trades Losses: {len(long_losses)} (avg ${long_losses['pnl'].mean():.2f})")
        if len(short_losses) > 0:
            print(f"   Short Trades Losses: {len(short_losses)} (avg ${short_losses['pnl'].mean():.2f})")

    def save_trade_analysis(self, trades_df, symbol):
        """Save trade data for visualization"""
        # Save detailed trade data
        trades_df.to_csv(f'trade_analysis_{symbol}_detailed.csv', index=False)
        
        # Save to pickle for chart generation
        with open(f'trade_data_{symbol}.pkl', 'wb') as f:
            pickle.dump(trades_df, f)
        
        print(f"✅ Saved {len(trades_df)} {symbol} trades to trade_data_{symbol}.pkl")

def run_complete_analysis():
    """Run complete analysis with both console output and data saving"""
    print("🎯 DETAILED TRADE ANALYSIS - COMPLETE VERSION")
    print("Identifying patterns in losing trades + Saving data for visualization")
    print("=" * 60)
    
    config_path = "config/vwap_ma_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    strategy = ReversalStrategyDetailed(config)
    
    def backtest_complete(df, symbol):
        print(f"\n📊 BACKTESTING {symbol}...")
        df = strategy.generate_signals(df)
        
        capital = 10000
        position = 0
        entry_price = 0
        entry_time = None
        entry_bar = 0
        trades = []
        current_bar = 0
        
        buy_signals = len(df[df['FinalSignal'] == 2])
        sell_signals = len(df[df['FinalSignal'] == 1])
        print(f"   Signals: {buy_signals} buys, {sell_signals} sells")
        
        for i, (idx, row) in enumerate(df.iterrows()):
            current_time = idx
            current_price = row['Close']
            current_bar = i
            
            # Check force exit conditions
            if position != 0:
                should_exit, exit_reason = strategy.should_force_exit(
                    current_time, entry_time, current_bar - entry_bar
                )
                if should_exit:
                    if position > 0:
                        pnl = (current_price - entry_price) * position
                    else:
                        pnl = (entry_price - current_price) * abs(position)
                    
                    capital += pnl
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': idx,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'pnl': pnl,
                        'type': 'LONG' if position > 0 else 'SHORT',
                        'exit_reason': exit_reason,
                        'duration_minutes': (idx - entry_time).total_seconds() / 60,
                        'duration_bars': current_bar - entry_bar
                    })
                    position = 0
                    entry_time = None
                    entry_bar = 0
            
            # Check normal exit conditions
            if position > 0 and (current_price <= row['SL'] or current_price >= row['TP']):
                pnl = (current_price - entry_price) * position
                capital += pnl
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': idx,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'pnl': pnl,
                    'type': 'LONG',
                    'exit_reason': 'SL' if current_price <= row['SL'] else 'TP',
                    'duration_minutes': (idx - entry_time).total_seconds() / 60,
                    'duration_bars': current_bar - entry_bar
                })
                position = 0
                entry_time = None
                entry_bar = 0
            elif position < 0 and (current_price >= row['SL'] or current_price <= row['TP']):
                pnl = (entry_price - current_price) * abs(position)
                capital += pnl
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': idx,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'pnl': pnl,
                    'type': 'SHORT',
                    'exit_reason': 'SL' if current_price >= row['SL'] else 'TP',
                    'duration_minutes': (idx - entry_time).total_seconds() / 60,
                    'duration_bars': current_bar - entry_bar
                })
                position = 0
                entry_time = None
                entry_bar = 0
            
            # Enter new positions
            if position == 0 and row['FinalSignal'] != 0 and strategy.is_valid_trading_time(current_time):
                position = 100 if row['FinalSignal'] == 2 else -100
                entry_price = row['Entry_Price']
                entry_time = idx
                entry_bar = current_bar
        
        if trades:
            trades_df = pd.DataFrame(trades)
            total_pnl = trades_df['pnl'].sum()
            win_rate = (trades_df['pnl'] > 0).mean() * 100
            
            print(f"📈 {symbol} SUMMARY:")
            print(f"   Trades: {len(trades_df)}, Win Rate: {win_rate:.1f}%, P&L: ${total_pnl:+.2f}")
            
            # COMPLETE ANALYSIS - Your preferred format
            strategy.analyze_losing_trades(trades_df, symbol)
            
            # SAVE DATA for visualization
            strategy.save_trade_analysis(trades_df, symbol)
            
            return trades_df, total_pnl
        return pd.DataFrame(), 0
    
    # Run analysis
    spy_data = strategy.load_data_proper('SPY')
    qqq_data = strategy.load_data_proper('QQQ')
    
    spy_trades, spy_pnl = backtest_complete(spy_data, 'SPY')
    qqq_trades, qqq_pnl = backtest_complete(qqq_data, 'QQQ')
    
    # Save combined data
    if not spy_trades.empty and not qqq_trades.empty:
        all_trades = pd.concat([spy_trades, qqq_trades], ignore_index=True)
        with open('trade_data_ALL.pkl', 'wb') as f:
            pickle.dump(all_trades, f)
        print(f"\n✅ Saved combined trade data: {len(all_trades)} trades")
    
    print(f"\n{'='*80}")
    print("🎯 FINAL STRATEGY SUMMARY")
    print(f"{'='*80}")
    print(f"TOTAL P&L: ${spy_pnl + qqq_pnl:+.2f}")
    print(f"SPY: ${spy_pnl:+.2f}, QQQ: ${qqq_pnl:+.2f}")
    
    print(f"\n{'='*80}")
    print("🎯 TRADE DATA SAVED - READY FOR VISUALIZATION")
    print(f"{'='*80}")
    print("Files created:")
    if not spy_trades.empty:
        print(f"  - trade_data_SPY.pkl ({len(spy_trades)} trades)")
    if not qqq_trades.empty:
        print(f"  - trade_data_QQQ.pkl ({len(qqq_trades)} trades)")
    if not spy_trades.empty and not qqq_trades.empty:
        print(f"  - trade_data_ALL.pkl ({len(spy_trades) + len(qqq_trades)} total trades)")

if __name__ == "__main__":
    run_complete_analysis()