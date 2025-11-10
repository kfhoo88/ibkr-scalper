import pandas as pd
import numpy as np

class PatternDetector:
    @staticmethod
    def bullish_engulfing(df):
        """Detect bullish engulfing pattern"""
        if len(df) < 2:
            return False
        
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        return (current['close'] > current['open'] and
                previous['close'] < previous['open'] and
                current['open'] < previous['close'] and
                current['close'] > previous['open'])
    
    @staticmethod
    def bearish_engulfing(df):
        """Detect bearish engulfing pattern"""
        if len(df) < 2:
            return False
        
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        return (current['close'] < current['open'] and
                previous['close'] > previous['open'] and
                current['open'] > previous['close'] and
                current['close'] < previous['open'])
    
    @staticmethod
    def hammer(df, threshold=0.6):
        """Detect hammer pattern"""
        if len(df) < 1:
            return False
        
        candle = df.iloc[-1]
        body_size = abs(candle['close'] - candle['open'])
        total_range = candle['high'] - candle['low']
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        
        return (lower_shadow > body_size * 2 and
                upper_shadow < body_size * 0.5 and
                body_size / total_range < threshold)