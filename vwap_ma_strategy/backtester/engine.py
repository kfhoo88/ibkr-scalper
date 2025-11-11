# vwap_ma_strategy/backtester/engine.py
import pandas as pd
import numpy as np
import yaml
import logging
from datetime import datetime, time
import os
import sys
import pytz

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.data_loader import DataLoader
from utils.option_pricing import OptionPricer

class VWAPMABacktester:
    def __init__(self, config_path="config/vwap_ma_config.yaml"):
        self.load_config(config_path)
        self.setup_logging()
        self.data_loader = DataLoader(self.config['backtest']['data_path'])
        self.option_pricer = OptionPricer()
        self.trades = []
        
    def load_config(self, config_path):
        """Load configuration from YAML file"""
        full_path = os.path.join(os.path.dirname(__file__), '..', config_path)
        with open(full_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        # Set instance variables for easy access
        self.ma_fast = self.config['indicators']['ma_fast']
        self.ma_slow = self.config['indicators']['ma_slow']
        self.profit_target = self.config['exit_rules']['profit_target_pct']  # 0.15
        self.stop_loss = self.config['exit_rules']['stop_loss_pct']          # 0.08
        #self.profit_target = self.config['exit_rules']['profit_target'] / 100
        #self.stop_loss = self.config['exit_rules']['stop_loss'] / 100
        self.hedge_trigger = self.config['exit_rules']['hedge_trigger'] / 100
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config['logging']['level']),
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def calculate_indicators(self, df):
        """Calculate VWAP, MAs, and other indicators"""
        # Handle timezone-aware datetime index
        if hasattr(df.index, 'tz') and df.index.tz is not None:
            df.index = df.index.tz_convert(None)  # Remove timezone
        
        # Ensure we have a proper datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, utc=True).tz_convert(None)
        
        # VWAP Calculation (resets daily)
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['tpv'] = df['typical_price'] * df['volume']
        
        # Daily cumulative calculations
        df['date'] = df.index.date
        df['daily_tpv'] = df.groupby('date')['tpv'].cumsum()
        df['daily_volume'] = df.groupby('date')['volume'].cumsum()
        df['vwap'] = df['daily_tpv'] / df['daily_volume']
        
        # Moving Averages
        df['ma_fast'] = df['close'].rolling(window=self.ma_fast).mean()
        df['ma_slow'] = df['close'].rolling(window=self.ma_slow).mean()
        
        # Volume SMA
        df['volume_sma'] = df['volume'].rolling(
            window=self.config['indicators']['volume_period']
        ).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # ATR for volatility
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['atr'] = df['tr'].rolling(window=self.config['indicators']['atr_period']).mean()
        df['atr_percentage'] = df['atr'] / df['close']
        
        return df
    
    def is_trading_hours(self, timestamp):
        """Check if current time is within trading hours (EST)"""
        # Convert to EST timezone
        est = pytz.timezone('US/Eastern')
        if timestamp.tzinfo is None:
            # If naive datetime, assume it's UTC and convert to EST
            timestamp = pytz.utc.localize(timestamp).astimezone(est)
        else:
            # If timezone-aware, convert to EST
            timestamp = timestamp.astimezone(est)
        
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
            
        # Avoid last minutes
        market_close = time(16, 0)
        avoid_last_minutes = self.config['trading_hours']['avoid_last_minutes']
        
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
        """Detect pullback pattern"""
        if current_index < 2:
            return False
        
        if direction == "long":
            # Look for one or more red candles before potential entry
            red_candles = 0
            for i in range(1, min(4, current_index + 1)):
                if df.iloc[current_index - i]['close'] < df.iloc[current_index - i]['open']:
                    red_candles += 1
                else:
                    break
            return red_candles >= self.config['entry_rules']['pullback_min_candles']
        
        else:  # short
            # Look for one or more green candles before potential entry
            green_candles = 0
            for i in range(1, min(4, current_index + 1)):
                if df.iloc[current_index - i]['close'] > df.iloc[current_index - i]['open']:
                    green_candles += 1
                else:
                    break
            return green_candles >= self.config['entry_rules']['pullback_min_candles']
    
    def generate_signal(self, df, current_index, symbol):
        """Generate trading signal based on VWAP + MA strategy"""
        if current_index < self.ma_slow:
            return None
        
        current = df.iloc[current_index]
        prev = df.iloc[current_index - 1]
        
        # Check market filters
        if current['atr_percentage'] < self.config['market_filters']['min_atr_percentage']:
            return None
        
        if current['volume_ratio'] < self.config['market_filters']['min_volume_ratio']:
            return None
        
        # Check trading hours
        if not self.is_trading_hours(current.name):
            return None
        
        signal = None
        
        # LONG Signal: MA9 > MA21, Price above VWAP, Green candle closes above MA9 after pullback
        if (current['ma_fast'] > current['ma_slow'] and
            current['close'] > current['vwap'] and
            current['close'] > current['ma_fast'] and
            prev['close'] <= prev['ma_fast'] and
            self.detect_pullback(df, current_index, "long")):
            
            signal = {
                'type': 'LONG',
                'timestamp': current.name,
                'price': current['close'],
                'symbol': symbol
                # REMOVED: 'option_price': option_price
            }
        
        # SHORT Signal: MA9 < MA21, Price below VWAP, Red candle closes below MA9 after pullback
        elif (current['ma_fast'] < current['ma_slow'] and
              current['close'] < current['vwap'] and
              current['close'] < current['ma_fast'] and
              prev['close'] >= prev['ma_fast'] and
              self.detect_pullback(df, current_index, "short")):
            
            signal = {
                'type': 'SHORT',
                'timestamp': current.name,
                'price': current['close'],
                'symbol': symbol
                # REMOVED: 'option_price': option_price
            }
        
        return signal

    def run_backtest(self, symbol):
        """Run complete backtest for symbol"""
        self.logger.info(f"Starting backtest for {symbol}")
        
        # Load and prepare data
        df = self.data_loader.load_symbol_data(symbol)
        if df is None:
            return None
            
        if not self.data_loader.validate_data(df, symbol):
            return None
            
        df = self.calculate_indicators(df)
        
        # Initialize tracking variables
        trades = []
        current_trade = None
        daily_trades = 0
        current_date = None
        
        for i in range(len(df)):
            current_time = df.index[i]
            
            # Reset daily trade count
            if current_date != current_time.date():
                current_date = current_time.date()
                daily_trades = 0
            
            # Check if we can take new trades
            if (current_trade is None and 
                daily_trades < self.config['position_management']['max_trades_per_day']):
                
                signal = self.generate_signal(df, i, symbol)
                if signal:
                    # Enter trade - SIMPLIFIED FOR DIRECT PRICE TRADING
                    current_trade = {
                        'entry_time': signal['timestamp'],
                        'entry_price': signal['price'],
                        'type': signal['type'],
                        'symbol': symbol,
                        'shares': 100  # Trade 100 shares directly instead of options
                    }
                    daily_trades += 1
                    self.logger.info(f"Entered {signal['type']} trade for {symbol} at {signal['timestamp']}")
            
            # Manage existing trade
            if current_trade:
                exit_reason = self.check_exit_conditions(df, i, current_trade)
                if exit_reason:
                    trades.append(self.close_trade(current_trade, df.iloc[i], exit_reason, symbol))
                    current_trade = None
        
        # Calculate performance metrics
        return self.calculate_performance(trades)

    def check_exit_conditions(self, df, current_index, trade):
        """Check if trade should be exited based on price moves"""
        current = df.iloc[current_index]
    
        # Calculate P&L percentage based on PRICE MOVES
        if trade['type'] == 'LONG':
            pnl_pct = (current['close'] - trade['entry_price']) / trade['entry_price']
        else:
            pnl_pct = (trade['entry_price'] - current['close']) / trade['entry_price']
        
        # Use PRICE-BASED targets (0.15 and 0.08)
        if pnl_pct >= self.profit_target:  # Should be 0.0015
            return 'profit_target'
        if pnl_pct <= -self.stop_loss:     # Should be -0.0008  
            return 'stop_loss'
        
        # Market close exit
        current_time = current.name.time()
        exit_time = time.fromisoformat(self.config['trading_hours']['afternoon_end'])
        if current_time >= exit_time:
            return 'market_close'
        
        return None

    def close_trade(self, trade, exit_data, exit_reason, symbol):
        trade['exit_time'] = exit_data.name
        trade['exit_price'] = exit_data['close']
        trade['exit_reason'] = exit_reason
        
        # Calculate P&L based on price moves
        if trade['type'] == 'LONG':
            trade['pnl'] = (trade['exit_price'] - trade['entry_price']) * trade.get('shares', 1)
        else:
            trade['pnl'] = (trade['entry_price'] - trade['exit_price']) * trade.get('shares', 1)
        
        # Apply commission (simplified)
        trade['pnl'] -= self.config['backtest']['commission_per_trade']
        
        trade['pnl_pct'] = (trade['pnl'] / (trade['entry_price'] * trade.get('shares', 1))) * 100
        
        self.logger.info(f"Closed {trade['type']} trade: {exit_reason}, P&L: ${trade['pnl']:.2f}")
        
        return trade

    def calculate_performance(self, trades):
        """Calculate backtest performance metrics"""
        if not trades:
            return {"error": "No trades executed"}
        
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
            'profit_factor': abs(df_trades[df_trades['pnl'] > 0]['pnl'].sum() / 
                               df_trades[df_trades['pnl'] < 0]['pnl'].sum()) if df_trades[df_trades['pnl'] < 0]['pnl'].sum() != 0 else float('inf'),
            'avg_holding_time': (df_trades['exit_time'] - df_trades['entry_time']).mean().total_seconds() / 60
        }
        
        return metrics

    def run_all_backtests(self):
        """Run backtests for all enabled symbols"""
        results = {}
        
        for symbol in self.config['symbols']['enabled']:
            print(f"\n{'='*50}")
            print(f"BACKTESTING: {symbol}")
            print(f"{'='*50}")
            
            result = self.run_backtest(symbol)
            results[symbol] = result
            
            if result and 'error' not in result:
                print(f"Total Trades: {result['total_trades']}")
                print(f"Win Rate: {result['win_rate']:.2f}%")
                print(f"Total P&L: ${result['total_pnl']:.2f}")
                print(f"Average P&L: ${result['avg_pnl']:.2f}")
                print(f"Profit Factor: {result['profit_factor']:.2f}")
                print(f"Average Holding Time: {result['avg_holding_time']:.1f} minutes")
            else:
                print(f"No trades or error: {result}")
        
        return results