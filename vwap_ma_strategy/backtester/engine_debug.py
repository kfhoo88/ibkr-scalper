# vwap_ma_strategy/backtester/engine_debug.py
import pandas as pd
import numpy as np
import yaml
import logging
from datetime import datetime, time
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.data_loader import DataLoader
from utils.option_pricing import OptionPricer

class VWAPMABacktesterDebug:
    def __init__(self, config_path="config/vwap_ma_config.yaml"):
        self.load_config(config_path)
        self.setup_logging()
        self.data_loader = DataLoader(self.config['backtest']['data_path'])
        self.option_pricer = OptionPricer()
        self.trades = []
        self.signals_found = 0
        self.failed_conditions = {
            'ma_trend': 0,
            'vwap_position': 0, 
            'candle_confirmation': 0,
            'pullback': 0,
            'market_filters': 0,
            'trading_hours': 0
        }
        
    def load_config(self, config_path):
        full_path = os.path.join(os.path.dirname(__file__), '..', config_path)
        with open(full_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        if 'logging' not in self.config:
            self.config['logging'] = {'level': 'INFO', 'save_signals': True, 'save_trades': True}
        
        self.ma_fast = self.config['indicators']['ma_fast']
        self.ma_slow = self.config['indicators']['ma_slow']
        self.profit_target = self.config['exit_rules']['profit_target_pct']  # 0.15
        self.stop_loss = self.config['exit_rules']['stop_loss_pct']          # 0.08
        # self.profit_target = self.config['exit_rules']['profit_target'] / 100
        # self.stop_loss = self.config['exit_rules']['stop_loss'] / 100
        self.hedge_trigger = self.config['exit_rules']['hedge_trigger'] / 100
        
    def setup_logging(self):
        logging.basicConfig(
            level=getattr(logging, self.config['logging']['level']),
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def calculate_indicators(self, df):
        if hasattr(df.index, 'tz') and df.index.tz is not None:
            df.index = df.index.tz_convert(None)
        
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, utc=True).tz_convert(None)
        
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['tpv'] = df['typical_price'] * df['volume']
        df['date'] = df.index.date
        df['daily_tpv'] = df.groupby('date')['tpv'].cumsum()
        df['daily_volume'] = df.groupby('date')['volume'].cumsum()
        df['vwap'] = df['daily_tpv'] / df['daily_volume']
        df['ma_fast'] = df['close'].rolling(window=self.ma_fast).mean()
        df['ma_slow'] = df['close'].rolling(window=self.ma_slow).mean()
        df['volume_sma'] = df['volume'].rolling(window=self.config['indicators']['volume_period']).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        df['tr'] = np.maximum(df['high'] - df['low'], np.maximum(abs(df['high'] - df['close'].shift(1)), abs(df['low'] - df['close'].shift(1))))
        df['atr'] = df['tr'].rolling(window=self.config['indicators']['atr_period']).mean()
        df['atr_percentage'] = df['atr'] / df['close']
        
        return df
    
    def is_trading_hours(self, timestamp):
        current_time = timestamp.time()
        morning_start = time.fromisoformat(self.config['trading_hours']['morning_start'])
        morning_end = time.fromisoformat(self.config['trading_hours']['morning_end'])
        afternoon_start = time.fromisoformat(self.config['trading_hours']['afternoon_start'])
        afternoon_end = time.fromisoformat(self.config['trading_hours']['afternoon_end'])
        
        # Avoid first minutes
        market_open = time(9, 30)
        avoid_first_minutes = self.config['trading_hours']['avoid_first_minutes']
        if current_time < time(market_open.hour, market_open.minute + avoid_first_minutes):
            return False
            
        # Avoid last minutes - fixed calculation
        market_close = time(16, 0)
        avoid_last_minutes = self.config['trading_hours']['avoid_last_minutes']
        
        # Calculate the cutoff time properly
        cutoff_minute = market_close.minute - avoid_last_minutes
        if cutoff_minute < 0:
            cutoff_hour = market_close.hour - 1
            cutoff_minute = 60 + cutoff_minute
        else:
            cutoff_hour = market_close.hour
        
        cutoff_time = time(cutoff_hour, cutoff_minute)
        
        if current_time > cutoff_time:
            return False
        
        in_morning = morning_start <= current_time <= morning_end
        in_afternoon = afternoon_start <= current_time <= afternoon_end
        
        return in_morning or in_afternoon
    
    def detect_pullback(self, df, current_index, direction):
        if current_index < 2:
            return False
        
        if direction == "long":
            red_candles = 0
            for i in range(1, min(4, current_index + 1)):
                if df.iloc[current_index - i]['close'] < df.iloc[current_index - i]['open']:
                    red_candles += 1
                else:
                    break
            return red_candles >= self.config['entry_rules']['pullback_min_candles']
        else:
            green_candles = 0
            for i in range(1, min(4, current_index + 1)):
                if df.iloc[current_index - i]['close'] > df.iloc[current_index - i]['open']:
                    green_candles += 1
                else:
                    break
            return green_candles >= self.config['entry_rules']['pullback_min_candles']
    
    def generate_signal(self, df, current_index, symbol):
        if current_index < self.ma_slow:
            return None
        
        current = df.iloc[current_index]
        prev = df.iloc[current_index - 1]
        
        # Debug each condition
        debug_info = {}
        
        # Market filters
        atr_ok = current['atr_percentage'] >= self.config['market_filters']['min_atr_percentage']
        volume_ok = current['volume_ratio'] >= self.config['market_filters']['min_volume_ratio']
        trading_hours_ok = self.is_trading_hours(current.name)
        
        if not atr_ok:
            self.failed_conditions['market_filters'] += 1
            return None
        if not volume_ok:
            self.failed_conditions['market_filters'] += 1
            return None
        if not trading_hours_ok:
            self.failed_conditions['trading_hours'] += 1
            return None
        
        # Check LONG conditions
        ma_trend_long = current['ma_fast'] > current['ma_slow']
        vwap_position_long = current['close'] > current['vwap']
        candle_confirmation_long = current['close'] > current['ma_fast'] and prev['close'] <= prev['ma_fast']
        pullback_long = self.detect_pullback(df, current_index, "long")
        
        # Check SHORT conditions  
        ma_trend_short = current['ma_fast'] < current['ma_slow']
        vwap_position_short = current['close'] < current['vwap']
        candle_confirmation_short = current['close'] < current['ma_fast'] and prev['close'] >= prev['ma_fast']
        pullback_short = self.detect_pullback(df, current_index, "short")
        
        signal = None
        
        if ma_trend_long and vwap_position_long and candle_confirmation_long and pullback_long:
            option_price = self.option_pricer.calculate_option_price(df, current_index, symbol)
            signal = {'type': 'LONG', 'timestamp': current.name, 'price': current['close'], 'option_price': option_price, 'symbol': symbol}
            self.signals_found += 1
            self.logger.info(f"LONG signal found at {current.name}")
            
        elif ma_trend_short and vwap_position_short and candle_confirmation_short and pullback_short:
            option_price = self.option_pricer.calculate_option_price(df, current_index, symbol)
            signal = {'type': 'SHORT', 'timestamp': current.name, 'price': current['close'], 'option_price': option_price, 'symbol': symbol}
            self.signals_found += 1
            self.logger.info(f"SHORT signal found at {current.name}")
        else:
            # Track why signals failed
            if not (ma_trend_long or ma_trend_short):
                self.failed_conditions['ma_trend'] += 1
            elif not (vwap_position_long or vwap_position_short):
                self.failed_conditions['vwap_position'] += 1
            elif not (candle_confirmation_long or candle_confirmation_short):
                self.failed_conditions['candle_confirmation'] += 1
            elif not (pullback_long or pullback_short):
                self.failed_conditions['pullback'] += 1
        
        return signal

    def run_backtest(self, symbol):
        self.logger.info(f"Starting backtest for {symbol}")
        
        df = self.data_loader.load_symbol_data(symbol)
        if df is None:
            return None
            
        df = self.calculate_indicators(df)
        
        trades = []
        current_trade = None
        daily_trades = 0
        current_date = None
        
        # Sample some data to check indicators
        sample_idx = len(df) - 100  # Look at last 100 candles
        if sample_idx > 0:
            sample = df.iloc[sample_idx:sample_idx+5]
            self.logger.info(f"Sample data - MA Fast: {sample['ma_fast'].values}, MA Slow: {sample['ma_slow'].values}, VWAP: {sample['vwap'].values}")
        
        for i in range(len(df)):
            current_time = df.index[i]
            
            if current_date != current_time.date():
                current_date = current_time.date()
                daily_trades = 0
            
            if current_trade is None and daily_trades < self.config['position_management']['max_trades_per_day']:
                signal = self.generate_signal(df, i, symbol)
                if signal:
                    current_trade = {
                        'entry_time': signal['timestamp'], 'entry_price': signal['price'],
                        'option_entry_price': signal['option_price'], 'type': signal['type'],
                        'symbol': symbol, 'contracts': self.config['position_management']['max_position_size']
                    }
                    daily_trades += 1
            
            if current_trade:
                exit_reason = self.check_exit_conditions(df, i, current_trade)
                if exit_reason:
                    trades.append(self.close_trade(current_trade, df.iloc[i], exit_reason, symbol))
                    current_trade = None
        
        # Print debug information
        self.logger.info(f"Signals found: {self.signals_found}")
        self.logger.info(f"Failed conditions: {self.failed_conditions}")
        
        return self.calculate_performance(trades)

    def check_exit_conditions(self, df, current_index, trade):
        current = df.iloc[current_index]
        current_option_price = self.option_pricer.calculate_option_price(df, current_index, trade['symbol'])
        
        if trade['type'] == 'LONG':
            pnl_pct = (current_option_price - trade['option_entry_price']) / trade['option_entry_price']
        else:
            pnl_pct = (trade['option_entry_price'] - current_option_price) / trade['option_entry_price']
        
        if pnl_pct >= self.profit_target:
            return 'profit_target'
        if pnl_pct <= -self.stop_loss:
            return 'stop_loss'
        
        current_time = current.name.time()
        exit_time = time.fromisoformat(self.config['trading_hours']['afternoon_end'])
        if current_time >= exit_time:
            return 'market_close'
        
        return None

    def close_trade(self, trade, exit_data, exit_reason, symbol):
        trade['exit_time'] = exit_data.name
        trade['exit_price'] = exit_data['close']
        trade['exit_reason'] = exit_reason
        trade['option_exit_price'] = self.option_pricer.calculate_option_price(pd.DataFrame([exit_data]), 0, symbol)
        
        if trade['type'] == 'LONG':
            trade['pnl'] = (trade['option_exit_price'] - trade['option_entry_price']) * trade['contracts']
        else:
            trade['pnl'] = (trade['option_entry_price'] - trade['option_exit_price']) * trade['contracts']
        
        commission = self.config['backtest']['commission_per_trade'] * trade['contracts']
        slippage = trade['option_entry_price'] * self.config['backtest']['slippage_per_trade'] * trade['contracts']
        trade['pnl'] -= (commission + slippage)
        trade['pnl_pct'] = (trade['pnl'] / (trade['option_entry_price'] * trade['contracts'])) * 100
        
        self.logger.info(f"Closed {trade['type']} trade: {exit_reason}, P&L: ${trade['pnl']:.2f}")
        
        return trade

    def calculate_performance(self, trades):
        if not trades:
            return {"error": "No trades executed", "signals_found": self.signals_found, "failed_conditions": self.failed_conditions}
        
        df_trades = pd.DataFrame(trades)
        
        metrics = {
            'total_trades': len(trades),
            'winning_trades': len(df_trades[df_trades['pnl'] > 0]),
            'losing_trades': len(df_trades[df_trades['pnl'] < 0]),
            'total_pnl': df_trades['pnl'].sum(),
            'avg_pnl': df_trades['pnl'].mean(),
            'win_rate': len(df_trades[df_trades['pnl'] > 0]) / len(trades) * 100,
            'largest_win': df_trades['pnl'].max(),
            'largest_loss': df_trades['pnl'].min(),
            'profit_factor': abs(df_trades[df_trades['pnl'] > 0]['pnl'].sum() / df_trades[df_trades['pnl'] < 0]['pnl'].sum()) if df_trades[df_trades['pnl'] < 0]['pnl'].sum() != 0 else float('inf'),
            'signals_found': self.signals_found,
            'failed_conditions': self.failed_conditions
        }
        
        return metrics

    def run_all_backtests(self):
        results = {}
        
        for symbol in self.config['symbols']['enabled']:
            print(f"\n{'='*50}")
            print(f"BACKTESTING: {symbol}")
            print(f"{'='*50}")
            
            # Reset counters for each symbol
            self.signals_found = 0
            self.failed_conditions = {k: 0 for k in self.failed_conditions.keys()}
            
            result = self.run_backtest(symbol)
            results[symbol] = result
            
            if result and 'error' not in result:
                print(f"Total Trades: {result['total_trades']}")
                print(f"Win Rate: {result['win_rate']:.2f}%")
                print(f"Total P&L: ${result['total_pnl']:.2f}")
            else:
                print(f"No trades executed")
                if result and 'signals_found' in result:
                    print(f"Signals found: {result['signals_found']}")
                    print(f"Failed conditions: {result['failed_conditions']}")
        
        return results