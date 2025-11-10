import pandas as pd
import numpy as np

class MovingAverages:
    @staticmethod
    def calculate_emas(df, periods=[9, 21]):
        """Calculate multiple EMAs"""
        ema_data = {}
        for period in periods:
            ema_data[f'ema_{period}'] = df['close'].ewm(span=period).mean()
        return ema_data
    
    @staticmethod
    def get_ma_trend(df, fast_period=9, slow_period=21):
        """Determine trend direction using EMAs"""
        if len(df) < slow_period:
            return 0
            
        df = df.copy()
        df['ema_fast'] = df['close'].ewm(span=fast_period).mean()
        df['ema_slow'] = df['close'].ewm(span=slow_period).mean()
        
        current_fast = df['ema_fast'].iloc[-1]
        current_slow = df['ema_slow'].iloc[-1]
        previous_fast = df['ema_fast'].iloc[-2]
        previous_slow = df['ema_slow'].iloc[-2]
        
        # Bullish: Fast EMA above Slow EMA and both trending up
        if (current_fast > current_slow and 
            current_fast > previous_fast and 
            current_slow > previous_slow):
            return 1
        
        # Bearish: Fast EMA below Slow EMA and both trending down
        elif (current_fast < current_slow and 
              current_fast < previous_fast and 
              current_slow < previous_slow):
            return -1
        
        else:
            return 0