# vwap_ma_strategy/main_reversal_config_fixed.py
"""
Reversal Strategy - USING EXISTING TIME FILTERS FROM CONFIG
"""

import os
import sys
import pandas as pd
import numpy as np
import yaml
from datetime import datetime, timedelta
import pytz

sys.path.append('..')

class ConfigFixedReversalStrategy:
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
        
        # TIME FILTERS FROM CONFIG (currently not being used!)
        self.trading_hours = config['trading_hours']
        self.exit_rules = config['exit_rules']
        
        # Market hours
        self.market_open = datetime.strptime('09:30', '%H:%M').time()
        self.market_close = datetime.strptime('16:00', '%H:%M').time()
        self.est = pytz.timezone('US/Eastern')
        
        print("🔧 CONFIG-FIXED STRATEGY")
        print(f"   Using time filters from config:")
        print(f"   - Avoid first {self.trading_hours['avoid_first_minutes']} mins")
        print(f"   - Avoid last {self.trading_hours['avoid_last_minutes']} mins") 
        print(f"   - Max hold: {self.exit_rules['max_hold_bars']} bars")
        print(f"   - Market close exit: {self.exit_rules['market_close_exit']}")
    
    def is_valid_trading_time(self, timestamp_est):
        """Check if current time is valid for trading using config rules"""
        time_only = timestamp_est.time()
        day_of_week = timestamp_est.weekday()
        
        # No trading on weekends
        if day_of_week >= 5:
            return False
        
        # Check if within market hours
        if not (self.market_open <= time_only <= self.market_close):
            return False
        
        # Avoid first X minutes after open
        market_open_dt = datetime.combine(timestamp_est.date(), self.market_open)
        minutes_after_open = (timestamp_est - market_open_dt).total_seconds() / 60
        if minutes_after_open < self.trading_hours['avoid_first_minutes']:
            return False
        
        # Avoid last X minutes before close  
        market_close_dt = datetime.combine(timestamp_est.date(), self.market_close)
        minutes_before_close = (market_close_dt - timestamp_est).total_seconds() / 60
        if minutes_before_close < self.trading_hours['avoid_last_minutes']:
            return False
        
        return True
    
    def should_force_exit(self, timestamp_est, entry_time, current_bar):
        """Check if we should force exit using config rules"""
        time_only = timestamp_est.time()
        
        # Force exit at market close
        if self.exit_rules['market_close_exit'] and time_only >= self.market_close:
            return True, 'MARKET_CLOSE'
        
        # Force exit after max hold bars
        if current_bar >= self.exit_rules['max_hold_bars']:
            return True, 'MAX_HOLD_BARS'
        
        # Force exit if approaching market close (last X minutes)
        market_close_dt = datetime.combine(timestamp_est.date(), self.market_close)
        minutes_before_close = (market_close_dt - timestamp_est).total_seconds() / 60
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
        """Generate signals USING TIME FILTERS from config"""
        df = self.calculate_indicators(df)
        df['EMASignal'] = 0
        df['SwingPoint'] = 0
        df['FinalSignal'] = 0
        df['Entry_Price'] = 0.0
        df['SL'] = 0.0
        df['TP'] = 0.0
        df['ValidTradingTime'] = False
        
        # Convert index to EST for time checks
        df_index_est = df.index.tz_localize('UTC').tz_convert(self.est)
        
        # Step 1: Identify trends and swing points (only during valid times)
        for i in range(self.ema_backcandles, len(df)-2):
            current_time_est = df_index_est[i]
            valid_time = self.is_valid_trading_time(current_time_est)
            df.loc[df.index[i], 'ValidTradingTime'] = valid_time
            
            if not valid_time:
                continue  # Skip outside valid trading hours
            
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
            current_time_est = df_index_est[i]
            if not self.is_valid_trading_time(current_time_est):
                continue
                
            current_ema = df['EMASignal'].iloc[i]
            prev_swing = df['SwingPoint'].iloc[i-1]
            current_atr = df['ATR'].iloc[i]
            current_price = df['Close'].iloc[i]
            current_ema_value = df['EMA'].iloc[i]
            
            # LONG ENTRY with strict EMA check
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
            
            # SHORT ENTRY with strict EMA check
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

