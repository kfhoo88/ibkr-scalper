import pandas as pd
import logging
from datetime import datetime, timedelta
from .base_strategy import BaseStrategy
from technical.heikin_ashi import HeikinAshi
from technical.moving_averages import MovingAverages
from technical.pattern_detector import PatternDetector

class HAMAScalpingStrategy(BaseStrategy):
    def __init__(self, ib_client=None, symbol='SPY', timeframe='1 min', 
                 ma_fast=9, ma_slow=21, lookback_periods=50):
        super().__init__(ib_client)
        self.symbol = symbol
        self.timeframe = timeframe
        self.ma_fast = ma_fast
        self.ma_slow = ma_slow
        self.lookback_periods = lookback_periods
        
        # Strategy parameters
        self.ha_lookback = 3
        self.min_trend_strength = 0.6
        self.volume_multiplier_threshold = 1.2
        
    def analyze_market_condition(self, df):
        """Comprehensive market analysis using HA + MA + Candlestick patterns"""
        if len(df) < self.lookback_periods:
            return None
            
        # Calculate Heikin Ashi
        ha_df = HeikinAshi.calculate_heikin_ashi(df)
        
        # Get technical signals
        ha_trend = HeikinAshi.get_ha_trend(ha_df, self.ha_lookback)
        ha_doji = HeikinAshi.is_ha_doji(ha_df)
        ma_trend = MovingAverages.get_ma_trend(df, self.ma_fast, self.ma_slow)
        bullish_pattern = PatternDetector.bullish_engulfing(df) or PatternDetector.hammer(df)
        bearish_pattern = PatternDetector.bearish_engulfing(df)
        
        # Volume analysis
        volume_ok, volume_ratio = self.volume_confirmation(df)
        
        # Trend strength
        trend_strength = self.calculate_trend_strength(ha_df, df)
        
        # Generate signals
        signals = {
            'ha_trend': ha_trend,
            'ma_trend': ma_trend,
            'ha_doji': ha_doji,
            'bullish_pattern': bullish_pattern,
            'bearish_pattern': bearish_pattern,
            'trend_strength': trend_strength,
            'volume_ok': volume_ok,
            'volume_ratio': volume_ratio,
            'timestamp': datetime.now()
        }
        
        return signals
    
    def volume_confirmation(self, df, lookback=20):
        """Volume confirmation for entries"""
        if len(df) < lookback + 1:
            return False, 0
            
        recent_volume = df['volume'].tail(3).mean()
        avg_volume = df['volume'].rolling(lookback).mean().iloc[-1]
        
        if avg_volume == 0:
            return False, 0
            
        volume_ratio = recent_volume / avg_volume
        volume_ok = volume_ratio > self.volume_multiplier_threshold
        
        return volume_ok, volume_ratio
    
    def calculate_trend_strength(self, ha_df, regular_df):
        """Calculate overall trend strength (0-1)"""
        strength_factors = []
        
        # HA trend consistency
        ha_trends = []
        for i in range(1, min(6, len(ha_df))):
            if ha_df['HA_Close'].iloc[-i] > ha_df['HA_Open'].iloc[-i]:
                ha_trends.append(1)
            else:
                ha_trends.append(-1)
        
        if ha_trends:
            ha_consistency = abs(sum(ha_trends)) / len(ha_trends)
            strength_factors.append(ha_consistency)
        
        # MA slope strength
        if len(regular_df) >= 5:
            recent_closes = regular_df['close'].tail(5)
            ma_slope = (recent_closes.iloc[-1] - recent_closes.iloc[0]) / recent_closes.iloc[0]
            strength_factors.append(min(abs(ma_slope) * 100, 1.0))
        
        return sum(strength_factors) / len(strength_factors) if strength_factors else 0
    
    def generate_trade_signal(self, signals):
        """Generate trade signals based on combined analysis"""
        if not signals or signals['trend_strength'] < self.min_trend_strength:
            return None
        
        # Strong bullish setup
        bullish_conditions = (
            signals['ha_trend'] == 1 and
            signals['ma_trend'] == 1 and
            signals['bullish_pattern'] and
            not signals['ha_doji'] and
            signals['volume_ok']
        )
        
        # Strong bearish setup
        bearish_conditions = (
            signals['ha_trend'] == -1 and
            signals['ma_trend'] == -1 and
            signals['bearish_pattern'] and
            not signals['ha_doji'] and
            signals['volume_ok']
        )
        
        if bullish_conditions:
            return 'CALL'
        elif bearish_conditions:
            return 'PUT'
        else:
            return None