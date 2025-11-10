# run_fast_enhanced.py
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
import time
from tqdm import tqdm

sys.path.append('core')

class EnhancedScalpingBacktester:
    def __init__(self):
        self.config = {
            'strategy': {
                'ma_fast_period': 8,
                'ma_slow_period': 21,
                'rsi_period': 14,
                'min_volume': 2000,
                'avoid_open_minutes': 30,
                'avoid_close_minutes': 45,
                'max_hold_minutes': 15,
                'atr_period': 14
            },
            'risk': {
                'stop_loss_pct': 0.15,  # Fixed % for now
                'take_profit_pct': 0.10,
                'max_position_value': 100,
                'max_daily_trades': 50
            }
        }
    
    def vectorized_heikin_ashi(self, data):
        """Vectorized Heikin Ashi calculation"""
        ha_close = (data['open'] + data['high'] + data['low'] + data['close']) / 4
        
        ha_open = np.zeros(len(data))
        ha_open[0] = (data['open'].iloc[0] + data['close'].iloc[0]) / 2
        for i in range(1, len(data)):
            ha_open[i] = (ha_open[i-1] + ha_close.iloc[i-1]) / 2
        
        ha_high = np.maximum.reduce([data['high'], ha_open, ha_close])
        ha_low = np.minimum.reduce([data['low'], ha_open, ha_close])
        
        return pd.DataFrame({
            'ha_open': ha_open,
            'ha_high': ha_high,
            'ha_low': ha_low, 
            'ha_close': ha_close
        }, index=data.index)
    
    def calculate_atr(self, data, period=14):
        """Calculate Average True Range - FIXED version"""
        # Convert to pandas Series for rolling operations
        high = pd.Series(data['high'])
        low = pd.Series(data['low'])
        close = pd.Series(data['close'])
        
        high_low = high - low
        high_close_prev = abs(high - close.shift(1))
        low_close_prev = abs(low - close.shift(1))
        
        true_range = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr
    
    def calculate_rsi(self, data, period=14):
        """Calculate RSI for momentum confirmation"""
        close = pd.Series(data['close'])
        delta = close.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def ensure_datetime_index(self, data):
        """Ensure proper datetime index"""
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index, utc=True)
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
        return data
    
    def precompute_enhanced_indicators(self, data):
        """Precompute all indicators with enhanced features - FIXED"""
        print("   🔧 Precomputing enhanced indicators...")
        
        # Ensure proper datetime index
        data = self.ensure_datetime_index(data)
        
        # Heikin Ashi
        ha_data = self.vectorized_heikin_ashi(data)
        
        # Enhanced Moving averages - using pandas Series
        data['ma_fast'] = data['close'].rolling(window=8).mean()
        data['ma_slow'] = data['close'].rolling(window=21).mean()
        data['ma_trend'] = data['close'].rolling(window=50).mean()
        
        # Heikin Ashi signals
        data['ha_trend'] = ha_data['ha_close'] > ha_data['ha_open']
        data['ha_strong_bull'] = (ha_data['ha_close'] > ha_data['ha_open']) & \
                                (ha_data['ha_close'] > ha_data['ha_high'].shift(1))
        data['ha_strong_bear'] = (ha_data['ha_close'] < ha_data['ha_open']) & \
                                (ha_data['ha_close'] < ha_data['ha_low'].shift(1))
        
        # Momentum indicators - FIXED: Ensure pandas Series
        data['rsi'] = self.calculate_rsi(data, 14)
        data['atr'] = self.calculate_atr(data, 14)
        data['price_vs_atr'] = data['atr'] / data['close'] * 100
        
        # Enhanced signal flags with simpler logic first
        data['bullish_signal'] = (data['ma_fast'] > data['ma_slow']) & \
                                (data['close'] > data['ma_trend']) & \
                                (data['rsi'] > 40) & (data['rsi'] < 80) & \
                                data['ha_strong_bull']
        
        data['bearish_signal'] = (data['ma_fast'] < data['ma_slow']) & \
                                (data['close'] < data['ma_trend']) & \
                                (data['rsi'] < 60) & (data['rsi'] > 20) & \
                                data['ha_strong_bear']
        
        # Time filters
        data['hour'] = data.index.hour
        data['minute'] = data.index.minute
        data['is_trading_hours'] = ~(
            ((data['hour'] == 9) & (data['minute'] < 30)) |
            ((data['hour'] == 15) & (data['minute'] >= 15))
        )
        
        # Volume filter
        data['volume_ok'] = data['volume'] >= 2000
        
        # Daily tracking
        data['trade_date'] = data.index.date
        
        print(f"   ✅ Indicators computed:")
        print(f"      - Bullish signals: {data['bullish_signal'].sum():,}")
        print(f"      - Bearish signals: {data['bearish_signal'].sum():,}")
        print(f"      - Trading hours: {data['is_trading_hours'].sum():,}")
        
        return data, ha_data
    
    def enhanced_backtest(self, data, symbol="SPY"):
        """Enhanced backtesting with better risk management"""
        print(f"🚀 ENHANCED BACKTEST: {symbol}")
        print("=" * 50)
        
        # Precompute enhanced indicators
        data, ha_data = self.precompute_enhanced_indicators(data)
        
        portfolio_value = 10000
        max_position_value = 100
        max_daily_trades = 50
        trades = []
        daily_trades = {}
        
        # Find all potential entry points
        valid_entries = (
            (data.index >= data.index[50]) &  # Enough data for indicators
            data['is_trading_hours'] &
            data['volume_ok'] &
            (data['bullish_signal'] | data['bearish_signal'])
        )
        
        entry_indices = data[valid_entries].index
        total_entries = len(entry_indices)
        
        print(f"   📊 Found {total_entries:,} potential entry points")
        print("   ⚡ Enhanced filters active")
        
        if total_entries == 0:
            print("   ❌ No valid entries found with current filters")
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_return': 0,
                'final_capital': portfolio_value,
                'trades': []
            }
        
        # Process trades
        progress_bar = tqdm(total=total_entries, desc=f"Trading {symbol}")
        
        for entry_time in entry_indices:
            entry_idx = data.index.get_loc(entry_time)
            entry_data = data.iloc[entry_idx]
            trade_date = entry_data['trade_date']
            
            # Skip if daily limit reached or insufficient capital
            current_daily_trades = daily_trades.get(trade_date, 0)
            if current_daily_trades >= max_daily_trades or portfolio_value < max_position_value:
                progress_bar.update(1)
                continue
            
            # Determine direction
            if entry_data['bullish_signal']:
                direction = 'LONG'
                entry_price = entry_data['close']
                stop_price = entry_price * (1 - 0.0015)  # 0.15% stop
                target_price = entry_price * (1 + 0.0010)  # 0.10% target
            else:
                direction = 'SHORT'
                entry_price = entry_data['close']
                stop_price = entry_price * (1 + 0.0015)  # 0.15% stop
                target_price = entry_price * (1 - 0.0010)  # 0.10% target
            
            # Simulate trade
            position_open = True
            current_idx = entry_idx
            max_hold = 15  # minutes
            
            while position_open and current_idx < min(entry_idx + max_hold, len(data) - 1):
                current_idx += 1
                current_data = data.iloc[current_idx]
                current_price = current_data['close']
                current_time = data.index[current_idx]
                
                # Check exit conditions
                if direction == 'LONG':
                    hit_target = current_price >= target_price
                    hit_stop = current_price <= stop_price
                else:
                    hit_target = current_price <= target_price
                    hit_stop = current_price >= stop_price
                
                time_exit = (current_idx >= entry_idx + max_hold)
                
                if hit_target or hit_stop or time_exit:
                    exit_price = current_price
                    
                    # Calculate P&L
                    if direction == 'LONG':
                        pnl_pct = (exit_price - entry_price) / entry_price
                    else:
                        pnl_pct = (entry_price - exit_price) / entry_price
                    
                    commission = 0.65
                    pnl = max_position_value * pnl_pct - commission
                    portfolio_value += pnl
                    
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': current_time,
                        'direction': direction,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct * 100,
                        'portfolio_value': portfolio_value,
                        'stop_hit': hit_stop,
                        'target_hit': hit_target,
                        'time_exit': time_exit
                    })
                    
                    # Update daily count
                    daily_trades[trade_date] = current_daily_trades + 1
                    position_open = False
                    
                    break
            
            progress_bar.update(1)
            
            # Update progress bar
            if trades:
                win_rate = len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100
            else:
                win_rate = 0
                
            progress_bar.set_postfix({
                'Trades': len(trades),
                'Equity': f"${portfolio_value:,.0f}",
                'Win %': f"{win_rate:.1f}%"
            })
            
            # Emergency stop
            if portfolio_value < 5000:
                print(f"\n   💥 STOPPED: 50% Drawdown reached")
                break
        
        progress_bar.close()
        
        # Calculate results
        if trades:
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t['pnl'] > 0])
            win_rate = winning_trades / total_trades
            total_pnl = sum(t['pnl'] for t in trades)
            total_return = (portfolio_value - 10000) / 10000
            
            # Advanced metrics
            stop_hits = len([t for t in trades if t['stop_hit']])
            target_hits = len([t for t in trades if t['target_hit']])
            time_exits = len([t for t in trades if t['time_exit']])
            
            winning_pnls = [t['pnl'] for t in trades if t['pnl'] > 0]
            losing_pnls = [t['pnl'] for t in trades if t['pnl'] < 0]
            
            avg_win = np.mean(winning_pnls) if winning_pnls else 0
            avg_loss = np.mean(losing_pnls) if losing_pnls else 0
            
            profit_factor = abs(sum(winning_pnls)) / abs(sum(losing_pnls)) if losing_pnls else float('inf')
            
            print("\n" + "=" * 60)
            print("ENHANCED RESULTS:")
            print("=" * 60)
            print(f"Total Trades: {total_trades:,}")
            print(f"Win Rate: {win_rate:.1%}")
            print(f"Profit Factor: {profit_factor:.2f}")
            print(f"Total P&L: ${total_pnl:,.2f}")
            print(f"Total Return: {total_return:.2%}")
            print(f"Final Capital: ${portfolio_value:,.2f}")
            print(f"Avg Win: ${avg_win:.2f} | Avg Loss: ${avg_loss:.2f}")
            print(f"Stops: {stop_hits} | Targets: {target_hits} | Time Exits: {time_exits}")
            print(f"Max Daily Trades: {max(daily_trades.values()) if daily_trades else 0}")
            
            # Monthly breakdown
            monthly_avg = total_pnl / 12
            print(f"Monthly Average: ${monthly_avg:,.2f}")
            print(f"$20k Target: {(monthly_avg/20000)*100:.1f}%")
            
        else:
            print("\n❌ No trades executed")
            total_trades = 0
            win_rate = 0
            total_pnl = 0
            total_return = 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades if trades else 0,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_return': total_return,
            'final_capital': portfolio_value,
            'trades': trades
        }

