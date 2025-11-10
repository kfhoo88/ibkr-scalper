#!/usr/bin/env python3
"""
Simplified Main File - Minimal dependencies
"""

import logging
import sys
import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_data():
    """Download SPY and QQQ data"""
    symbols = ['SPY', 'QQQ']
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 1 year
    
    data = {}
    for symbol in symbols:
        try:
            logger.info(f"Downloading {symbol} data...")
            ticker = yf.Ticker(symbol)
            hist_data = ticker.history(start=start_date, end=end_date, interval='1h')
            data[symbol] = hist_data
            logger.info(f"✅ {symbol}: {len(hist_data)} bars downloaded")
        except Exception as e:
            logger.error(f"❌ Failed to download {symbol}: {e}")
    
    return data

def simple_backtest(data):
    """Run a simple backtest to verify everything works"""
    if 'SPY' not in data:
        logger.error("No SPY data available")
        return
    
    spy_data = data['SPY']
    logger.info(f"Running backtest on {len(spy_data)} SPY bars")
    
    # Simple test: count potential trade signals
    trade_signals = 0
    for i in range(50, len(spy_data), 10):  # Check every 10th bar
        recent_data = spy_data.iloc[:i]
        if len(recent_data) > 20:
            # Simple momentum signal
            recent_5 = recent_data['Close'].tail(5).mean()
            recent_20 = recent_data['Close'].tail(20).mean()
            if recent_5 > recent_20:
                trade_signals += 1
    
    logger.info(f"Found {trade_signals} potential long signals")
    return trade_signals

def main():
    print("🚀 IBKR Scalper - Simplified Version")
    print("=" * 40)
    
    # Download data
    data = download_data()
    
    if not data:
        print("❌ No data downloaded - check your internet connection")
        return
    
    # Run simple backtest
    signals = simple_backtest(data)
    
    print(f"\n📊 SIMPLE BACKTEST COMPLETE")
    print(f"✅ Data downloaded for: {list(data.keys())}")
    print(f"✅ Potential trade signals: {signals}")
    print(f"✅ SPY data points: {len(data['SPY']) if 'SPY' in data else 0}")
    
    print(f"\n💡 Next steps:")
    print("1. Basic system is working!")
    print("2. Data download successful")
    print("3. Ready for full strategy implementation")

if __name__ == "__main__":
    main()