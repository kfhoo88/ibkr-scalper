# core/options_scalper_fixed.py
import pandas as pd
import numpy as np
from datetime import timedelta
import logging

class OptionsScalpingBacktester:
    def __init__(self, config):
        self.config = config
        self.strategy_config = config['strategy']
        self.risk_config = config['risk'] 
        self.trading_config = config['trading']
        self.backtest_config = config['backtesting']
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def ensure_datetime_index(self, data):
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index, utc=True)
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
        return data
        
    def calculate_heikin_ashi(self, data):
        ha_close = (data['open'] + data['high'] + data['low'] + data['close']) / 4
        ha_open = np.zeros(len(data))
        ha_open[0] = (data['open'].iloc[0] + data['close'].iloc[0]) / 2
        for i in range(1, len(data)):
            ha_open[i] = (ha_open[i-1] + ha_close.iloc[i-1]) / 2
        ha_high = np.maximum.reduce([data['high'], ha_open, ha_close])
        ha_low = np.minimum.reduce([data['low'], ha_open, ha_close])
        return pd.DataFrame({
            'ha_open': ha_open, 'ha_high': ha_high,
            'ha_low': ha_low, 'ha_close': ha_close
        })
    
    def simulate_options_move(self, underlying_move_pct, option_type="call"):
        """
        AGGRESSIVE options pricing for 1-5 minute scalping
        For ATM options with 0-1 DTE in quick scalps:
        - Small moves can generate 10-30% options moves
        - Medium moves can generate 30-60% options moves  
        - Large moves can generate 60-100%+ options moves
        """
        abs_move = abs(underlying_move_pct)
        
        # MUCH HIGHER leverage for quick scalping
        if abs_move < 0.001:  # < 0.1%
            leverage = 30.0   # Was 3.0
        elif abs_move < 0.005:  # 0.1-0.5%
            leverage = 50.0   # Was 6.0
        elif abs_move < 0.01:   # 0.5-1.0%
            leverage = 70.0    # Was 10.0
        else:                   # > 1.0%
            leverage = 90.0    # Was 15.0
        
        # Options are more volatile
        volatility_factor = 1.5  # Slightly higher
        
        # Direction matters for options
        if option_type == "call":
            options_move_pct = underlying_move_pct * leverage * volatility_factor
        else:  # put
            options_move_pct = -underlying_move_pct * leverage * volatility_factor
        
        return options_move_pct

    def calculate_ha_wick_strength(self, ha_data):
        """Calculate Heikin Ashi wick strength - little/no lower wick for bullish"""
        body_size = abs(ha_data['ha_close'] - ha_data['ha_open'])
        lower_wick = ha_data['ha_open'] - ha_data['ha_low']  # For bullish, open is usually > low
        
        # Fix: Handle division for pandas Series properly
        wick_ratio = lower_wick / body_size
        wick_ratio = wick_ratio.where(body_size > 0, 0)  # Set to 0 where body_size is 0
        
        return wick_ratio

    def enhanced_signals(self, data, ha_data):
        """Your exact live trading rules"""
        # Calculate wick strength
        wick_strength = self.calculate_ha_wick_strength(ha_data)
        
        # Your exact rules:
        data['is_bullish'] = (
            (ha_data['ha_close'] > ha_data['ha_open']) &           # Green HA candle
            (wick_strength < 0.3) &                                # Little/no lower wick (<30% of body)
            (data['ma_fast'] > data['ma_slow']) &                  # MA9 above MA14
            (data['close'] > data['ma_fast'])                      # Regular candle close above MA9
        )
        
        data['is_bearish'] = (
            (ha_data['ha_close'] < ha_data['ha_open']) &           # Red HA candle  
            (wick_strength < 0.3) &                                # Little/no upper wick
            (data['ma_fast'] < data['ma_slow']) &                  # MA9 below MA14
            (data['close'] < data['ma_fast'])                      # Regular candle close below MA9
        )
        
        return data
        
    def precompute_indicators(self, data):
        """Precompute indicators for options trading"""
        self.logger.info("Precomputing indicators for OPTIONS trading...")
        
        data = self.ensure_datetime_index(data)
        ha_data = self.calculate_heikin_ashi(data)  # This must come FIRST
        
        # Create MA columns FIRST
        data['ma_fast'] = ha_data['ha_close'].rolling(window=9).mean()
        data['ma_slow'] = ha_data['ha_close'].rolling(window=14).mean()
        
        # THEN use them in enhanced_signals
        data = self.enhanced_signals(data, ha_data)  # Now ma_fast/ma_slow exist
        
        # Time filters
        data['hour'] = data.index.hour
        data['minute'] = data.index.minute
        data['is_trading_hours'] = ~(
            ((data['hour'] == 9) & (data['minute'] < 45)) |
            ((data['hour'] == 15) & (data['minute'] >= 30))
        )
        
        data['volume_ok'] = data['volume'] >= 1000
        
        self.logger.info(f"Bullish signals: {data['is_bullish'].sum()}")
        self.logger.info(f"Bearish signals: {data['is_bearish'].sum()}")
        
        return data, ha_data
        
    def execute_options_trade(self, entry_data, entry_time, data, capital, position_size):
        """Execute OPTIONS trade with DEBUGGING"""
        direction = 'LONG' if entry_data['is_bullish'] else 'SHORT'
        underlying_entry_price = entry_data['close']
        
        # OPTIONS PARAMETERS 
        stop_loss_pct = 0.30  # 30% stop loss on OPTIONS PREMIUM
        take_profit_pct = 0.20  # 20% take profit on OPTIONS PREMIUM
        
        option_type = "call" if direction == 'LONG' else "put"
        
        max_hold_minutes = 5
        max_exit_time = entry_time + timedelta(minutes=max_hold_minutes)
        
        # Get future data
        future_mask = (data.index > entry_time) & (data.index <= max_exit_time)
        future_data = data[future_mask]
        
        exit_reason = "MAX_HOLD"
        exit_time = max_exit_time
        final_options_pnl_pct = 0
        max_options_move = 0
        min_options_move = 0
        
        # Track options moves throughout the hold period
        options_moves = []
        
        for idx, bar in future_data.iterrows():
            current_underlying_price = bar['close']
            
            # Calculate underlying price move
            if direction == 'LONG':
                underlying_move_pct = (current_underlying_price - underlying_entry_price) / underlying_entry_price
            else:
                underlying_move_pct = (underlying_entry_price - current_underlying_price) / underlying_entry_price
            
            # Convert to options premium move
            options_move_pct = self.simulate_options_move(underlying_move_pct, option_type)
            options_moves.append(options_move_pct)
            
            # Update min/max for debugging
            max_options_move = max(max_options_move, options_move_pct)
            min_options_move = min(min_options_move, options_move_pct)
            
            # DEBUG: Check if we should hit stop/target
            if options_move_pct <= -stop_loss_pct and exit_reason == "MAX_HOLD":
                self.logger.debug(f"STOP HIT: {options_move_pct:.1%} <= {-stop_loss_pct:.1%}")
                exit_reason = "STOP_LOSS"
                final_options_pnl_pct = -stop_loss_pct
                exit_time = idx
                break
            elif options_move_pct >= take_profit_pct and exit_reason == "MAX_HOLD":
                self.logger.debug(f"TARGET HIT: {options_move_pct:.1%} >= {take_profit_pct:.1%}")
                exit_reason = "TAKE_PROFIT" 
                final_options_pnl_pct = take_profit_pct
                exit_time = idx
                break
        
        # Time-based exit (use final move)
        if exit_reason == "MAX_HOLD":
            if options_moves:
                final_options_pnl_pct = options_moves[-1]
                # Still apply stops/targets for final move
                if final_options_pnl_pct <= -stop_loss_pct:
                    final_options_pnl_pct = -stop_loss_pct
                    exit_reason = "STOP_LOSS"
                elif final_options_pnl_pct >= take_profit_pct:
                    final_options_pnl_pct = take_profit_pct
                    exit_reason = "TAKE_PROFIT"
            else:
                final_options_pnl_pct = 0
        
        # Calculate P&L
        commission = 0.65
        pnl = position_size * final_options_pnl_pct - commission
        capital += pnl
        
        # Calculate actual hold time
        hold_minutes = (exit_time - entry_time).total_seconds() / 60
        
        trade_result = {
            'symbol': 'SPY',
            'entry_time': entry_time,
            'exit_time': exit_time,
            'direction': direction,
            'underlying_entry': underlying_entry_price,
            'options_pnl_pct': final_options_pnl_pct * 100,
            'pnl': pnl,
            'exit_reason': exit_reason,
            'hold_minutes': hold_minutes,
            'max_move': max_options_move * 100,
            'min_move': min_options_move * 100
        }
        
        return trade_result, capital

    
    def backtest(self, data, symbol):
        """Backtest with PROPER options simulation"""
        self.logger.info(f"🚀 Starting OPTIONS backtest for {symbol}")
        self.logger.info("💰 Using 30% stops / 20% targets on OPTIONS PREMIUM")
        self.logger.info("⚡ Dynamic leverage: 3-15x based on move size")
        
        data, ha_data = self.precompute_indicators(data)
        
        capital = 10000
        position_size = 200
        trades = []
        
        valid_entries = (
            data['is_trading_hours'] & 
            data['volume_ok'] & 
            (data['is_bullish'] | data['is_bearish'])
        )
        
        entry_indices = data[valid_entries].index
        self.logger.info(f"📊 Found {len(entry_indices)} potential entries")
        
        # Process trades
        for i, entry_time in enumerate(entry_indices):
            if capital < position_size:
                self.logger.info("💸 Insufficient capital - stopping")
                break
                
            if i % 1000 == 0 and i > 0:
                self.logger.info(f"⏳ Processed {i}/{len(entry_indices)} entries")
                # Show detailed sample
                recent_trades = trades[-3:] if len(trades) >= 3 else trades
                for t in recent_trades:
                    self.logger.info(f"   {t['exit_reason']}: {t['options_pnl_pct']:+.1f}% (Range: {t['min_move']:.1f}% to {t['max_move']:.1f}%)")
            
            entry_data = data.loc[entry_time]
            trade_result, capital = self.execute_options_trade(
                entry_data, entry_time, data, capital, position_size
            )
            
            trade_result['symbol'] = symbol
            trades.append(trade_result)
        
        # Calculate results
        if trades:
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t['pnl'] > 0])
            win_rate = winning_trades / total_trades
            total_pnl = sum(t['pnl'] for t in trades)
            
            stops = len([t for t in trades if t['exit_reason'] == "STOP_LOSS"])
            targets = len([t for t in trades if t['exit_reason'] == "TAKE_PROFIT"])
            time_exits = len([t for t in trades if t['exit_reason'] == "MAX_HOLD"])
            
            # Calculate averages
            avg_hold = np.mean([t['hold_minutes'] for t in trades])
            avg_options_pnl = np.mean([t['options_pnl_pct'] for t in trades])
            winning_trades_list = [t for t in trades if t['options_pnl_pct'] > 0]
            losing_trades_list = [t for t in trades if t['options_pnl_pct'] < 0]
            avg_win_pct = np.mean([t['options_pnl_pct'] for t in winning_trades_list]) if winning_trades_list else 0
            avg_loss_pct = np.mean([t['options_pnl_pct'] for t in losing_trades_list]) if losing_trades_list else 0
            
            self.logger.info(f"🎯 OPTIONS RESULTS: {total_trades} trades, {win_rate:.1%} win rate")
            self.logger.info(f"📊 Exits - Stops: {stops}, Targets: {targets}, Time: {time_exits}")
            self.logger.info(f"💰 Options P&L: ${total_pnl:.2f}")
            self.logger.info(f"📈 Avg Options Return: {avg_options_pnl:.1f}%")
            self.logger.info(f"🎯 Avg Win: {avg_win_pct:.1f}%, Avg Loss: {avg_loss_pct:.1f}%")
            self.logger.info(f"⏱️  Avg Hold Time: {avg_hold:.1f} minutes")
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'final_capital': capital,
                'stops': stops,
                'targets': targets, 
                'time_exits': time_exits,
                'avg_hold_minutes': avg_hold,  # FIXED: Added this key
                'avg_options_pnl_pct': avg_options_pnl,
                'avg_win_pct': avg_win_pct,
                'avg_loss_pct': avg_loss_pct,
                'trades': trades
            }
        else:
            return {
                'total_trades': 0, 'winning_trades': 0, 'win_rate': 0,
                'total_pnl': 0, 'final_capital': capital,
                'stops': 0, 'targets': 0, 'time_exits': 0,
                'avg_hold_minutes': 0,  # FIXED: Added this key
                'avg_options_pnl_pct': 0, 'avg_win_pct': 0, 'avg_loss_pct': 0,
                'trades': []
            }