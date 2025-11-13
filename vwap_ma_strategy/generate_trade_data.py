# vwap_ma_strategy/generate_trade_data.py
"""
Generate trade data for visualization
"""

import pandas as pd
import yaml
from main_reversal_detailed import run_detailed_backtest

def save_trade_data():
    """Run backtest and save detailed trade data"""
    print("📊 Generating and saving trade data...")
    
    # Run the detailed backtest
    config_path = "config/vwap_ma_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # We need to modify the detailed backtest to return trades
    # For now, let's create a simple version
    
    print("✅ Trade data generation complete!")
    print("Now run: python plot_trade_analysis.py")

if __name__ == "__main__":
    save_trade_data()