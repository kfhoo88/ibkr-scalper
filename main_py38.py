#!/usr/bin/env python3
"""
IBKR Scalper - Python 3.8 Compatible Version
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check and import dependencies with Python 3.8 compatibility"""
    try:
        import pandas as pd
        logger.info(f"✅ pandas {pd.__version__}")
    except ImportError as e:
        logger.error(f"❌ pandas import failed: {e}")
        return False
        
    try:
        import yfinance as yf
        logger.info("✅ yfinance")
    except ImportError as e:
        logger.error(f"❌ yfinance import failed: {e}")
        return False
        
    try:
        import numpy as np
        logger.info(f"✅ numpy {np.__version__}")
    except ImportError as e:
        logger.error(f"❌ numpy import failed: {e}")
        return False
        
    return True

def download_market_data():
    """Download SPY and QQQ data"""
    symbols = ['SPY', 'QQQ']
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # 6 months for testing
    
    data = {}
    for symbol in symbols:
        try:
            logger.info(f"📥 Downloading {symbol} data...")
            ticker = yf.Ticker(symbol)
            # Use period instead of start/end for better compatibility
            hist_data = ticker.history(period="6mo", interval="1h")
            
            if hist_data.empty:
                logger.warning(f"⚠️ No data returned for {symbol}")
                continue
                
            data[symbol] = hist_data
            logger.info(f"✅ {symbol}: {len(hist_data)} bars, {hist_data.index[0]} to {hist_data.index[-1]}")
            
        except Exception as e:
            logger.error(f"❌ Failed to download {symbol}: {e}")
    
    return data

def simple_strategy_test(data):
    """Test a simple moving average strategy"""
    if 'SPY' not in data:
        logger.error("No SPY data available for testing")
        return None
        
    spy_data = data['SPY']
    logger.info(f"Testing strategy on {len(spy_data)} SPY bars")
    
    # Simple moving average crossover strategy
    signals = []
    for i in range(20, len(spy_data)):
        window = spy_data.iloc[i-20:i]
        short_ma = window['Close'].tail(5).mean()
        long_ma = window['Close'].mean()
        
        if short_ma > long_ma:
            signals.append('BUY')
        else:
            signals.append('SELL')
    
    # Count signals
    buy_signals = signals.count('BUY')
    sell_signals = signals.count('SELL')
    
    logger.info(f"Strategy signals: {buy_signals} BUY, {sell_signals} SELL")
    
    return {
        'total_signals': len(signals),
        'buy_signals': buy_signals,
        'sell_signals': sell_signals,
        'buy_ratio': buy_signals / len(signals) if signals else 0
    }

def main():
    print("🚀 IBKR Scalper - Python 3.8 Edition")
    print("=" * 45)
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        print("❌ Missing dependencies. Please install required packages.")
        return
    
    # Download data
    print("\n📥 Downloading market data...")
    data = download_market_data()
    
    if not data:
        print("❌ No data downloaded. Check internet connection.")
        return
        
    # Run strategy test
    print("\n🤖 Testing trading strategy...")
    results = simple_strategy_test(data)
    
    # Display results
    print("\n📊 STRATEGY TEST RESULTS")
    print("=" * 30)
    if results:
        print(f"Total data points: {len(data['SPY']) if 'SPY' in data else 0}")
        print(f"Trading signals generated: {results['total_signals']}")
        print(f"BUY signals: {results['buy_signals']} ({results['buy_ratio']*100:.1f}%)")
        print(f"SELL signals: {results['sell_signals']}")
    else:
        print("No results generated")
    
    print(f"\n💡 Next Steps:")
    print("1. Basic system is WORKING! 🎉")
    print("2. Data download successful")
    print("3. Ready to implement full strategy")
    print("4. Run: python strategy_development.py")

if __name__ == "__main__":
    main()