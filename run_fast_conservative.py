# run_fast_conservative.py
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
import time
from tqdm import tqdm

sys.path.append('core')

class ConservativeScalpingBacktester:
    def __init__(self):
        self.config = {
            'strategy': {
                'min_volume': 5000,        # Higher volume requirement
                'avoid_open_minutes': 45,  # Wait longer after open
                'avoid_close_minutes': 60, # Stop earlier before close
                'max_hold_minutes': 10,    # Shorter holds
                'max_daily_trades': 20,    # Much fewer trades
                'required_win_rate': 0.55  # Minimum historical win rate
            },
            'risk': {
                'stop_loss_pct': 0.08,     # Tighter stops (0.08%)
                'take_profit_pct': 0.12,   # Better risk/reward
                'max_position_value': 50,  # Smaller position size
                'max_drawdown': 0.10       # 10% max drawdown
            }
        }
    
    def calculate_vwap(self, data):
        """Calculate VWAP - often better than MAs for intraday"""
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        vwap = (typical_price * data['volume']).cumsum() / data['volume'].cumsum()
        return vwap
    
    def calculate_ema(self, data, period):
        """Calculate EMA"""
        return data['close'].ewm(span=period, adjust=False).mean()
    
    def calculate_support_resistance(self, data, lookback=20):
        """Simple support/resistance levels"""
        data['resistance'] = data['high'].rolling(window=lookback).max()
        data['support'] = data['low'].rolling(window=lookback).min()
        return data
    
    def precompute_conservative_indicators(self, data):
        """Precompute indicators for conservative strategy"""
        print("   🔧 Precomputing conservative indicators...")
        
        # Ensure proper datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index, utc=True)
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
        
        # Volume-weighted indicators
        data['vwap'] = self.calculate_vwap(data)
        data['ema_9'] = self.calculate_ema(data, 9)
        data['ema_21'] = self.calculate_ema(data, 21)
        
        # Support/Resistance
        data = self.calculate_support_resistance(data, 20)
        
        # Price position relative to VWAP
        data['above_vwap'] = data['close'] > data['vwap']
        data['vwap_distance_pct'] = abs(data['close'] - data['vwap']) / data['vwap'] * 100
        
        # EMA alignment
        data['emas_bullish'] = (data['ema_9'] > data['ema_21']) & (data['ema_21'] > data['vwap'])
        data['emas_bearish'] = (data['ema_9'] < data['ema_21']) & (data['ema_21'] < data['vwap'])
        
        # Support/Resistance tests
        data['near_resistance'] = (data['high'] >= data['resistance'] * 0.998)
        data['near_support'] = (data['low'] <= data['support'] * 1.002)
        
        # Momentum
        data['price_change_5m'] = data['close'].pct_change(5)
        data['volume_spike'] = data['volume'] > data['volume'].rolling(50).mean() * 1.5
        
        # HIGH-QUALITY SETUPS ONLY
        
        # Setup 1: VWAP Bounce with EMA alignment
        data['vwap_bounce_bullish'] = (
            data['near_support'] &
            data['above_vwap'] &
            data['emas_bullish'] &
            (data['vwap_distance_pct'] < 0.3) &  # Close to VWAP
            (data['price_change_5m'] < 0) &      # Recent pullback
            data['volume_spike']
        )
        
        data['vwap_bounce_bearish'] = (
            data['near_resistance'] &
            (~data['above_vwap']) &
            data['emas_bearish'] &
            (data['vwap_distance_pct'] < 0.3) &
            (data['price_change_5m'] > 0) &      # Recent rally
            data['volume_spike']
        )
        
        # Setup 2: Breakout with volume confirmation
        data['breakout_bullish'] = (
            (data['close'] > data['resistance']) &
            data['above_vwap'] &
            data['emas_bullish'] &
            (data['volume'] > data['volume'].rolling(20).mean() * 2)
        )
        
        data['breakout_bearish'] = (
            (data['close'] < data['support']) &
            (~data['above_vwap']) &
            data['emas_bearish'] &
            (data['volume'] > data['volume'].rolling(20).mean() * 2)
        )
        
        # Combine setups
        data['bullish_signal'] = data['vwap_bounce_bullish'] | data['breakout_bullish']
        data['bearish_signal'] = data['vwap_bounce_bearish'] | data['breakout_bearish']
        
        # Time filters - Much more restrictive
        data['hour'] = data.index.hour
        data['minute'] = data.index.minute
        data['is_trading_hours'] = (
            (data['hour'] > 10) | ((data['hour'] == 10) & (data['minute'] >= 0))
        ) & (
            (data['hour'] < 14) | ((data['hour'] == 14) & (data['minute'] <= 0))
        )  # Only trade 10:00 AM - 2:00 PM
        
        # Volume filter
        data['volume_ok'] = data['volume'] >= 5000
        
        # Avoid high volatility (gap moves)
        data['prev_close'] = data['close'].shift(390)  # Previous day close
        data['overnight_gap'] = abs(data['open'] - data['prev_close']) / data['prev_close'] * 100
        data['low_volatility'] = data['overnight_gap'] < 1.0  # Avoid gaps > 1%
        
        print(f"   ✅ Conservative signals:")
        print(f"      - Bullish signals: {data['bullish_signal'].sum():,}")
        print(f"      - Bearish signals: {data['bearish_signal'].sum():,}")
        print(f"      - Trading hours: {data['is_trading_hours'].sum():,}")
        print(f"      - VWAP bounces: {data['vwap_bounce_bullish'].sum():,} bull / {data['vwap_bounce_bearish'].sum():,} bear")
        print(f"      - Breakouts: {data['breakout_bullish'].sum():,} bull / {data['breakout_bearish'].sum():,} bear")
        
        return data
    
    def conservative_backtest(self, data, symbol="SPY"):
        """Conservative backtesting with high-quality setups only"""
        print(f"🚀 CONSERVATIVE BACKTEST: {symbol}")
        print("=" * 50)
        print("   Strategy: VWAP Bounces & Breakouts only")
        print("   Hours: 10:00 AM - 2:00 PM")
        print("   Max 20 trades/day, Tight stops")
        
        # Precompute indicators
        data = self.precompute_conservative_indicators(data)
        
        portfolio_value = 10000
        max_position_value = 50
        max_daily_trades = 20
        max_drawdown = 0.10
        trades = []
        daily_trades = {}
        consecutive_losses = 0
        
        # Find potential entry points - MUCH FEWER
        valid_entries = (
            (data.index >= data.index[50]) &
            data['is_trading_hours'] &
            data['volume_ok'] &
            data['low_volatility'] &
            (data['bullish_signal'] | data['bearish_signal'])
        )
        
        entry_indices = data[valid_entries].index
        total_entries = len(entry_indices)
        
        print(f"   📊 Found {total_entries:,} potential entry points")
        print(f"   ⚡ Only {max_daily_trades} trades allowed per day")
        
        if total_entries == 0:
            print("   ❌ No valid entries found with conservative filters")
            return {
                'total_trades': 0, 'winning_trades': 0, 'win_rate': 0,
                'total_pnl': 0, 'total_return': 0, 'final_capital': portfolio_value,
                'trades': []
            }
        
        # Process trades
        progress_bar = tqdm(total=total_entries, desc=f"Trading {symbol}")
        
        for entry_time in entry_indices:
            entry_idx = data.index.get_loc(entry_time)
            entry_data = data.iloc[entry_idx]
            trade_date = entry_data.name.date()
            
            # Conservative filters
            current_daily_trades = daily_trades.get(trade_date, 0)
            if (current_daily_trades >= max_daily_trades or 
                portfolio_value < max_position_value or
                portfolio_value < 10000 * (1 - max_drawdown)):
                progress_bar.update(1)
                continue
            
            # Determine direction
            if entry_data['bullish_signal']:
                direction = 'LONG'
                entry_price = entry_data['close']
                stop_price = entry_price * (1 - 0.0008)  # 0.08% stop
                target_price = entry_price * (1 + 0.0012) # 0.12% target
                setup_type = "VWAP Bounce" if entry_data['vwap_bounce_bullish'] else "Breakout"
            else:
                direction = 'SHORT'
                entry_price = entry_data['close']
                stop_price = entry_price * (1 + 0.0008)  # 0.08% stop
                target_price = entry_price * (1 - 0.0012) # 0.12% target
                setup_type = "VWAP Bounce" if entry_data['vwap_bounce_bearish'] else "Breakout"
            
            # Simulate trade
            position_open = True
            current_idx = entry_idx
            max_hold = 10  # minutes max
            
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
                    
                    trade_result = {
                        'entry_time': entry_time, 'exit_time': current_time,
                        'direction': direction, 'setup_type': setup_type,
                        'entry_price': entry_price, 'exit_price': exit_price,
                        'pnl': pnl, 'pnl_pct': pnl_pct * 100,
                        'portfolio_value': portfolio_value,
                        'stop_hit': hit_stop, 'target_hit': hit_target,
                        'time_exit': time_exit
                    }
                    
                    trades.append(trade_result)
                    
                    # Update counters
                    daily_trades[trade_date] = current_daily_trades + 1
                    if pnl < 0:
                        consecutive_losses += 1
                    else:
                        consecutive_losses = 0
                    
                    position_open = False
                    break
            
            progress_bar.update(1)
            
            # Update progress
            if trades:
                win_rate = len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100
                current_pnl = sum(t['pnl'] for t in trades)
            else:
                win_rate = 0
                current_pnl = 0
                
            progress_bar.set_postfix({
                'Trades': len(trades),
                'Equity': f"${portfolio_value:,.0f}",
                'Win %': f"{win_rate:.1f}%",
                'P&L': f"${current_pnl:,.0f}"
            })
            
            # Stop if too many consecutive losses or max drawdown
            if consecutive_losses >= 5 or portfolio_value < 10000 * (1 - max_drawdown):
                print(f"\n   🛑 STOPPED: {'Max drawdown' if portfolio_value < 9000 else '5 consecutive losses'}")
                break
        
        progress_bar.close()
        
        # Calculate results
        if trades:
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t['pnl'] > 0])
            win_rate = winning_trades / total_trades
            total_pnl = sum(t['pnl'] for t in trades)
            total_return = (portfolio_value - 10000) / 10000
            
            # Analyze by setup type
            vwap_trades = [t for t in trades if 'VWAP' in t['setup_type']]
            breakout_trades = [t for t in trades if 'Breakout' in t['setup_type']]
            
            vwap_win_rate = len([t for t in vwap_trades if t['pnl'] > 0]) / len(vwap_trades) if vwap_trades else 0
            breakout_win_rate = len([t for t in breakout_trades if t['pnl'] > 0]) / len(breakout_trades) if breakout_trades else 0
            
            print("\n" + "=" * 60)
            print("CONSERVATIVE RESULTS:")
            print("=" * 60)
            print(f"Total Trades: {total_trades:,}")
            print(f"Win Rate: {win_rate:.1%}")
            print(f"Total P&L: ${total_pnl:,.2f}")
            print(f"Total Return: {total_return:.2%}")
            print(f"Final Capital: ${portfolio_value:,.2f}")
            print(f"VWAP Bounce Win Rate: {vwap_win_rate:.1%} ({len(vwap_trades)} trades)")
            print(f"Breakout Win Rate: {breakout_win_rate:.1%} ({len(breakout_trades)} trades)")
            print(f"Max Daily Trades: {max(daily_trades.values()) if daily_trades else 0}")
            
            # Monthly analysis
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

