# vwap_ma_strategy/main_reversal_timezone_perfect.py
"""
Reversal Strategy - PERFECT TIMEZONE HANDLING
Consistent timezone handling from data loading to trade saving
"""

import os
import sys
import pandas as pd
import numpy as np
import yaml
from datetime import datetime, timedelta
import pytz

sys.path.append('..')

class TimezonePerfectReversalStrategy:
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
        
        print("🔧 PERFECT TIMEZONE STRATEGY")
        print(f"   Data: Eastern Time with DST (already correct)")
        print(f"   All calculations: Eastern Time")
        print(f"   Trade saving: Eastern Time")
    
    def load_data_proper(self, symbol):
        """Load data with proper timezone handling"""
        filename = f"../data/historical/{symbol}_IBKR_1min_1year_20251110.csv"
        df = pd.read_csv(filename)
        
        # Data already has correct Eastern Time with DST - keep it as is!
        df['date'] = pd.to_datetime(df['date'])  # Keep the built-in timezone info
        df = df.set_index('date')
        
        column_map = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}
        df = df.rename(columns=column_map)[['Open', 'High', 'Low', 'Close', 'Volume']]
        
        print(f"✅ Loaded {symbol} data:")
        print(f"   First: {df.index[0]} (TZ: {df.index[0].tz})")
        print(f"   Last: {df.index[-1]} (TZ: {df.index[-1].tz})")
        
        return df
    
    def is_valid_trading_time(self, timestamp):
        """Check if current time is valid for trading - using Eastern Time"""
        # Convert to timezone-naive for time comparison (since market hours don't care about DST)
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
        market_open_dt = self.est.localize(market_open_dt)  # Make timezone-aware
        minutes_after_open = (timestamp - market_open_dt).total_seconds() / 60
        if minutes_after_open < self.trading_hours['avoid_first_minutes']:
            return False
        
        # Avoid last X minutes before close  
        market_close_dt = datetime.combine(timestamp.date(), market_close)
        market_close_dt = self.est.localize(market_close_dt)  # Make timezone-aware
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
        
        # Data index already has correct Eastern Time - use it directly!
        
        # Step 1: Identify trends and swing points (only during valid times)
        for i in range(self.ema_backcandles, len(df)-2):
            current_time = df.index[i]  # Already in Eastern Time
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
            current_time = df.index[i]  # Already in Eastern Time
            if not self.is_valid_trading_time(current_time):
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

def run_timezone_perfect_backtest():
    """Run backtest with PERFECT timezone handling"""
    print("🎯 REVERSAL STRATEGY - PERFECT TIMEZONE HANDLING")
    print("Consistent Eastern Time throughout the pipeline")
    print("=" * 60)
    
    config_path = "config/vwap_ma_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    strategy = TimezonePerfectReversalStrategy(config)
    
    def backtest_perfect(df, symbol):
        print(f"\n📊 BACKTESTING {symbol} (PERFECT TIMEZONE)...")
        df = strategy.generate_signals(df)
        
        capital = 10000
        position = 0
        entry_price = 0
        entry_time = None
        entry_bar = 0
        trades = []
        current_bar = 0
        
        for i, (idx, row) in enumerate(df.iterrows()):
            current_time = idx  # Already in correct Eastern Time
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
            
            # Enter new positions (only during valid trading times)
            if position == 0 and row['FinalSignal'] != 0 and strategy.is_valid_trading_time(current_time):
                position = 100 if row['FinalSignal'] == 2 else -100
                entry_price = row['Entry_Price']
                entry_time = idx  # Save as timezone-aware timestamp
                entry_bar = current_bar
        
        if trades:
            trades_df = pd.DataFrame(trades)
            total_pnl = trades_df['pnl'].sum()
            win_rate = (trades_df['pnl'] > 0).mean() * 100
            
            # Analyze results
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
    
    # Run analysis with proper data loading
    spy_data = strategy.load_data_proper('SPY')
    qqq_data = strategy.load_data_proper('QQQ')
    
    spy_trades, spy_pnl = backtest_perfect(spy_data, 'SPY')
    qqq_trades, qqq_pnl = backtest_perfect(qqq_data, 'QQQ')
    
    print(f"\n{'='*80}")
    print("🎯 PERFECT TIMEZONE STRATEGY SUMMARY")
    print(f"{'='*80}")
    print(f"TOTAL P&L: ${spy_pnl + qqq_pnl:+.2f}")
    print(f"SPY: ${spy_pnl:+.2f}, QQQ: ${qqq_pnl:+.2f}")
    
    # Save trade data WITH CORRECT TIMEZONES
    if not spy_trades.empty:
        spy_trades.to_pickle('trade_data_SPY_timezone_perfect.pkl')
        print(f"✅ Saved SPY trades with correct timezones")
    if not qqq_trades.empty:
        qqq_trades.to_pickle('trade_data_QQQ_timezone_perfect.pkl')
        print(f"✅ Saved QQQ trades with correct timezones")

if __name__ == "__main__":
    run_timezone_perfect_backtest()