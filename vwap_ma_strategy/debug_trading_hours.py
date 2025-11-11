# vwap_ma_strategy/debug_trading_hours.py
import pandas as pd
import numpy as np
from utils.data_loader import DataLoader
import yaml
import os
from datetime import time

def debug_trading_hours():
    # Load config
    with open('config/vwap_ma_config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    data_loader = DataLoader(config['backtest']['data_path'])
    df = data_loader.load_symbol_data('SPY')
    
    if df is None:
        print("Failed to load data")
        return
    
    # Fix datetime index
    if hasattr(df.index, 'tz') and df.index.tz is not None:
        df.index = df.index.tz_convert(None)
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, utc=True).tz_convert(None)
    
    # Check trading hours for some sample signals from diagnostic
    test_times = [
        '2025-11-06 14:49:00',  # SHORT signal from diagnostic
        '2025-11-06 15:12:00',  # SHORT signal from diagnostic  
        '2025-11-07 14:46:00',  # SHORT signal from diagnostic
        '2025-11-07 15:22:00',  # LONG signal from diagnostic
    ]
    
    print("Trading Hours Configuration:")
    print(f"Morning: {config['trading_hours']['morning_start']} to {config['trading_hours']['morning_end']}")
    print(f"Afternoon: {config['trading_hours']['afternoon_start']} to {config['trading_hours']['afternoon_end']}")
    print()
    
    for time_str in test_times:
        if time_str in df.index:
            timestamp = df.index[df.index == time_str][0]
            current_time = timestamp.time()
            
            morning_start = time.fromisoformat(config['trading_hours']['morning_start'])
            morning_end = time.fromisoformat(config['trading_hours']['morning_end'])
            afternoon_start = time.fromisoformat(config['trading_hours']['afternoon_start'])
            afternoon_end = time.fromisoformat(config['trading_hours']['afternoon_end'])
            
            in_morning = morning_start <= current_time <= morning_end
            in_afternoon = afternoon_start <= current_time <= afternoon_end
            in_trading_hours = in_morning or in_afternoon
            
            print(f"Time: {timestamp}")
            print(f"  Local time: {current_time}")
            print(f"  In morning session: {in_morning} ({morning_start} to {morning_end})")
            print(f"  In afternoon session: {in_afternoon} ({afternoon_start} to {afternoon_end})")
            print(f"  In trading hours: {in_trading_hours}")
            print()

if __name__ == "__main__":
    debug_trading_hours()