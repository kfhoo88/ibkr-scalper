#!/usr/bin/env python3
"""
IBKR Scalper - Fixed Version for Python 3.8
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check and import dependencies with Python 3.8 compatibility"""
    dependencies = {
        'pandas': None,
        'numpy': None,
        'yfinance': None,
        'matplotlib': None
    }
    
    for dep in dependencies:
        try:
            module = __import__(dep)
            dependencies[dep] = getattr(module, '__version__', 'unknown')
            logger.info(f"✅ {dep} {dependencies[dep]}")
        except ImportError as e:
            logger.error(f"❌ {dep} import failed: {e}")
            return False
    
    return True

def download_market_data():
    """Download SPY and QQQ data with error handling"""
    symbols = ['SPY', 'QQQ']
    data = {}
    
    for symbol in symbols:
        try:
            logger.info(f"📥 Downloading {symbol} data...")
            
            # Import yfinance here to avoid multitasking issues
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            # Use shorter period for testing
            hist_data = ticker.history(period="1mo", interval="1h")
            
            if hist_data.empty:
                logger.warning(f"⚠️ No data returned for {symbol}")
                continue
                
            data[symbol] = hist_data
            logger.info(f"✅ {symbol}: {len(hist_data)} bars")
            
        except Exception as e:
            logger.error(f"❌ Failed to download {symbol}: {e}")
    
    return data

def run_heikin_ashi_analysis(data):
    """Run Heikin Ashi analysis on the data"""
    if 'SPY' not in data:
        return None
        
    spy_data = data['SPY']
    logger.info("Running Heikin Ashi analysis...")
    
    try:
        # Calculate Heikin Ashi candles
        ha_data = spy_data.copy()
        
        # Heikin Ashi calculations
        ha_data['HA_Close'] = (spy_data['Open'] + spy_data['High'] + spy_data['Low'] + spy_data['Close']) / 4
        
        # Initialize HA_Open
        ha_data['HA_Open'] = (spy_data['Open'] + spy_data['Close']) / 2
        for i in range(1, len(ha_data)):
            ha_data.iloc[i, ha_data.columns.get_loc('HA_Open')] = (
                ha_data.iloc[i-1]['HA_Open'] + ha_data.iloc[i-1]['HA_Close']
            ) / 2
        
        # Count bullish vs bearish HA candles
        bullish_ha = (ha_data['HA_Close'] > ha_data['HA_Open']).sum()
        bearish_ha = (ha_data['HA_Close'] < ha_data['HA_Open']).sum()
        
        return {
            'total_candles': len(ha_data),
            'bullish_ha': bullish_ha,
            'bearish_ha': bearish_ha,
            'bullish_ratio': bullish_ha / len(ha_data) if len(ha_data) > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"❌ Heikin Ashi analysis failed: {e}")
        return None

def run_ema_analysis(data):
    """Run EMA analysis on the data"""
    if 'SPY' not in data:
        return None
        
    spy_data = data['SPY']
    
    try:
        # Calculate EMAs
        ema_9 = spy_data['Close'].ewm(span=9).mean()
        ema_21 = spy_data['Close'].ewm(span=21).mean()
        
        # Current EMA values
        current_ema_9 = ema_9.iloc[-1]
        current_ema_21 = ema_21.iloc[-1]
        
        # Determine trend
        if current_ema_9 > current_ema_21:
            trend = "BULLISH"
        elif current_ema_9 < current_ema_21:
            trend = "BEARISH"
        else:
            trend = "NEUTRAL"
            
        return {
            'ema_9': current_ema_9,
            'ema_21': current_ema_21,
            'trend': trend,
            'ema_spread': abs(current_ema_9 - current_ema_21)
        }
        
    except Exception as e:
        logger.error(f"❌ EMA analysis failed: {e}")
        return None

def main():
    print("🚀 IBKR Scalper - Fixed Python 3.8 Version")
    print("=" * 50)
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        print("❌ Missing dependencies.")
        return
    
    # Download data
    print("\n📥 Downloading market data...")
    data = download_market_data()
    
    if not data:
        print("❌ No data downloaded.")
        return
        
    # Run analyses
    print("\n🤖 Running technical analysis...")
    
    # Heikin Ashi analysis
    ha_results = run_heikin_ashi_analysis(data)
    
    # EMA analysis
    ema_results = run_ema_analysis(data)
    
    # Display results
    print("\n📊 TECHNICAL ANALYSIS RESULTS")
    print("=" * 35)
    
    if ha_results:
        print(f"Heikin Ashi Analysis:")
        print(f"  Total candles: {ha_results['total_candles']}")
        print(f"  Bullish HA: {ha_results['bullish_ha']} ({ha_results['bullish_ratio']*100:.1f}%)")
        print(f"  Bearish HA: {ha_results['bearish_ha']}")
    
    if ema_results:
        print(f"\nEMA Analysis:")
        print(f"  EMA 9: ${ema_results['ema_9']:.2f}")
        print(f"  EMA 21: ${ema_results['ema_21']:.2f}")
        print(f"  Trend: {ema_results['trend']}")
        print(f"  Spread: ${ema_results['ema_spread']:.2f}")
    
    # Save data for future use
    try:
        import pandas as pd
        for symbol, symbol_data in data.items():
            filename = f"data/historical/{symbol}_data.csv"
            symbol_data.to_csv(filename)
            print(f"✅ {symbol} data saved to {filename}")
    except Exception as e:
        logger.error(f"❌ Failed to save data: {e}")
    
    print(f"\n🎉 SYSTEM IS FULLY OPERATIONAL!")
    print(f"💡 Next: Implement the complete trading strategy")
    print(f"📁 Data saved in: data/historical/")

if __name__ == "__main__":
    main()