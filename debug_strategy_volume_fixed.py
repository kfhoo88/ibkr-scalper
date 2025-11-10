#!/usr/bin/env python3
"""
Fixed Strategy Debugger with Dynamic Volume - Standalone Version
"""

import pandas as pd
import numpy as np
import os

def calculate_heikin_ashi(df):
    """Calculate Heikin Ashi candles"""
    # Use lowercase column names to handle different cases
    df_lower = df.rename(columns=str.lower)
    
    ha_close = (df_lower['open'] + df_lower['high'] + df_lower['low'] + df_lower['close']) / 4
    ha_open = [(df_lower['open'].iloc[0] + df_lower['close'].iloc[0]) / 2]
    
    for i in range(1, len(df_lower)):
        ha_open.append((ha_open[i-1] + ha_close.iloc[i-1]) / 2)
    
    ha_open = pd.Series(ha_open, index=df_lower.index)
    ha_high = df_lower[['high', 'open', 'close']].max(axis=1)
    ha_low = df_lower[['low', 'open', 'close']].min(axis=1)
    
    return ha_open, ha_high, ha_low, ha_close

def calculate_ema_trend(df, fast_period=8, slow_period=21):
    """Calculate EMA trend direction"""
    df_lower = df.rename(columns=str.lower)
    df_copy = df_lower.copy()
    
    df_copy['ema_fast'] = df_copy['close'].ewm(span=fast_period).mean()
    df_copy['ema_slow'] = df_copy['close'].ewm(span=slow_period).mean()
    
    # Get current and previous values
    current_fast = df_copy['ema_fast'].iloc[-1]
    current_slow = df_copy['ema_slow'].iloc[-1]
    prev_fast = df_copy['ema_fast'].iloc[-2] if len(df_copy) > 1 else current_fast
    prev_slow = df_copy['ema_slow'].iloc[-2] if len(df_copy) > 1 else current_slow
    
    # Determine trend
    if current_fast > current_slow and current_fast > prev_fast and current_slow > prev_slow:
        return 1, current_fast, current_slow, prev_fast, prev_slow  # Bullish
    elif current_fast < current_slow and current_fast < prev_fast and current_slow < prev_slow:
        return -1, current_fast, current_slow, prev_fast, prev_slow  # Bearish
    else:
        return 0, current_fast, current_slow, prev_fast, prev_slow  # Neutral

def detect_candle_patterns(df):
    """Detect bullish and bearish engulfing patterns"""
    df_lower = df.rename(columns=str.lower)
    
    if len(df_lower) < 3:
        return False, False
    
    current = df_lower.iloc[-1]
    prev = df_lower.iloc[-2]
    
    bullish_engulfing = (current['close'] > current['open'] and 
                        prev['close'] < prev['open'] and
                        current['open'] < prev['close'] and 
                        current['close'] > prev['open'])
    
    bearish_engulfing = (current['close'] < current['open'] and 
                        prev['close'] > prev['open'] and
                        current['open'] > prev['close'] and 
                        current['close'] < prev['open'])
    
    return bullish_engulfing, bearish_engulfing

def calculate_trend_strength(df, ha_trend, ha_doji, volume_ratio):
    """Calculate trend strength score (0-1)"""
    df_lower = df.rename(columns=str.lower)
    factors = []
    
    # Factor 1: Heikin Ashi consistency (5-bar lookback)
    if len(df_lower) >= 5:
        ha_bullish_count = 0
        for i in range(1, 6):
            idx = -i
            if df_lower['ha_close'].iloc[idx] > df_lower['ha_open'].iloc[idx]:
                ha_bullish_count += 1
        
        ha_consistency = ha_bullish_count / 5
        # Convert to directional consistency based on current trend
        if ha_trend == -1:
            ha_consistency = 1 - ha_consistency
        factors.append(ha_consistency)
    
    # Factor 2: Price momentum (5-bar percentage change)
    if len(df_lower) >= 5:
        price_change = (df_lower['close'].iloc[-1] - df_lower['close'].iloc[-5]) / df_lower['close'].iloc[-5]
        # Normalize to 0-1 scale (assuming max 1% move in 5 bars)
        price_momentum = min(abs(price_change) / 0.01, 1.0)
        factors.append(price_momentum)
    
    # Factor 3: Volume strength
    volume_strength = min(volume_ratio / 2.0, 1.0)  # Normalize with max expected ratio of 2.0
    factors.append(volume_strength)
    
    # Calculate weighted average
    if factors:
        # Give more weight to price momentum and HA consistency
        weights = [0.4, 0.4, 0.2]  # HA consistency, price momentum, volume
        trend_strength = sum(f * w for f, w in zip(factors, weights))
        return min(trend_strength, 1.0)
    
    return 0.0