def run_config_fixed_backtest():
    """Run backtest USING CONFIG TIME FILTERS"""
    print("🎯 REVERSAL STRATEGY - USING CONFIG TIME FILTERS")
    print("Finally implementing the existing time filters!")
    print("=" * 60)
    
    config_path = "config/vwap_ma_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    strategy = ConfigFixedReversalStrategy(config)
    
    def load_data(symbol):
        filename = f"../data/historical/{symbol}_IBKR_1min_1year_20251110.csv"
        df = pd.read_csv(filename)
        df['date'] = pd.to_datetime(df['date'], utc=True)
        df = df.set_index('date')
        column_map = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}
        return df.rename(columns=column_map)[['Open', 'High', 'Low', 'Close', 'Volume']]
    
    def backtest_fixed(df, symbol):
        print(f"\n📊 BACKTESTING {symbol} (WITH TIME FILTERS)...")
        df = strategy.generate_signals(df)
        
        df_index_est = df.index.tz_convert(strategy.est)
        
        capital = 10000
        position = 0
        entry_price = 0
        entry_time = None
        entry_bar = 0
        trades = []
        current_bar = 0
        
        for i, (idx, row) in enumerate(df.iterrows()):
            current_time_est = df_index_est[i]
            current_price = row['Close']
            current_bar = i
            
            # Check force exit conditions USING CONFIG RULES
            if position != 0:
                should_exit, exit_reason = strategy.should_force_exit(
                    current_time_est, entry_time, current_bar - entry_bar
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
            
            # Enter new positions (only during valid trading times)
            if position == 0 and row['FinalSignal'] != 0 and strategy.is_valid_trading_time(current_time_est):
                position = 100 if row['FinalSignal'] == 2 else -100
                entry_price = row['Entry_Price']
                entry_time = idx
                entry_bar = current_bar
        
        if trades:
            trades_df = pd.DataFrame(trades)
            total_pnl = trades_df['pnl'].sum()
            win_rate = (trades_df['pnl'] > 0).mean() * 100
            
            # Analyze exit reasons
            market_close_exits = trades_df[trades_df['exit_reason'] == 'MARKET_CLOSE']
            max_hold_exits = trades_df[trades_df['exit_reason'] == 'MAX_HOLD_BARS']
            overnight_trades = trades_df[trades_df['duration_minutes'] > (16 * 60)]
            
            print(f"📈 {symbol} RESULTS:")
            print(f"   Trades: {len(trades_df)}, Win Rate: {win_rate:.1f}%, P&L: ${total_pnl:+.2f}")
            print(f"   Market Close Exits: {len(market_close_exits)}")
            print(f"   Max Hold Exits: {len(max_hold_exits)}")
            print(f"   Overnight Trades: {len(overnight_trades)}")
            print(f"   Avg Duration: {trades_df['duration_minutes'].mean():.1f} mins")
            
            return trades_df, total_pnl
        return pd.DataFrame(), 0
    
    # Run analysis
    spy_data = load_data('SPY')
    qqq_data = load_data('QQQ')
    
    spy_trades, spy_pnl = backtest_fixed(spy_data, 'SPY')
    qqq_trades, qqq_pnl = backtest_fixed(qqq_data, 'QQQ')
    
    print(f"\n{'='*80}")
    print("🎯 CONFIG-FIXED STRATEGY SUMMARY")
    print(f"{'='*80}")
    print(f"TOTAL P&L: ${spy_pnl + qqq_pnl:+.2f}")
    print(f"SPY: ${spy_pnl:+.2f}, QQQ: ${qqq_pnl:+.2f}")
    
    # Save trade data
    if not spy_trades.empty:
        spy_trades.to_pickle('trade_data_SPY_config_fixed.pkl')
    if not qqq_trades.empty:
        qqq_trades.to_pickle('trade_data_QQQ_config_fixed.pkl')

if __name__ == "__main__":
    run_config_fixed_backtest()