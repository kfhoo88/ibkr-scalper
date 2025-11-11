# vwap_ma_strategy/test_filters.py
from backtester.engine import VWAPMABacktester

def test_filters():
    backtester = VWAPMABacktester()
    df = backtester.data_loader.load_symbol_data('SPY')
    
    if df is None:
        print("Failed to load data")
        return
        
    df = backtester.calculate_indicators(df)
    
    # Test a known signal time
    test_time = '2025-11-06 14:49:00'
    if test_time in df.index:
        idx = df.index.get_loc(test_time)
        print(f"Testing signal at: {test_time}")
        
        # Check all conditions
        current = df.iloc[idx]
        prev = df.iloc[idx-1]
        
        print(f"MA Fast: {current['ma_fast']:.2f}, MA Slow: {current['ma_slow']:.2f}")
        print(f"Close: {current['close']:.2f}, VWAP: {current['vwap']:.2f}")
        print(f"MA Trend (Fast>Slow): {current['ma_fast'] > current['ma_slow']}")
        print(f"VWAP Position (Close<VWAP): {current['close'] < current['vwap']}")
        print(f"Candle Confirmation: {current['close'] < current['ma_fast'] and prev['close'] >= prev['ma_fast']}")
        print(f"Volume Ratio: {current['volume_ratio']:.2f}")
        print(f"ATR %: {current['atr_percentage']:.4f}")
        print(f"Trading Hours: {backtester.is_trading_hours(current.name)}")
        
        # Generate signal
        signal = backtester.generate_signal(df, idx, 'SPY')
        print(f"Signal generated: {signal}")

if __name__ == "__main__":
    test_filters()