def get_volume_threshold(trend_strength):
    """Dynamic volume threshold based on trend strength"""
    if trend_strength > 0.7:
        return 1.0  # Strong trends need less volume confirmation
    elif trend_strength > 0.5:
        return 1.2  # Moderate trends need moderate volume
    else:
        return 1.5  # Weak trends need strong volume confirmation

def analyze_market_dynamic(df, ha_lookback=2, min_trend_strength=0.3):
    """Enhanced market analysis with dynamic volume thresholds"""
    try:
        # Convert to lowercase column names for consistency
        df_lower = df.rename(columns=str.lower)
        df_analysis = df_lower.copy()
        
        # Calculate Heikin Ashi
        ha_open, ha_high, ha_low, ha_close = calculate_heikin_ashi(df_analysis)
        df_analysis['ha_open'] = ha_open
        df_analysis['ha_close'] = ha_close
        df_analysis['ha_high'] = ha_high
        df_analysis['ha_low'] = ha_low
        
        # Calculate HA trend
        ha_trend = 0
        if len(df_analysis) >= ha_lookback + 1:
            bullish_count = 0
            bearish_count = 0
            for i in range(1, ha_lookback + 1):
                idx = -i
                if df_analysis['ha_close'].iloc[idx] > df_analysis['ha_open'].iloc[idx]:
                    bullish_count += 1
                elif df_analysis['ha_close'].iloc[idx] < df_analysis['ha_open'].iloc[idx]:
                    bearish_count += 1
            
            if bullish_count == ha_lookback:
                ha_trend = 1
            elif bearish_count == ha_lookback:
                ha_trend = -1
        
        # Check for HA doji
        ha_doji = abs(df_analysis['ha_close'].iloc[-1] - df_analysis['ha_open'].iloc[-1]) / (df_analysis['ha_high'].iloc[-1] - df_analysis['ha_low'].iloc[-1] + 1e-8) < 0.1
        
        # Calculate EMA trend
        ema_trend, ema_fast, ema_slow, ema_fast_prev, ema_slow_prev = calculate_ema_trend(df_analysis)
        
        # Detect candle patterns
        bullish_pattern, bearish_pattern = detect_candle_patterns(df_analysis)
        
        # Analyze volume
        recent_volume = df_analysis['volume'].tail(3).mean()
        avg_volume = df_analysis['volume'].tail(20).mean()
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Calculate trend strength
        trend_strength = calculate_trend_strength(df_analysis, ha_trend, ha_doji, volume_ratio)
        
        # Get dynamic volume threshold
        dynamic_volume_threshold = get_volume_threshold(trend_strength)
        volume_ok = volume_ratio >= dynamic_volume_threshold
        
        # Generate signal
        signal = "HOLD"
        reason = []
        
        # Check if trend strength meets minimum requirement
        if trend_strength >= min_trend_strength:
            
            # Bullish conditions (with dynamic volume)
            bullish_conditions = [
                ha_trend == 1,
                ema_trend == 1,
                bullish_pattern or trend_strength > 0.6,
                not ha_doji,
                volume_ok or trend_strength > 0.7  # Volume OR very strong trend
            ]
            
            # Bearish conditions (with dynamic volume)
            bearish_conditions = [
                ha_trend == -1,
                ema_trend == -1,
                bearish_pattern or trend_strength > 0.6,
                not ha_doji,
                volume_ok or trend_strength > 0.7  # Volume OR very strong trend
            ]
            
            if all(bullish_conditions):
                signal = "BUY"
                reason.append("All bullish conditions met with dynamic volume")
            elif all(bearish_conditions):
                signal = "SELL"
                reason.append("All bearish conditions met with dynamic volume")
            else:
                # Provide detailed reasons for holding
                if ha_trend == 1 and ema_trend == 1:
                    missing = []
                    if not (bullish_pattern or trend_strength > 0.6):
                        missing.append("no pattern/weak trend")
                    if ha_doji:
                        missing.append("HA doji")
                    if not (volume_ok or trend_strength > 0.7):
                        missing.append(f"volume ratio {volume_ratio:.2f} < {dynamic_volume_threshold}")
                    reason.append(f"Bullish setup missing: {', '.join(missing)}")
                elif ha_trend == -1 and ema_trend == -1:
                    missing = []
                    if not (bearish_pattern or trend_strength > 0.6):
                        missing.append("no pattern/weak trend")
                    if ha_doji:
                        missing.append("HA doji")
                    if not (volume_ok or trend_strength > 0.7):
                        missing.append(f"volume ratio {volume_ratio:.2f} < {dynamic_volume_threshold}")
                    reason.append(f"Bearish setup missing: {', '.join(missing)}")
                else:
                    reason.append("HA and EMA trends don't align")
        else:
            reason.append(f"Trend strength {trend_strength:.2f} < minimum {min_trend_strength}")
        
        return {
            'signal': signal,
            'ha_trend': ha_trend,
            'ema_trend': ema_trend,
            'bullish_pattern': bullish_pattern,
            'bearish_pattern': bearish_pattern,
            'ha_doji': ha_doji,
            'volume_ratio': volume_ratio,
            'volume_ok': volume_ok,
            'dynamic_volume_threshold': dynamic_volume_threshold,
            'trend_strength': trend_strength,
            'reason': '; '.join(reason),
            'current_price': df_analysis['close'].iloc[-1]
        }
        
    except Exception as e:
        return {
            'signal': 'HOLD',
            'reason': f'Error in analysis: {str(e)}',
            'current_price': 0
        }

