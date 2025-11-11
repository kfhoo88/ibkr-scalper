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
        #self.profit_target = self.config['exit_rules']['profit_target_pct']  # 0.15
        #self.stop_loss = self.config['exit_rules']['stop_loss_pct']          # 0.08
        #self.profit_target = self.config['exit_rules']['profit_target'] / 100
        #self.stop_loss = self.config['exit_rules']['stop_loss'] / 100
        self.hedge_trigger = self.config['exit_rules']['hedge_trigger'] / 100
        
    def setup_logging(self):
        """Setup logging configuration to file"""
        log_filename = f"backtest_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=getattr(logging, self.config['logging']['level']),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()  # Also print to console
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Logging to file: {log_filename}")
    
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
        """Generate breakout signals with dynamic support/resistance"""
        if current_index < 20:
            return None
            
        current = df.iloc[current_index]
        prev = df.iloc[current_index - 1]
        
        # === BREAKOUT LEVELS (5-period lookback) ===
        lookback = 5
        resistance = df['high'].rolling(lookback).max().iloc[current_index]  # lowercase 'high'
        support = df['low'].rolling(lookback).min().iloc[current_index]      # lowercase 'low'
        
        # === OUR EXISTING FILTERS ===
        volume_ok = current['volume'] > 0.8 * df['volume'].tail(20).mean()
        
        # Trend strength
        ma_uptrend = (current['ma_fast'] > current['ma_slow'] and 
                     current['ma_fast'] > prev['ma_fast'])
        ma_downtrend = (current['ma_fast'] < current['ma_slow'] and 
                       current['ma_fast'] < prev['ma_fast'])
        
        # Your candle color filters
        long_candle_ok = current['close'] > current['open']  # GREEN candle
        short_candle_ok = current['close'] < current['open']  # RED candle
        
        # MA distance limit
        ma_diff = abs(current['ma_fast'] - current['ma_slow'])
        ma_diff_ok = ma_diff <= 0.20
        
        # === BREAKOUT ENTRIES ===
        if (ma_uptrend and 
            current['high'] >= resistance and  # lowercase 'high'
            volume_ok and long_candle_ok and ma_diff_ok):
            
            signal = {'type': 'LONG', 'timestamp': current.name, 'price': current['close']}
            self.logger.info(f"🔰 BREAKOUT LONG: Price=${current['close']:.2f}, "
                            f"Resistance=${resistance:.2f}, MA_Diff=${ma_diff:.2f}")
            return signal
            
        elif (ma_downtrend and 
              current['low'] <= support and  # lowercase 'low'
              volume_ok and short_candle_ok and ma_diff_ok):
            
            signal = {'type': 'SHORT', 'timestamp': current.name, 'price': current['close']}
            self.logger.info(f"🔰 BREAKOUT SHORT: Price=${current['close']:.2f}, "
                            f"Support=${support:.2f}, MA_Diff=${ma_diff:.2f}")
            return signal
        
        return None

    def run_backtest(self, symbol):
        """Run complete backtest for symbol"""
        self.logger.info(f"Starting backtest for {symbol}")
        
        # Load and prepare data
        df = self.data_loader.load_symbol_data(symbol)
        if df is None:
            return {'trades': [], 'performance': {}}
            
        if not self.data_loader.validate_data(df, symbol):
            return {'trades': [], 'performance': {}}
            
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
        
        # Calculate performance metrics and return both
        performance = self.calculate_performance(trades)
        return {
            'trades': trades,
            'performance': performance
        }

    def check_exit_conditions(self, df, current_index, trade):
        """Check exit conditions with ATR-based TP and previous-candle SL"""
        current = df.iloc[current_index]
        prev_candle = df.iloc[current_index - 1]  # Previous candle
        current_atr = current['atr']
        
        # ATR-based Take Profit (1.5x ATR) + Previous Candle SL
        if trade['type'] == 'LONG':
            tp_price = trade['entry_price'] + (current_atr * 1.5)
            sl_price = prev_candle['low']  # Previous candle low as support
            
            # ENHANCED DEBUG: Show TP/SL levels and distances
            tp_distance = tp_price - trade['entry_price']
            sl_distance = trade['entry_price'] - sl_price
            risk_reward = tp_distance / sl_distance if sl_distance > 0 else 0
            
            self.logger.info(f"🎯 LONG CHECK: Entry=${trade['entry_price']:.2f}, "
                            f"Current=${current['close']:.2f}, ATR=${current_atr:.3f}, "
                            f"TP=${tp_price:.2f}(+{tp_distance:.2f}), "
                            f"SL=${sl_price:.2f}(-{sl_distance:.2f}), "
                            f"R:R={risk_reward:.2f}, "
                            f"High=${current['high']:.2f}, Low=${current['low']:.2f}")
            
            # Check exits
            if current['high'] >= tp_price:
                self.logger.info(f"✅ LONG HIT TP: Current High${current['high']:.2f} >= TP${tp_price:.2f}")
                return 'profit_target'
            if current['low'] <= sl_price:
                self.logger.info(f"❌ LONG HIT SL: Current Low${current['low']:.2f} <= SL${sl_price:.2f}")
                return 'stop_loss'
                
        else:  # SHORT
            tp_price = trade['entry_price'] - (current_atr * 1.5)
            sl_price = prev_candle['high']  # Previous candle high as resistance
            
            # ENHANCED DEBUG: Show TP/SL levels and distances
            tp_distance = trade['entry_price'] - tp_price
            sl_distance = sl_price - trade['entry_price']
            risk_reward = tp_distance / sl_distance if sl_distance > 0 else 0
            
            self.logger.info(f"🎯 SHORT CHECK: Entry=${trade['entry_price']:.2f}, "
                            f"Current=${current['close']:.2f}, ATR=${current_atr:.3f}, "
                            f"TP=${tp_price:.2f}(-{tp_distance:.2f}), "
                            f"SL=${sl_price:.2f}(+{sl_distance:.2f}), "
                            f"R:R={risk_reward:.2f}, "
                            f"High=${current['high']:.2f}, Low=${current['low']:.2f}")
            
            # Check exits
            if current['low'] <= tp_price:
                self.logger.info(f"✅ SHORT HIT TP: Current Low${current['low']:.2f} <= TP${tp_price:.2f}")
                return 'profit_target'
            if current['high'] >= sl_price:
                self.logger.info(f"❌ SHORT HIT SL: Current High${current['high']:.2f} >= SL${sl_price:.2f}")
                return 'stop_loss'
        
        # Time-based exit (10 minutes)
        hold_time = (current.name - trade['entry_time']).total_seconds() / 60
        if hold_time > 10:
            self.logger.info(f"⏰ TIME EXIT: Held {hold_time:.1f} minutes")
            return 'time_exit'
        
        # Market close exit
        #current_time = current.name.time()
        #exit_time = time.fromisoformat(self.config['trading_hours']['afternoon_end'])
        #if current_time >= exit_time:
        #    self.logger.info(f"🏁 MARKET CLOSE EXIT: {current_time}")
        #    return 'market_close'
        
        return None

    def close_trade(self, trade, exit_data, exit_reason, symbol):
        trade['exit_time'] = exit_data.name
        trade['exit_price'] = exit_data['close']
        trade['exit_reason'] = exit_reason
        
        # Calculate P&L
        shares = trade.get('shares', 100)
        if trade['type'] == 'LONG':
            trade['pnl'] = (trade['exit_price'] - trade['entry_price']) * shares
        else:
            trade['pnl'] = (trade['entry_price'] - trade['exit_price']) * shares
        
        # Apply commission
        trade['pnl'] -= self.config['backtest']['commission_per_trade']
        
        # ADD MISSING pnl_pct calculation
        trade['pnl_pct'] = (trade['pnl'] / (trade['entry_price'] * shares)) * 100
        
        # Calculate hold time in minutes
        hold_time = (trade['exit_time'] - trade['entry_time']).total_seconds() / 60
        trade['hold_minutes'] = hold_time
        
        # CLOSE DEBUG INFO
        candle_color = "GREEN" if exit_data['close'] > exit_data['open'] else "RED"
        self.logger.info(f"🔚 CLOSE {trade['type']}: {exit_reason}, "
                        f"Exit=${exit_data['close']:.2f}, Candle={candle_color}, "
                        f"P&L=${trade['pnl']:.2f}({trade['pnl_pct']:.2f}%), "
                        f"Held {hold_time:.1f}min")
        
        return trade

    def calculate_performance(self, trades):
        """Calculate performance metrics with options conversion"""
        # Handle empty or invalid trades
        if not trades or not isinstance(trades, list):
            print(f"DEBUG: Invalid trades data - type: {type(trades)}, value: {trades}")
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_pnl': 0,
                'max_win': 0,
                'max_loss': 0,
                'profit_factor': 0,
                'total_options_pnl': 0,
                'avg_options_pnl': 0,
                'options_win_rate': 0,
                'options_profit_factor': 0,
            }
        
        # Ensure all trades are dictionaries
        valid_trades = []
        for trade in trades:
            if isinstance(trade, dict) and 'pnl' in trade:
                valid_trades.append(trade)
            else:
                print(f"DEBUG: Invalid trade skipped: {trade}")
        
        if not valid_trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_pnl': 0,
                'max_win': 0,
                'max_loss': 0,
                'profit_factor': 0,
                'total_options_pnl': 0,
                'avg_options_pnl': 0,
                'options_win_rate': 0,
                'options_profit_factor': 0,
            }
        
        # Use valid_trades for calculations
        total_pnl = sum(trade['pnl'] for trade in valid_trades)
        winning_trades = [t for t in valid_trades if t['pnl'] > 0]
        win_rate = len(winning_trades) / len(valid_trades) * 100
        
        # Calculate profit factor
        gross_profit = sum(trade['pnl'] for trade in valid_trades if trade['pnl'] > 0)
        gross_loss = abs(sum(trade['pnl'] for trade in valid_trades if trade['pnl'] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Options conversion
        options_pnls = []
        for trade in valid_trades:
            options_result = self.convert_to_options_pnl(trade, trade.get('symbol', 'SPY'))
            options_pnls.append(options_result['options_pnl_dollar'])
            trade['options_pnl'] = options_result
        
        total_options_pnl = sum(options_pnls)
        
        # Calculate options profit factor
        options_gross_profit = sum(pnl for pnl in options_pnls if pnl > 0)
        options_gross_loss = abs(sum(pnl for pnl in options_pnls if pnl < 0))
        options_profit_factor = options_gross_profit / options_gross_loss if options_gross_loss > 0 else 0
        
        # Performance metrics
        return {
            'total_trades': len(valid_trades),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_pnl': total_pnl / len(valid_trades),
            'max_win': max((t['pnl'] for t in valid_trades), default=0),
            'max_loss': min((t['pnl'] for t in valid_trades), default=0),
            'profit_factor': profit_factor,
            'total_options_pnl': total_options_pnl,
            'avg_options_pnl': total_options_pnl / len(valid_trades),
            'options_win_rate': len([p for p in options_pnls if p > 0]) / len(options_pnls) * 100,
            'options_profit_factor': options_profit_factor,
        }

    def run_all_backtests(self):
        """Run backtests for all enabled symbols"""
        all_results = {}
        
        for symbol in self.config['symbols']['enabled']:
            print(f"\n{'='*50}")
            print(f"BACKTESTING: {symbol}")
            print(f"{'='*50}")
            
            raw_result = self.run_backtest(symbol)
            
            # Extract trades and performance
            trades_list = raw_result.get('trades', [])
            performance = raw_result.get('performance', {})
            
            print(f"DEBUG: Found {len(trades_list)} trades")
            
            # Add options conversion to the performance metrics
            if trades_list:
                options_pnls = []
                for trade in trades_list:
                    options_result = self.convert_to_options_pnl(trade, symbol)
                    options_pnls.append(options_result['options_pnl_dollar'])
                    trade['options_pnl'] = options_result
                
                total_options_pnl = sum(options_pnls)
                options_gross_profit = sum(pnl for pnl in options_pnls if pnl > 0)
                options_gross_loss = abs(sum(pnl for pnl in options_pnls if pnl < 0))
                options_profit_factor = options_gross_profit / options_gross_loss if options_gross_loss > 0 else 0
                
                performance['total_options_pnl'] = total_options_pnl
                performance['avg_options_pnl'] = total_options_pnl / len(trades_list)
                performance['options_win_rate'] = len([p for p in options_pnls if p > 0]) / len(options_pnls) * 100
                performance['options_profit_factor'] = options_profit_factor
            
            all_results[symbol] = performance
            
            # Print results
            print(f"\n--- SHARES PERFORMANCE ---")
            print(f"Total Trades: {performance.get('total_trades', 0)}")
            print(f"Win Rate: {performance.get('win_rate', 0):.2f}%")
            print(f"Total P&L: ${performance.get('total_pnl', 0):.2f}")
            print(f"Average P&L: ${performance.get('avg_pnl', 0):.2f}")
            print(f"Profit Factor: {performance.get('profit_factor', 0):.2f}")
            
            # Options results
            print(f"\n--- OPTIONS CONVERSION ---")
            print(f"Options Total P&L: ${performance.get('total_options_pnl', 0):.2f}")
            print(f"Options Avg P&L: ${performance.get('avg_options_pnl', 0):.2f}")
            print(f"Options Win Rate: {performance.get('options_win_rate', 0):.2f}%")
            print(f"Options Profit Factor: {performance.get('options_profit_factor', 0):.2f}")
            
            # Save trades for analysis
            self.trades.extend(trades_list)
        
        return all_results
                    
               
    def convert_to_options_pnl(self, share_trade, symbol):
        """Convert to realistic options trading with proper risk management"""
        OPTIONS_CONVERSION = {
            'SPY': {
                'delta_multiplier': 0.4,      # 0.4 delta target
                'leverage_multiplier': 25,    # Options move ~25x share percentage
                'theta_decay_per_minute': 0.002,  # Higher decay for 1 DTE
                'premium_per_contract': 200,  # $200 premium target
                'contracts_per_trade': 1,     # 1 contract per trade
                'commission_per_trade': 1.00  # Realistic commission
            },
            'QQQ': {
                'delta_multiplier': 0.4,
                'leverage_multiplier': 30,    # QQQ more volatile
                'theta_decay_per_minute': 0.0025,
                'premium_per_contract': 200,
                'contracts_per_trade': 1,
                'commission_per_trade': 1.00
            }
        }
        
        conversion = OPTIONS_CONVERSION.get(symbol, OPTIONS_CONVERSION['SPY'])
        
        # Calculate options P&L percentage
        share_pnl_pct = share_trade['pnl_pct']
        options_pnl_pct = share_pnl_pct * conversion['leverage_multiplier'] * conversion['delta_multiplier']
        
        # Apply theta decay based on hold time (more aggressive for 1 DTE)
        if 'hold_minutes' in share_trade:
            theta_loss = share_trade['hold_minutes'] * conversion['theta_decay_per_minute'] * 100
            options_pnl_pct -= theta_loss
        
        # Realistic premium and commission
        premium = conversion['premium_per_contract']
        contracts = conversion['contracts_per_trade']
        options_pnl_dollar = (options_pnl_pct / 100) * premium * contracts
        
        # Apply realistic options commission
        options_pnl_dollar -= conversion['commission_per_trade']
        
        return {
            'options_pnl_dollar': options_pnl_dollar,
            'options_pnl_pct': options_pnl_pct,
            'premium': premium,
            'contracts': contracts,
            'commission': conversion['commission_per_trade']
        }