# vwap_ma_strategy/debug_signal_generation.py
import pandas as pd
import numpy as np
from utils.data_loader import DataLoader
from backtester.engine import VWAPMABacktester
import yaml

def debug_signal_generation():
    # Load data
    with open('config/vwap_ma_config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    data_loader = DataLoader(config['backtest']['data_path'])
    df = data_loader.load_symbol_data('SPY')
    
    if df is None:
        print("Failed to load data")
        return
    
    # Initialize backtester and calculate indicators
    backtester = VWAPMABacktester()
    df = backtester.calculate_indicators(df)
    
    test_times = [
        '2025-11-06 14:49:00',  # SHORT signal
    ]
    
    print("DEBUG SIGNAL GENERATION")
    print("=" * 60)
    
    for time_str in test_times:
        if time_str in df.index:
            idx = df.index.get_loc(time_str)
            current = df.iloc[idx]
            
            print(f"\nTime: {time_str}")
            
            # Check market filters
            atr_ok = current['atr_percentage'] >= config['market_filters']['min_atr_percentage']
            volume_ok = current['volume_ratio'] >= config['market_filters']['min_volume_ratio']
            trading_hours_ok = backtester.is_trading_hours(current.name)
            
            print(f"Market Filters:")
            print(f"  ATR %: {current['atr_percentage']:.4f} (min: {config['market_filters']['min_atr_percentage']}) - {'PASS' if atr_ok else 'FAIL'}")
            print(f"  Volume Ratio: {current['volume_ratio']:.2f} (min: {config['market_filters']['min_volume_ratio']}) - {'PASS' if volume_ok else 'FAIL'}")
            print(f"  Trading Hours: {trading_hours_ok} - {'PASS' if trading_hours_ok else 'FAIL'}")
            
            if not (atr_ok and volume_ok and trading_hours_ok):
                print("BLOCKED by market filters!")
                return
            
            # Now check strategy conditions
            signal = backtester.generate_signal(df, idx, 'SPY')
            print(f"Final Signal: {signal}")
            
            # Let's manually call the internal logic
            prev = df.iloc[idx-1]
            
            # SHORT conditions
            ma_trend_short = current['ma_fast'] < current['ma_slow']
            vwap_position_short = current['close'] < current['vwap']
            candle_confirmation_short = current['close'] < current['ma_fast'] and prev['close'] >= prev['ma_fast']
            pullback_short = backtester.detect_pullback(df, idx, "short")
            
            print(f"Strategy Conditions (SHORT):")
            print(f"  MA Trend: {ma_trend_short}")
            print(f"  VWAP Position: {vwap_position_short}")
            print(f"  Candle Confirmation: {candle_confirmation_short}")
            print(f"  Pullback: {pullback_short}")
            print(f"  ALL CONDITIONS: {ma_trend_short and vwap_position_short and candle_confirmation_short and pullback_short}")

if __name__ == "__main__":
    debug_signal_generation()