#!/usr/bin/env python3
"""
Complete Debug Scalping Strategy with All Methods
"""

import pandas as pd
import numpy as np
import logging
from strategies.complete_scalper import CompleteScalpingStrategy

logger = logging.getLogger(__name__)

class DebugScalpingStrategy(CompleteScalpingStrategy):
    """Complete strategy with detailed debugging"""
    
    def __init__(self):
        super().__init__()
        
        # Optimized parameters for 1-minute scalping
        self.ha_lookback = 2           # Shorter lookback for faster signals
        self.min_trend_strength = 0.3  # Lower threshold for 1-minute
        self.volume_threshold = 1.5    # Higher volume requirement for confirmation
        
        # EMA periods optimized for 1-minute
        self.ema_fast = 5    # 5-minute EMA
        self.ema_slow = 13   # 13-minute EMA
    
    def calculate_emas(self, df):
        """Calculate EMAs with 1-minute optimized periods"""
        df = df.copy()
        df['EMA_Fast'] = df['Close'].ewm(span=self.ema_fast).mean()
        df['EMA_Slow'] = df['Close'].ewm(span=self.ema_slow).mean()
        return df
    
    def get_ema_trend(self, df):
        """Determine EMA trend direction with debug"""
        if len(df) < 2:
            return 0
            
        current_fast = df['EMA_Fast'].iloc[-1]
        current_slow = df['EMA_Slow'].iloc[-1]
        prev_fast = df['EMA_Fast'].iloc[-2]
        prev_slow = df['EMA_Slow'].iloc[-2]
        
        print(f"   📊 EMA Values: Fast={current_fast:.2f}, Slow={current_slow:.2f}")
        print(f"   📊 EMA Previous: Fast={prev_fast:.2f}, Slow={prev_slow:.2f}")
        
        # Bullish: Fast above Slow and both rising
        if (current_fast > current_slow and 
            current_fast > prev_fast and 
            current_slow > prev_slow):
            print("   ✅ EMA Trend: BULLISH (Fast > Slow and both rising)")
            return 1
        
        # Bearish: Fast below Slow and both falling
        elif (current_fast < current_slow and 
              current_fast < prev_fast and 
              current_slow < prev_slow):
            print("   ✅ EMA Trend: BEARISH (Fast < Slow and both falling)")
            return -1
        
        print("   ⚠️ EMA Trend: NEUTRAL (no clear trend)")
        return 0
    
    def analyze_market(self, df):
        """Analyze market with detailed debugging"""
        print(f"\n🔍 DEBUG ANALYSIS - Data length: {len(df)}")
        print(f"   First date: {df.index[0]}")
        print(f"   Last date: {df.index[-1]}")
        print(f"   Current price: ${df['Close'].iloc[-1]:.2f}")
        
        if len(df) < 50:
            print("❌ Insufficient data for analysis (need >= 50 bars)")
            return None
        
        try:
            # Calculate Heikin Ashi with debug
            print(f"\n📊 CALCULATING HEIKIN ASHI...")
            ha_df = self.ha_calculator.calculate_heikin_ashi(df)
            
            # Check last few HA candles
            print(f"   Last 3 HA candles:")
            for i in range(-3, 0):
                idx = ha_df.index[i]
                ha_open = ha_df.loc[idx, 'HA_Open']
                ha_close = ha_df.loc[idx, 'HA_Close']
                direction = "BULLISH" if ha_close > ha_open else "BEARISH" if ha_close < ha_open else "DOJI"
                print(f"     {idx}: {ha_open:.2f} -> {ha_close:.2f} ({direction})")
            
            ha_trend = self.ha_calculator.get_ha_trend(ha_df, self.ha_lookback)
            ha_doji = self.ha_calculator.is_ha_doji(ha_df)
            
            print(f"   HA Trend: {ha_trend} (lookback={self.ha_lookback})")
            print(f"   HA Doji: {ha_doji}")

            # Calculate EMAs with debug
            print(f"\n📊 CALCULATING EMAs...")
            ema_df = self.calculate_emas(df)
            ema_trend = self.get_ema_trend(ema_df)
            
            # Pattern detection with debug
            print(f"\n📊 CHECKING PATTERNS...")
            bullish_pattern = self.pattern_detector.bullish_engulfing(df)
            bearish_pattern = self.pattern_detector.bearish_engulfing(df)
            
            # Show last 2 candles for pattern checking
            if len(df) >= 2:
                last_candle = df.iloc[-1]
                prev_candle = df.iloc[-2]
                print(f"   Last 2 candles for pattern detection:")
                print(f"     Previous: O={prev_candle['Open']:.2f}, H={prev_candle['High']:.2f}, L={prev_candle['Low']:.2f}, C={prev_candle['Close']:.2f}")
                print(f"     Current:  O={last_candle['Open']:.2f}, H={last_candle['High']:.2f}, L={last_candle['Low']:.2f}, C={last_candle['Close']:.2f}")
            
            print(f"   Bullish Engulfing: {bullish_pattern}")
            print(f"   Bearish Engulfing: {bearish_pattern}")

            # Volume analysis with debug
            print(f"\n📊 ANALYZING VOLUME...")
            volume_ok, volume_ratio = self._check_volume(df)
            
            # Show volume details
            if len(df) >= 20:
                recent_volume = df['Volume'].tail(3).mean()
                avg_volume = df['Volume'].tail(20).mean()
                print(f"   Recent volume (3 bars): {recent_volume:.0f}")
                print(f"   Average volume (20 bars): {avg_volume:.0f}")
                print(f"   Volume ratio: {volume_ratio:.2f}")
                print(f"   Volume threshold: {self.volume_threshold}")
                print(f"   Volume OK: {volume_ok}")

            # Trend strength with debug
            print(f"\n📊 CALCULATING TREND STRENGTH...")
            trend_strength = self._calculate_trend_strength(ha_df, df)
            print(f"   Trend strength: {trend_strength:.2f}")
            print(f"   Minimum required: {self.min_trend_strength}")

            # Generate final signal with condition breakdown
            print(f"\n🎯 GENERATING TRADING SIGNAL...")
            signal = self._generate_signal_debug({
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
                'timestamp': pd.Timestamp.now()
            }
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _check_volume(self, df, lookback=20):
        """Check volume confirmation with debug"""
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
        """Trend strength calculation with debug"""
        strength_factors = []
        
        print(f"   Calculating trend strength factors:")
        
        # HA trend consistency
        if len(ha_df) >= 5:
            recent_ha = ha_df.tail(5)
            ha_bullish = sum(recent_ha['HA_Close'] > recent_ha['HA_Open'])
            ha_consistency = abs(ha_bullish - 2.5) / 2.5
            strength_factors.append(ha_consistency)
            print(f"     HA Consistency: {ha_bullish}/5 bullish = {ha_consistency:.2f}")
        
        # Price momentum
        if len(regular_df) >= 10:
            recent_prices = regular_df['Close'].tail(10)
            price_change = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]
            momentum_strength = min(abs(price_change) * 1000, 1.0)
            strength_factors.append(momentum_strength)
            print(f"     Price Momentum: {price_change*100:.3f}% = {momentum_strength:.2f}")
        
        # Volume strength
        if len(regular_df) >= 20:
            recent_volume = regular_df['Volume'].tail(5).mean()
            avg_volume = regular_df['Volume'].tail(20).mean()
            if avg_volume > 0:
                volume_strength = min(recent_volume / avg_volume / 3, 1.0)
                strength_factors.append(volume_strength)
                print(f"     Volume Strength: {recent_volume/avg_volume:.2f} ratio = {volume_strength:.2f}")
        
        final_strength = sum(strength_factors) / len(strength_factors) if strength_factors else 0
        print(f"   Final trend strength: {final_strength:.2f} (from {len(strength_factors)} factors)")
        
        return final_strength
    
    def _generate_signal_debug(self, signals):
        """Generate signal with detailed condition debugging"""
        print(f"\n🎯 SIGNAL GENERATION CONDITIONS:")
        print(f"   Strategy Parameters:")
        print(f"     - HA Lookback: {self.ha_lookback}")
        print(f"     - Min Trend Strength: {self.min_trend_strength}")
        print(f"     - Volume Threshold: {self.volume_threshold}")
        
        # Check trend strength first
        if signals['trend_strength'] < self.min_trend_strength:
            print(f"   ❌ TREND STRENGTH FAILED: {signals['trend_strength']:.2f} < {self.min_trend_strength}")
            return 'HOLD'
        else:
            print(f"   ✅ TREND STRENGTH PASSED: {signals['trend_strength']:.2f} >= {self.min_trend_strength}")
        
        # Bullish conditions
        print(f"\n   🔼 BULLISH CONDITIONS:")
        bullish_conditions = [
            (f"HA Trend == 1", signals['ha_trend'] == 1),
            (f"EMA Trend == 1", signals['ema_trend'] == 1),
            (f"Bullish Pattern OR Strong Trend", signals['bullish_pattern'] or signals['trend_strength'] > 0.6),
            (f"Not HA Doji", not signals['ha_doji']),
            (f"Volume OK (>{self.volume_threshold})", signals['volume_ok'])
        ]
        
        bullish_all_met = True
        for condition_name, condition_met in bullish_conditions:
            status = "✅" if condition_met else "❌"
            print(f"     {status} {condition_name}: {condition_met}")
            if not condition_met:
                bullish_all_met = False
        
        # Bearish conditions
        print(f"\n   🔽 BEARISH CONDITIONS:")
        bearish_conditions = [
            (f"HA Trend == -1", signals['ha_trend'] == -1),
            (f"EMA Trend == -1", signals['ema_trend'] == -1),
            (f"Bearish Pattern OR Strong Trend", signals['bearish_pattern'] or signals['trend_strength'] > 0.6),
            (f"Not HA Doji", not signals['ha_doji']),
            (f"Volume OK (>{self.volume_threshold})", signals['volume_ok'])
        ]
        
        bearish_all_met = True
        for condition_name, condition_met in bearish_conditions:
            status = "✅" if condition_met else "❌"
            print(f"     {status} {condition_name}: {condition_met}")
            if not condition_met:
                bearish_all_met = False
        
        # Final decision
        print(f"\n   🎯 FINAL DECISION:")
        if bullish_all_met:
            print(f"   🚀 ALL BULLISH CONDITIONS MET - GENERATING BUY_CALL SIGNAL!")
            return 'BUY_CALL'
        elif bearish_all_met:
            print(f"   🚀 ALL BEARISH CONDITIONS MET - GENERATING BUY_PUT SIGNAL!")
            return 'BUY_PUT'
        else:
            print(f"   ⏸️  NO CONDITIONS FULLY MET - HOLDING")
            if not bullish_all_met and not bearish_all_met:
                print(f"   💡 Missing conditions:")
                if signals['ha_trend'] != signals['ema_trend']:
                    print(f"     - HA and EMA trends don't match (HA: {signals['ha_trend']}, EMA: {signals['ema_trend']})")
                if not signals['volume_ok']:
                    print(f"     - Volume ratio too low (need > {self.volume_threshold})")
                if not signals['bullish_pattern'] and not signals['bearish_pattern'] and signals['trend_strength'] <= 0.6:
                    print(f"     - No pattern and trend strength <= 0.6")
            return 'HOLD'