def debug_detailed_analysis(data, point):
    """Perform detailed analysis debugging"""
    print(f"\n" + "-"*40)
    print(f"🧪 Testing at bar {point}: {data.index[point]}")
    print("-"*40)
    
    test_data = data.iloc[:point]
    analysis = analyze_market_dynamic(test_data)
    
    if analysis and 'signal' in analysis:
        print(f"🔍 DEBUG ANALYSIS - Data length: {len(test_data)}")
        print(f"   First date: {test_data.index[0]}")
        print(f"   Last date: {test_data.index[-1]}")
        print(f"   Current price: ${analysis.get('current_price', 0):.2f}")
        
        # Show key metrics
        print(f"\n📊 KEY METRICS:")
        print(f"   HA Trend: {analysis.get('ha_trend', 'N/A')}")
        print(f"   EMA Trend: {analysis.get('ema_trend', 'N/A')}")
        print(f"   Trend Strength: {analysis.get('trend_strength', 0):.2f}")
        print(f"   Volume Ratio: {analysis.get('volume_ratio', 0):.2f}")
        print(f"   Dynamic Volume Threshold: {analysis.get('dynamic_volume_threshold', 1.5):.1f}")
        print(f"   Volume OK (Dynamic): {analysis.get('volume_ok', False)}")
        print(f"   HA Doji: {analysis.get('ha_doji', False)}")
        print(f"   Bullish Pattern: {analysis.get('bullish_pattern', False)}")
        print(f"   Bearish Pattern: {analysis.get('bearish_pattern', False)}")
        
        print(f"\n🎯 SIGNAL GENERATION:")
        print(f"   Strategy Parameters:")
        print(f"     - Min Trend Strength: 0.3")
        print(f"     - Dynamic Volume: Enabled")
        
        if analysis['trend_strength'] >= 0.3:
            print(f"   ✅ TREND STRENGTH PASSED: {analysis['trend_strength']:.2f} >= 0.3")
            
            # Bullish conditions check
            bullish_conditions = [
                analysis.get('ha_trend') == 1,
                analysis.get('ema_trend') == 1,
                analysis.get('bullish_pattern') or analysis['trend_strength'] > 0.6,
                not analysis.get('ha_doji'),
                analysis.get('volume_ok') or analysis['trend_strength'] > 0.7
            ]
            
            print(f"\n   🔼 BULLISH CONDITIONS:")
            print(f"     {'✅' if bullish_conditions[0] else '❌'} HA Trend == 1: {bullish_conditions[0]}")
            print(f"     {'✅' if bullish_conditions[1] else '❌'} EMA Trend == 1: {bullish_conditions[1]}")
            print(f"     {'✅' if bullish_conditions[2] else '❌'} Bullish Pattern OR Strong Trend: {bullish_conditions[2]}")
            print(f"     {'✅' if bullish_conditions[3] else '❌'} Not HA Doji: {bullish_conditions[3]}")
            print(f"     {'✅' if bullish_conditions[4] else '❌'} Volume OK OR Very Strong Trend: {bullish_conditions[4]}")
            
            # Bearish conditions check
            bearish_conditions = [
                analysis.get('ha_trend') == -1,
                analysis.get('ema_trend') == -1,
                analysis.get('bearish_pattern') or analysis['trend_strength'] > 0.6,
                not analysis.get('ha_doji'),
                analysis.get('volume_ok') or analysis['trend_strength'] > 0.7
            ]
            
            print(f"\n   🔽 BEARISH CONDITIONS:")
            print(f"     {'✅' if bearish_conditions[0] else '❌'} HA Trend == -1: {bearish_conditions[0]}")
            print(f"     {'✅' if bearish_conditions[1] else '❌'} EMA Trend == -1: {bearish_conditions[1]}")
            print(f"     {'✅' if bearish_conditions[2] else '❌'} Bearish Pattern OR Strong Trend: {bearish_conditions[2]}")
            print(f"     {'✅' if bearish_conditions[3] else '❌'} Not HA Doji: {bearish_conditions[3]}")
            print(f"     {'✅' if bearish_conditions[4] else '❌'} Volume OK OR Very Strong Trend: {bearish_conditions[4]}")
            
        else:
            print(f"   ❌ TREND STRENGTH FAILED: {analysis['trend_strength']:.2f} < 0.3")
        
        print(f"\n   🎯 FINAL DECISION:")
        if analysis['signal'] != 'HOLD':
            print(f"   🎯 {analysis['signal']} SIGNAL GENERATED!")
            print(f"   💡 {analysis.get('reason', 'Signal conditions met')}")
        else:
            print(f"   ⏸️  NO CONDITIONS FULLY MET - HOLDING")
            if analysis.get('reason'):
                print(f"   💡 {analysis['reason']}")
        
        print(f"📊 Result: {analysis['signal']}")
        
        return analysis['signal'] != 'HOLD'
    
    else:
        print("❌ No analysis returned")
        return False