def run_enhanced_backtest():
    """Run enhanced backtest with better strategy"""
    print("🎯 ENHANCED 1-YEAR BACKTEST")
    print("Better risk management & strategy filters")
    print("=" * 60)
    
    symbols = ['SPY']  # Test SPY first
    
    results = {}  # Initialize results
    
    for symbol in symbols:
        print(f"\n{'='*60}")
        print(f"PROCESSING: {symbol}")
        print(f"{'='*60}")
        
        # Load data
        data_file = f"{symbol}_IBKR_1min_1year_20251110.csv"
        file_path = os.path.join('data/historical', data_file)
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {data_file}")
            continue
        
        print(f"📥 Loading: {data_file}")
        
        try:
            data = pd.read_csv(file_path)
            data['date'] = pd.to_datetime(data['date'], utc=True)
            data.set_index('date', inplace=True)
            data.index = data.index.tz_localize(None)
            
            print(f"   Loaded {len(data):,} bars")
            print(f"   Period: {data.index[0]} to {data.index[-1]}")
            
        except Exception as e:
            print(f"   ❌ Error loading data: {e}")
            continue
        
        # Run enhanced backtest
        backtester = EnhancedScalpingBacktester()
        start_time = time.time()
        
        try:
            result = backtester.enhanced_backtest(data, symbol)
            duration = (time.time() - start_time) / 60
            
            print(f"\n   ✅ Enhanced backtest completed in {duration:.1f} minutes")
            results[symbol] = result
            
        except Exception as e:
            print(f"   ❌ Error during enhanced backtest: {e}")
            import traceback
            traceback.print_exc()
        
        time.sleep(1)
    
    return results

if __name__ == "__main__":
    print("⚡ ENHANCED SCALPING STRATEGY")
    print("Better filters: RSI, ATR, Trend, Volume")
    print("Dynamic stops, Reduced position size, Daily limits")
    
    results = run_enhanced_backtest()
    
    if results:
        print(f"\n🎉 BACKTESTING COMPLETE!")
        for symbol, result in results.items():
            if result['total_trades'] > 0:
                print(f"   {symbol}: {result['total_trades']} trades, P&L: ${result['total_pnl']:,.2f}")