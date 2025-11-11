# vwap_ma_strategy/direct_comparison_fixed.py
import pandas as pd
import numpy as np
from utils.data_loader import DataLoader
from backtester.engine import VWAPMABacktester
import yaml

def direct_comparison_fixed():
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
    
    # Remove timezone from test times to match the data
    test_times = [
        '2025-11-06 14:49:00',  # SHORT signal
        '2025-11-06 15:12:00',  # SHORT signal
        '2025-11-07 14:46:00',  # SHORT signal  
        '2025-11-07 15:22:00',  # LONG signal
    ]
    
    print("DIRECT COMPARISON (Fixed Timezone)")
    print("=" * 60)
    
    for time_str in test_times:
        if time_str in df.index:
            idx = df.index.get_loc(time_str)
            current = df.iloc[idx]
            prev = df.iloc[idx-1]
            
            print(f"\nTime: {time_str}")
            print(f"Close: {current['close']:.2f}, VWAP: {current['vwap']:.2f}")
            print(f"MA Fast: {current['ma_fast']:.2f}, MA Slow: {current['ma_slow']:.2f}")
            print(f"Prev Close: {prev['close']:.2f}, Prev MA Fast: {prev['ma_fast']:.2f}")
            
            print(f"Trading Hours: {backtester.is_trading_hours(current.name)}")
            
            # Check all conditions individually
            ma_trend_short = current['ma_fast'] < current['ma_slow']
            vwap_position_short = current['close'] < current['vwap']
            candle_confirmation_short = current['close'] < current['ma_fast'] and prev['close'] >= prev['ma_fast']
            
            ma_trend_long = current['ma_fast'] > current['ma_slow']
            vwap_position_long = current['close'] > current['vwap']
            candle_confirmation_long = current['close'] > current['ma_fast'] and prev['close'] <= prev['ma_fast']
            
            print(f"SHORT - MA Trend: {ma_trend_short}, VWAP: {vwap_position_short}, Candle: {candle_confirmation_short}")
            print(f"LONG - MA Trend: {ma_trend_long}, VWAP: {vwap_position_long}, Candle: {candle_confirmation_long}")
            
            # Check pullback
            pullback_short = backtester.detect_pullback(df, idx, "short")
            pullback_long = backtester.detect_pullback(df, idx, "long")
            print(f"Pullback Short: {pullback_short}, Pullback Long: {pullback_long}")
            
            # Generate signal
            signal = backtester.generate_signal(df, idx, 'SPY')
            print(f"Final Signal: {signal}")

if __name__ == "__main__":
    direct_comparison_fixed()