# vwap_ma_strategy/utils/option_pricing.py
import pandas as pd
import numpy as np
from datetime import time

class OptionPricer:
    def __init__(self):
        self.base_rates = {'SPY': 0.010, 'QQQ': 0.012}
    
    def calculate_historical_volatility(self, df, period=20):
        """Calculate historical volatility from price data"""
        returns = df['close'].pct_change()
        hist_vol = returns.rolling(period).std() * np.sqrt(252) * 100
        return hist_vol
    
    def estimate_time_decay(self, current_time):
        """Estimate time decay for 1DTE options"""
        if current_time < time(12, 0):
            return 0.95  # Morning: 5% decay
        elif current_time < time(14, 0):
            return 0.85  # Early afternoon: 15% decay
        else:
            return 0.70  # Late afternoon: 30% decay
    
    def calculate_option_price(self, df, current_index, symbol):
        """Calculate realistic option price using volatility model"""
        current_row = df.iloc[current_index]
        underlying_price = current_row['close']
        current_time = current_row.name.time()
        
        # Base rate by symbol
        base_rate = self.base_rates.get(symbol, 0.011)
        
        # Historical volatility adjustment
        hist_vol = self.calculate_historical_volatility(df).iloc[current_index]
        vol_adjustment = max(0.5, min(2.0, hist_vol / 20))  # Normalize to 20% VIX
        
        # Time decay
        time_decay = self.estimate_time_decay(current_time)
        
        # Calculate option price
        option_price = underlying_price * base_rate * vol_adjustment * time_decay
        
        # Ensure reasonable bounds
        option_price = max(option_price, underlying_price * 0.005)  # Min 0.5%
        option_price = min(option_price, underlying_price * 0.03)   # Max 3%
        
        return round(option_price, 2)