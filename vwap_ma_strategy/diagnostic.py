# vwap_ma_strategy/diagnostic.py
import pandas as pd
import numpy as np
from utils.data_loader import DataLoader
from utils.option_pricing import OptionPricer
import yaml
import os

def run_diagnostic():
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
    
    # Calculate basic indicators
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['tpv'] = df['typical_price'] * df['volume']
    df['date'] = df.index.date
    df['daily_tpv'] = df.groupby('date')['tpv'].cumsum()
    df['daily_volume'] = df.groupby('date')['volume'].cumsum()
    df['vwap'] = df['daily_tpv'] / df['daily_volume']
    df['ma_fast'] = df['close'].rolling(window=9).mean()
    df['ma_slow'] = df['close'].rolling(window=21).mean()
    
    # Check last 1000 candles for potential signals
    test_data = df.tail(1000).copy()
    
    signal_count = 0
    for i in range(1, len(test_data)):
        current = test_data.iloc[i]
        prev = test_data.iloc[i-1]
        
        # Skip if we don't have all indicators calculated
        if pd.isna(current['ma_fast']) or pd.isna(current['ma_slow']) or pd.isna(current['vwap']):
            continue
            
        # Check LONG conditions
        ma_trend_long = current['ma_fast'] > current['ma_slow']
        vwap_position_long = current['close'] > current['vwap']
        candle_confirmation_long = current['close'] > current['ma_fast'] and prev['close'] <= prev['ma_fast']
        
        # Check SHORT conditions  
        ma_trend_short = current['ma_fast'] < current['ma_slow']
        vwap_position_short = current['close'] < current['vwap']
        candle_confirmation_short = current['close'] < current['ma_fast'] and prev['close'] >= prev['ma_fast']
        
        if (ma_trend_long and vwap_position_long and candle_confirmation_long):
            print(f"LONG signal at {current.name}: MA9={current['ma_fast']:.2f}, MA21={current['ma_slow']:.2f}, Close={current['close']:.2f}, VWAP={current['vwap']:.2f}")
            signal_count += 1
        elif (ma_trend_short and vwap_position_short and candle_confirmation_short):
            print(f"SHORT signal at {current.name}: MA9={current['ma_fast']:.2f}, MA21={current['ma_slow']:.2f}, Close={current['close']:.2f}, VWAP={current['vwap']:.2f}")
            signal_count += 1
    
    print(f"\nTotal signals found in last 1000 candles: {signal_count}")
    
    if signal_count == 0:
        print("\nNo signals found. Let's check why...")
        print("Checking last 10 candles for condition breakdown:")
        
        sample = test_data.tail(10)
        for i, (idx, row) in enumerate(sample.iterrows()):
            if pd.isna(row['ma_fast']) or pd.isna(row['ma_slow']) or pd.isna(row['vwap']):
                continue
                
            print(f"\n{idx}:")
            print(f"  Close={row['close']:.2f}, MA9={row['ma_fast']:.2f}, MA21={row['ma_slow']:.2f}, VWAP={row['vwap']:.2f}")
            print(f"  MA9>MA21: {row['ma_fast'] > row['ma_slow']}, Close>VWAP: {row['close'] > row['vwap']}")
            
            # Check if this could be a signal with different confirmation
            if i > 0:
                prev_row = sample.iloc[i-1]
                current_confirmation = row['close'] > row['ma_fast'] and prev_row['close'] <= prev_row['ma_fast']
                alt_confirmation = row['close'] > row['ma_fast']  # Simpler confirmation
                print(f"  Standard confirmation: {current_confirmation}")
                print(f"  Alternative confirmation: {alt_confirmation}")

if __name__ == "__main__":
    run_diagnostic()