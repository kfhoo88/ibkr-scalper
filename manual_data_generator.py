#!/usr/bin/env python3
"""
Manual Data Generator - Creates synthetic data for testing
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_synthetic_data(symbol, days=180, start_price=400):
    """Generate synthetic price data for testing"""
    print(f"📊 Generating synthetic data for {symbol}...")
    
    # Create date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='1H')
    
    # Remove weekends (simplified)
    dates = dates[dates.dayofweek < 5]
    
    # Generate price data with some randomness
    np.random.seed(42)  # For reproducible results
    
    prices = [start_price]
    for i in range(1, len(dates)):
        # Random price movement
        change = np.random.normal(0, 0.002)  # Small random changes
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    # Create DataFrame
    data = pd.DataFrame({
        'Open': prices,
        'High': [p * (1 + abs(np.random.normal(0, 0.001))) for p in prices],
        'Low': [p * (1 - abs(np.random.normal(0, 0.001))) for p in prices],
        'Close': prices,
        'Volume': np.random.randint(1000000, 5000000, len(prices))
    }, index=dates)
    
    # Add some realistic price variations
    data['High'] = data[['Open', 'High', 'Close']].max(axis=1)
    data['Low'] = data[['Open', 'Low', 'Close']].min(axis=1)
    
    print(f"✅ Generated {len(data)} synthetic bars for {symbol}")
    return data

def main():
    print("🚀 Manual Data Generator")
    print("=" * 30)
    
    # Create directory
    os.makedirs('data/historical', exist_ok=True)
    
    # Generate data for SPY and QQQ
    symbols = {
        'SPY': 450,  # Start around $450
        'QQQ': 380   # Start around $380
    }
    
    all_data = {}
    
    for symbol, start_price in symbols.items():
        data = generate_synthetic_data(symbol, days=90, start_price=start_price)
        all_data[symbol] = data
        
        # Save to CSV
        filename = f"data/historical/{symbol}_synthetic.csv"
        data.to_csv(filename)
        print(f"💾 Saved {filename}")
    
    print(f"\n🎉 Generated synthetic data for {len(all_data)} symbols")
    print("💡 You can now test the trading strategy with this data")
    
    # Display sample
    print(f"\n📈 SPY Sample (first 5 rows):")
    print(all_data['SPY'].head())
    
    print(f"\n📈 QQQ Sample (first 5 rows):")
    print(all_data['QQQ'].head())

if __name__ == "__main__":
    main()