#!/usr/bin/env python3
"""
Working Main File with Data Fallback
"""

import os
import pandas as pd
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_data():
    """Load data from files or generate synthetic data"""
    data_files = {
        'SPY': 'data/historical/SPY.csv',
        'QQQ': 'data/historical/QQQ.csv',
        'SPY_alt': 'data/historical/SPY_alt.csv', 
        'QQQ_alt': 'data/historical/QQQ_alt.csv',
        'SPY_synthetic': 'data/historical/SPY_synthetic.csv',
        'QQQ_synthetic': 'data/historical/QQQ_synthetic.csv'
    }
    
    data = {}
    
    for symbol, filepath in data_files.items():
        if os.path.exists(filepath):
            try:
                loaded_data = pd.read_csv(filepath, index_col=0, parse_dates=True)
                if not loaded_data.empty:
                    # Extract symbol name from filename
                    sym = symbol.split('_')[0]
                    data[sym] = loaded_data
                    logger.info(f"✅ Loaded {sym} from {filepath} ({len(loaded_data)} bars)")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load {filepath}: {e}")
    
    return data

def run_technical_analysis(data):
    """Run technical analysis on loaded data"""
    if not data:
        logger.error("❌ No data available for analysis")
        return None
    
    results = {}
    
    for symbol, symbol_data in data.items():
        try:
            logger.info(f"🔍 Analyzing {symbol}...")
            
            # Simple moving averages
            sma_20 = symbol_data['Close'].rolling(window=20).mean().iloc[-1]
            current_price = symbol_data['Close'].iloc[-1]
            
            # Determine trend
            if current_price > sma_20:
                trend = "BULLISH"
            else:
                trend = "BEARISH"
            
            # Calculate some basic metrics
            volatility = symbol_data['Close'].pct_change().std()
            total_bars = len(symbol_data)
            
            results[symbol] = {
                'current_price': current_price,
                'sma_20': sma_20,
                'trend': trend,
                'volatility': volatility,
                'total_bars': total_bars,
                'date_range': f"{symbol_data.index[0]} to {symbol_data.index[-1]}"
            }
            
        except Exception as e:
            logger.error(f"❌ Analysis failed for {symbol}: {e}")
    
    return results

def main():
    print("🚀 IBKR Scalper - Working Version")
    print("=" * 40)
    
    # Load data
    print("📂 Loading data...")
    data = load_data()
    
    if not data:
        print("❌ No data files found.")
        print("💡 Please run: python data_downloader.py")
        return
    
    # Run analysis
    print("\n🤖 Running technical analysis...")
    results = run_technical_analysis(data)
    
    # Display results
    print("\n📊 TRADING ANALYSIS RESULTS")
    print("=" * 35)
    
    if results:
        for symbol, analysis in results.items():
            print(f"\n{symbol}:")
            print(f"  Current Price: ${analysis['current_price']:.2f}")
            print(f"  SMA 20: ${analysis['sma_20']:.2f}")
            print(f"  Trend: {analysis['trend']}")
            print(f"  Volatility: {analysis['volatility']:.4f}")
            print(f"  Bars: {analysis['total_bars']}")
            print(f"  Period: {analysis['date_range']}")
    else:
        print("❌ No analysis results")
    
    print(f"\n🎉 SYSTEM READY!")
    print(f"💡 Next: Implement the complete trading strategy")

if __name__ == "__main__":
    main()