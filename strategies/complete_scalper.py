#!/usr/bin/env python3
"""
Complete Heikin Ashi + EMA Scalping Strategy
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class HeikinAshiCalculator:
    @staticmethod
    def calculate_heikin_ashi(df):
        """Calculate Heikin Ashi candles from regular OHLC data"""
        ha_df = df.copy()
        
        # Heikin Ashi Close = (Open + High + Low + Close) / 4
        ha_df['HA_Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
        
        # Heikin Ashi Open = (previous HA_Open + previous HA_Close) / 2
        ha_df['HA_Open'] = 0.0
        ha_df.loc[ha_df.index[0], 'HA_Open'] = (df['Open'].iloc[0] + df['Close'].iloc[0]) / 2
        
        for i in range(1, len(ha_df)):
            ha_df.loc[ha_df.index[i], 'HA_Open'] = (
                ha_df.loc[ha_df.index[i-1], 'HA_Open'] + 
                ha_df.loc[ha_df.index[i-1], 'HA_Close']
            ) / 2
        
        # Heikin Ashi High = max(High, HA_Open, HA_Close)
        ha_df['HA_High'] = ha_df[['High', 'HA_Open', 'HA_Close']].max(axis=1)
        
        # Heikin Ashi Low = min(Low, HA_Open, HA_Close)
        ha_df['HA_Low'] = ha_df[['Low', 'HA_Open', 'HA_Close']].min(axis=1)
        
        return ha_df
    
    @staticmethod
    def get_ha_trend(ha_df, lookback=3):
        """Determine Heikin Ashi trend direction"""
        if len(ha_df) < lookback:
            return 0
            
        recent = ha_df.tail(lookback)
        bullish_count = sum(recent['HA_Close'] > recent['HA_Open'])
        bearish_count = sum(recent['HA_Close'] < recent['HA_Open'])
        
        if bullish_count > bearish_count:
            return 1  # Bullish
        elif bearish_count > bullish_count:
            return -1  # Bearish
        else:
            return 0  # Neutral
    
    @staticmethod
    def is_ha_doji(ha_df, threshold=0.1):
        """Check if current HA candle is a Doji"""
        if len(ha_df) == 0:
            return False
            
        current = ha_df.iloc[-1]
        body_size = abs(current['HA_Close'] - current['HA_Open'])
        total_range = current['HA_High'] - current['HA_Low']
        
        if total_range == 0:
            return False
            
        return (body_size / total_range) < threshold

class EMAStrategy:
    @staticmethod
    def calculate_emas(df, fast_period=9, slow_period=21):
        """Calculate EMA indicators"""
        df = df.copy()
        df['EMA_Fast'] = df['Close'].ewm(span=fast_period).mean()
        df['EMA_Slow'] = df['Close'].ewm(span=slow_period).mean()
        return df
    
    @staticmethod
    def get_ema_trend(df):
        """Determine EMA trend direction"""
        if len(df) < 2:
            return 0
            
        current_fast = df['EMA_Fast'].iloc[-1]
        current_slow = df['EMA_Slow'].iloc[-1]
        prev_fast = df['EMA_Fast'].iloc[-2]
        prev_slow = df['EMA_Slow'].iloc[-2]
        
        # Bullish: Fast above Slow and both rising
        if (current_fast > current_slow and 
            current_fast > prev_fast and 
            current_slow > prev_slow):
            return 1
        
        # Bearish: Fast below Slow and both falling
        elif (current_fast < current_slow and 
              current_fast < prev_fast and 
              current_slow < prev_slow):
            return -1
        
        return 0

class PatternDetector:
    @staticmethod
    def bullish_engulfing(df):
        """Detect bullish engulfing pattern"""
        if len(df) < 2:
            return False
        
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        return (current['Close'] > current['Open'] and  # Current bullish
                previous['Close'] < previous['Open'] and  # Previous bearish
                current['Open'] < previous['Close'] and   # Engulfing body
                current['Close'] > previous['Open'])
    
    @staticmethod
    def bearish_engulfing(df):
        """Detect bearish engulfing pattern"""
        if len(df) < 2:
            return False
        
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        return (current['Close'] < current['Open'] and  # Current bearish
                previous['Close'] > previous['Open'] and  # Previous bullish
                current['Open'] > previous['Close'] and   # Engulfing body
                current['Close'] < previous['Open'])

class CompleteScalpingStrategy:
    def __init__(self):
        self.ha_calculator = HeikinAshiCalculator()
        self.ema_strategy = EMAStrategy()
        self.pattern_detector = PatternDetector()
        
        # Strategy parameters
        self.ha_lookback = 3
        self.min_trend_strength = 0.6
        self.volume_threshold = 1.2
        
    def analyze_market(self, df):
        """Complete market analysis using all indicators"""
        if len(df) < 50:  # Need sufficient data
            return None
        
        try:
            # Calculate Heikin Ashi
            ha_df = self.ha_calculator.calculate_heikin_ashi(df)
            
            # Calculate EMAs
            ema_df = self.ema_strategy.calculate_emas(df)
            
            # Get signals
            ha_trend = self.ha_calculator.get_ha_trend(ha_df, self.ha_lookback)
            ha_doji = self.ha_calculator.is_ha_doji(ha_df)
            ema_trend = self.ema_strategy.get_ema_trend(ema_df)
            
            # Pattern detection
            bullish_pattern = self.pattern_detector.bullish_engulfing(df)
            bearish_pattern = self.pattern_detector.bearish_engulfing(df)
            
            # Volume analysis
            volume_ok, volume_ratio = self._check_volume(df)
            
            # Trend strength
            trend_strength = self._calculate_trend_strength(ha_df, df)
            
            # Generate final signal
            signal = self._generate_signal({
                'ha_trend': ha_trend,
                'ema_trend': ema_trend,
                'ha_doji': ha_doji,
                'bullish_pattern': bullish_pattern,
                'bearish_pattern': bearish_pattern,
                'volume_ok': volume_ok,
                'trend_strength': trend_strength,
                'current_price': df['Close'].iloc[-1]
            })
            
            return {
                'signal': signal,
                'ha_trend': ha_trend,
                'ema_trend': ema_trend,
                'ha_doji': ha_doji,
                'bullish_pattern': bullish_pattern,
                'bearish_pattern': bearish_pattern,
                'volume_ratio': volume_ratio,
                'trend_strength': trend_strength,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"❌ Market analysis failed: {e}")
            return None
    
    def _check_volume(self, df, lookback=20):
        """Check volume confirmation"""
        if len(df) < lookback + 1:
            return False, 0
            
        recent_volume = df['Volume'].tail(3).mean()
        avg_volume = df['Volume'].rolling(lookback).mean().iloc[-1]
        
        if avg_volume == 0:
            return False, 0
            
        volume_ratio = recent_volume / avg_volume
        volume_ok = volume_ratio > self.volume_threshold
        
        return volume_ok, volume_ratio
    
    def _calculate_trend_strength(self, ha_df, regular_df):
        """Calculate overall trend strength (0-1)"""
        strength_factors = []
        
        # HA trend consistency
        if len(ha_df) >= 5:
            recent_ha = ha_df.tail(5)
            ha_bullish = sum(recent_ha['HA_Close'] > recent_ha['HA_Open'])
            ha_consistency = abs(ha_bullish - 2.5) / 2.5  # Normalize to 0-1
            strength_factors.append(ha_consistency)
        
        # Price momentum
        if len(regular_df) >= 10:
            recent_prices = regular_df['Close'].tail(10)
            price_change = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]
            momentum_strength = min(abs(price_change) * 10, 1.0)  # Normalize
            strength_factors.append(momentum_strength)
        
        return sum(strength_factors) / len(strength_factors) if strength_factors else 0
    
    def _generate_signal(self, signals):
        """Generate final trading signal"""
        if signals['trend_strength'] < self.min_trend_strength:
            return 'HOLD'
        
        # Bullish conditions
        bullish_conditions = (
            signals['ha_trend'] == 1 and
            signals['ema_trend'] == 1 and
            signals['bullish_pattern'] and
            not signals['ha_doji'] and
            signals['volume_ok']
        )
        
        # Bearish conditions
        bearish_conditions = (
            signals['ha_trend'] == -1 and
            signals['ema_trend'] == -1 and
            signals['bearish_pattern'] and
            not signals['ha_doji'] and
            signals['volume_ok']
        )
        
        if bullish_conditions:
            return 'BUY_CALL'
        elif bearish_conditions:
            return 'BUY_PUT'
        else:
            return 'HOLD'