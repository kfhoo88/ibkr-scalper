# vwap_ma_strategy/check_data_times.py
from utils.data_loader import DataLoader
import yaml

def check_data_times():
    with open('config/vwap_ma_config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    data_loader = DataLoader(config['backtest']['data_path'])
    df = data_loader.load_symbol_data('SPY')
    
    if df is None:
        print("Failed to load data")
        return
    
    print("First 10 timestamps in data:")
    for i in range(min(10, len(df))):
        print(f"  {df.index[i]}")
    
    print("\nLast 10 timestamps in data:")
    for i in range(max(0, len(df)-10), len(df)):
        print(f"  {df.index[i]}")
    
    print(f"\nData time range: {df.index[0]} to {df.index[-1]}")

if __name__ == "__main__":
    check_data_times()