def run_conservative_backtest():
    """Run conservative backtest"""
    print("🎯 CONSERVATIVE 1-YEAR BACKTEST")
    print("High-quality setups only: VWAP Bounces & Breakouts")
    print("Limited hours: 10:00 AM - 2:00 PM")
    print("Max 20 trades/day, Tight risk management")
    print("=" * 60)
    
    symbols = ['SPY']
    results = {}
    
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
        
        # Run conservative backtest
        backtester = ConservativeScalpingBacktester()
        start_time = time.time()
        
        try:
            result = backtester.conservative_backtest(data, symbol)
            duration = (time.time() - start_time) / 60
            
            print(f"\n   ✅ Conservative backtest completed in {duration:.1f} minutes")
            results[symbol] = result
            
        except Exception as e:
            print(f"   ❌ Error during backtest: {e}")
            import traceback
            traceback.print_exc()
        
        time.sleep(1)
    
    return results

if __name__ == "__main__":
    results = run_conservative_backtest()
    
    if results:
        print(f"\n🎉 CONSERVATIVE BACKTESTING COMPLETE!")
        for symbol, result in results.items():
            if result['total_trades'] > 0:
                print(f"   {symbol}: {result['total_trades']} trades, "
                      f"Win Rate: {result['win_rate']:.1%}, "
                      f"P&L: ${result['total_pnl']:,.2f}")