def main():
    print("🚀 Fixed Strategy with Dynamic Volume Thresholds - STANDALONE")
    print("=" * 60)
    
    # Test with our signal data
    test_files = [
        ('SPY Bullish Signal', 'data/historical/SPY_bullish_signal.csv'),
        ('SPY Bearish Signal', 'data/historical/SPY_bearish_signal.csv'),
        ('QQQ Bullish Signal', 'data/historical/QQQ_bullish_signal.csv'),
    ]
    
    for test_name, filepath in test_files:
        print(f"\n" + "="*60)
        print(f"🔍 DEBUGGING: {test_name}")
        print(f"📁 File: {filepath}")
        print("="*60)
        
        try:
            # Load data with flexible column handling
            data = pd.read_csv(filepath)
            
            # Handle different datetime column names
            datetime_col = None
            for col in data.columns:
                if 'time' in col.lower() or 'date' in col.lower():
                    datetime_col = col
                    break
            
            if datetime_col:
                data[datetime_col] = pd.to_datetime(data[datetime_col])
                data = data.set_index(datetime_col)
            else:
                # If no datetime column, use index
                data.index = pd.date_range(start='2024-01-10 09:30:00', periods=len(data), freq='1min')
            
            print(f"📊 Data columns: {list(data.columns)}")
            print(f"📊 Data shape: {data.shape}")
            
            # Test multiple points to find where signals trigger
            test_points = [100, 110, 120, 130, 140]
            signal_found = False
            
            for point in test_points:
                if point < len(data):
                    signal_found = debug_detailed_analysis(data, point)
                    if signal_found:
                        print(f"\n🎉 SIGNAL FOUND AT BAR {point}!")
                        break
                        
        except Exception as e:
            print(f"❌ Error testing {test_name}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n" + "="*60)
    print("🎯 DEBUGGING COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()