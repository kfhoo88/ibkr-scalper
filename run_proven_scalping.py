# run_proven_scalping.py
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime, time
import time as time_module
from tqdm import tqdm

sys.path.append('core')

class ProvenScalpingBacktester:
    def __init__(self):
        # Your proven configuration from PROJECT_CONTEXT.md
        self.config = {
            'ma_fast_period': 9,
            'ma_slow_period': 14,
            'min_volume': 1000,
            'stop_loss_pct': 0.30,    # 30% stop loss
            'take_profit_pct': 0.20,  # 20% profit target
            'max_hold_minutes': 20,
            'avoid_open_minutes': 15,
            'avoid_close_minutes': 30,
            'max_volatility': 2.0,
            'max_position_value': 200
        }
        
    def calculate_heikin_ashi(self, data):
        """Calculate Heikin Ashi candles"""
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
        }, index=data.index)
    
    def calculate_volatility(self, data, period=20):
        """Calculate volatility to filter high-vol periods"""
        returns = data['close'].pct_change()
        volatility = returns.rolling(window=period).std() * np.sqrt(252) * 100  # Annualized %
        return volatility
    
    def precompute_indicators(self, data):
        """Precompute all indicators using your proven settings"""
        print("   🔧 Precomputing proven indicators...")
        
        # Ensure proper datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index, utc=True)
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
        
        # Heikin Ashi
        ha_data = self.calculate_heikin_ashi(data)
        
        # Moving averages (your proven settings)
        data['ma_fast'] = ha_data['ha_close'].rolling(window=9).mean()
        data['ma_slow'] = ha_data['ha_close'].rolling(window=14).mean()
        
        # Signal flags (exactly as your proven config)
        data['is_bullish'] = (data['ma_fast'] > data['ma_slow']) & (ha_data['ha_close'] > ha_data['ha_open'])
        data['is_bearish'] = (data['ma_fast'] < data['ma_slow']) & (ha_data['ha_close'] < ha_data['ha_open'])
        
        # Volatility filter
        data['volatility'] = self.calculate_volatility(data)
        data['volatility_ok'] = data['volatility'] <= 2.0  # Your max_volatility setting
        
        # Time filters (your exact settings)
        data['hour'] = data.index.hour
        data['minute'] = data.index.minute
        data['is_trading_hours'] = ~(
            ((data['hour'] == 9) & (data['minute'] < 45)) |  # Avoid first 15 min (9:30-9:45)
            ((data['hour'] == 15) & (data['minute'] >= 30))   # Avoid last 30 min (15:30-16:00)
        )
        
        # Volume filter
        data['volume_ok'] = data['volume'] >= 1000
        
        print(f"   ✅ Signals: {data['is_bullish'].sum():,} bull / {data['is_bearish'].sum():,} bear")
        print(f"   ✅ Trading hours: {data['is_trading_hours'].sum():,} bars")
        print(f"   ✅ Volatility OK: {data['volatility_ok'].sum():,} bars")
        
        return data, ha_data
    
    def simulate_options_pnl(self, direction, entry_price, exit_price, contract_value=200):
        """
        Simulate options P&L based on price movement
        This approximates how options would behave with your strategy
        """
        if direction == 'LONG':
            price_change_pct = (exit_price - entry_price) / entry_price
            # Options provide leveraged returns - approximate 5x leverage for ATM options
            options_leverage = 5.0
            pnl_pct = price_change_pct * options_leverage
        else:  # SHORT
            price_change_pct = (entry_price - exit_price) / entry_price
            options_leverage = 5.0
            pnl_pct = price_change_pct * options_leverage
        
        # Apply your proven stop loss and take profit levels
        stop_loss = -0.30  # 30%
        take_profit = 0.20  # 20%
        pnl_pct = max(min(pnl_pct, take_profit), stop_loss)
        
        # Calculate final P&L
        pnl = contract_value * pnl_pct
        commission = 0.65  # IBKR commission
        net_pnl = pnl - commission
        
        return net_pnl, pnl_pct
    
    def proven_backtest(self, data, symbol="SPY"):
        """Backtest using your proven 62% win rate configuration"""
        print(f"🚀 PROVEN SCALPING BACKTEST: {symbol}")
        print("=" * 60)
        print("   Configuration: 9/14 MA Heikin Ashi, 30% stop, 20% target")
        print("   Max hold: 20 min, Avoid first 15min/last 30min")
        print("   $200 per trade, Options simulation with 5x leverage")
        
        # Precompute indicators
        data, ha_data = self.precompute_indicators(data)
        
        # Trading parameters
        portfolio_value = 10000
        max_position_value = 200
        trades = []
        trade_log = []
        
        # Find entry points using your proven filters
        valid_entries = (
            (data.index >= data.index[20]) &  # Enough data for indicators
            data['is_trading_hours'] &
            data['volume_ok'] &
            data['volatility_ok'] &
            (data['is_bullish'] | data['is_bearish'])
        )
        
        entry_indices = data[valid_entries].index
        total_entries = len(entry_indices)
        
        print(f"   📊 Found {total_entries:,} potential entry points")
        
        if total_entries == 0:
            print("   ❌ No valid entries found")
            return {
                'total_trades': 0, 'winning_trades': 0, 'win_rate': 0,
                'total_pnl': 0, 'total_return': 0, 'final_capital': portfolio_value,
                'trades': [], 'trade_log': []
            }
        
        # Process trades
        progress_bar = tqdm(total=total_entries, desc=f"Scalping {symbol}")
        
        for entry_time in entry_indices:
            entry_idx = data.index.get_loc(entry_time)
            entry_data = data.iloc[entry_idx]
            
            # Skip if insufficient capital
            if portfolio_value < max_position_value:
                progress_bar.update(1)
                continue
            
            # Determine direction
            if entry_data['is_bullish']:
                direction = 'LONG'
                entry_price = entry_data['close']
            else:
                direction = 'SHORT' 
                entry_price = entry_data['close']
            
            # Find exit (max 20 minutes or when stop/target hit)
            max_hold = 20
            exit_idx = entry_idx
            exit_reason = "MAX_HOLD"
            
            for offset in range(1, max_hold + 1):
                if entry_idx + offset >= len(data):
                    break
                    
                current_idx = entry_idx + offset
                current_data = data.iloc[current_idx]
                current_price = current_data['close']
                current_time = data.index[current_idx]
                
                # Calculate current P&L percentage
                if direction == 'LONG':
                    current_pnl_pct = (current_price - entry_price) / entry_price
                else:
                    current_pnl_pct = (entry_price - current_price) / entry_price
                
                # Apply options leverage approximation
                current_pnl_pct *= 5.0  # 5x leverage for options
                
                # Check if stop loss or take profit hit
                if current_pnl_pct <= -0.30:  # 30% stop loss
                    exit_idx = current_idx
                    exit_reason = "STOP_LOSS"
                    break
                elif current_pnl_pct >= 0.20:  # 20% take profit
                    exit_idx = current_idx
                    exit_reason = "TAKE_PROFIT"
                    break
                elif offset == max_hold:  # Max hold time reached
                    exit_idx = current_idx
                    exit_reason = "MAX_HOLD"
                    break
            
            # Get exit data
            exit_data = data.iloc[exit_idx]
            exit_price = exit_data['close']
            exit_time = data.index[exit_idx]
            
            # Calculate final P&L with options simulation
            pnl, pnl_pct = self.simulate_options_pnl(direction, entry_price, exit_price, max_position_value)
            portfolio_value += pnl
            
            # Record trade
            trade = {
                'entry_time': entry_time,
                'exit_time': exit_time,
                'direction': direction,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'portfolio_value': portfolio_value,
                'exit_reason': exit_reason,
                'hold_minutes': (exit_time - entry_time).total_seconds() / 60
            }
            
            trades.append(trade)
            
            # Update progress
            progress_bar.update(1)
            win_rate = len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100 if trades else 0
            progress_bar.set_postfix({
                'Trades': len(trades),
                'Equity': f"${portfolio_value:,.0f}",
                'Win %': f"{win_rate:.1f}%"
            })
        
        progress_bar.close()
        
        # Calculate results
        if trades:
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t['pnl'] > 0])
            win_rate = winning_trades / total_trades
            total_pnl = sum(t['pnl'] for t in trades)
            total_return = (portfolio_value - 10000) / 10000
            
            # Analyze exit reasons
            stops = len([t for t in trades if t['exit_reason'] == "STOP_LOSS"])
            targets = len([t for t in trades if t['exit_reason'] == "TAKE_PROFIT"])
            time_exits = len([t for t in trades if t['exit_reason'] == "MAX_HOLD"])
            
            # Calculate average hold time
            avg_hold = np.mean([t['hold_minutes'] for t in trades])
            
            print("\n" + "=" * 60)
            print("PROVEN SCALPING RESULTS:")
            print("=" * 60)
            print(f"Total Trades: {total_trades:,}")
            print(f"Win Rate: {win_rate:.1%}")
            print(f"Total P&L: ${total_pnl:,.2f}")
            print(f"Total Return: {total_return:.2%}")
            print(f"Final Capital: ${portfolio_value:,.2f}")
            print(f"Stops: {stops} | Targets: {targets} | Time Exits: {time_exits}")
            print(f"Average Hold Time: {avg_hold:.1f} minutes")
            
            # Monthly analysis for $20K target
            monthly_pnl = total_pnl / 12
            trades_per_month = total_trades / 12
            print(f"\n📈 MONTHLY ANALYSIS:")
            print(f"   Monthly P&L: ${monthly_pnl:,.2f}")
            print(f"   Monthly Trades: {trades_per_month:.0f}")
            print(f"   $20K Target: {(monthly_pnl/20000)*100:.1f}%")
            
            # Scaling analysis
            if monthly_pnl > 0:
                scale_factor = 20000 / monthly_pnl
                required_capital = 10000 * scale_factor
                print(f"   Required Capital for $20K/month: ${required_capital:,.0f}")
                print(f"   Position Size for $20K/month: ${max_position_value * scale_factor:,.0f}")
            
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

def run_proven_backtest():
    """Run backtest with proven 62% win rate configuration"""
    print("🎯 PROVEN SCALPING STRATEGY - $20K Monthly Target")
    print("Based on 62% win rate configuration from PROJECT_CONTEXT.md")
    print("=" * 70)
    
    symbols = ['SPY', 'QQQ']
    results = {}
    
    for symbol in symbols:
        print(f"\n{'='*70}")
        print(f"PROCESSING: {symbol}")
        print(f"{'='*70}")
        
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
        
        # Run proven backtest
        backtester = ProvenScalpingBacktester()
        start_time = time_module.time()
        
        try:
            result = backtester.proven_backtest(data, symbol)
            duration = (time_module.time() - start_time) / 60
            
            print(f"\n   ✅ Proven backtest completed in {duration:.1f} minutes")
            results[symbol] = result
            
        except Exception as e:
            print(f"   ❌ Error during backtest: {e}")
            import traceback
            traceback.print_exc()
        
        time_module.sleep(1)
    
    # Summary
    if results:
        print(f"\n{'='*70}")
        print("🎉 PROVEN SCALPING BACKTEST COMPLETE!")
        print(f"{'='*70}")
        
        total_pnl = sum(r['total_pnl'] for r in results.values())
        total_trades = sum(r['total_trades'] for r in results.values())
        avg_win_rate = np.mean([r['win_rate'] for r in results.values()])
        
        print(f"📊 COMBINED RESULTS:")
        print(f"   Total Trades: {total_trades:,}")
        print(f"   Average Win Rate: {avg_win_rate:.1%}")
        print(f"   Total P&L: ${total_pnl:,.2f}")
        
        monthly_avg = total_pnl / 12
        print(f"   Monthly Average: ${monthly_avg:,.2f}")
        print(f"   $20k Target Achievement: {(monthly_avg/20000)*100:.1f}%")
        
        if monthly_avg > 0:
            scale_factor = 20000 / monthly_avg
            print(f"   Scaling Required: {scale_factor:.1f}x current size")
            print(f"   Target Position Size: ${200 * scale_factor:,.0f}")
    
    return results

if __name__ == "__main__":
    results = run_proven_backtest()