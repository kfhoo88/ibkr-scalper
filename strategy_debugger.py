#!/usr/bin/env python3
"""
Debug Strategy Conditions in Detail
"""

import pandas as pd
import logging
from strategies.scalping_1min import Scalping1MinStrategy

# Setup detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DebugScalpingStrategy(Scalping1MinStrategy):
    """Strategy with detailed debugging"""
    
    def analyze_market(self, df):
        """Analyze market with detailed debugging"""
        print(f"\n🔍 DEBUG ANALYSIS - Data length: {len(df)}")
        
        if len(df) < 50:
            print("❌ Insufficient data for analysis")
            return None
        
        try:
            # Calculate Heikin Ashi with debug
            ha_df = self.ha_calculator.calculate_heikin_ashi(df)
            print(f"📊 Heikin Ashi calculated: {len(ha_df)} bars")
            
            # Calculate EMAs with debug
            ema_df = self.calculate_emas(df)
            print(f"📊 EMAs calculated: Fast={ema_df['EMA_Fast'].iloc[-1]:.2f}, Slow={ema_df['EMA_Slow'].iloc[-1]:.2f}")
            
            # Get individual signals with debug
            ha_trend = self.ha_calculator.get_ha_trend(ha_df, self.ha_lookback)
            ha_doji = self.ha_calculator.is_ha_doji(ha_df)
            ema_trend = self.get_ema_trend(ema_df)
            
            print(f"🎯 INDICATOR VALUES:")
            print(f"   HA Trend: {ha_trend} (1=Bullish, -1=Bearish, 0=Neutral)")
            print(f"   EMA Trend: {ema_trend} (1=Bullish, -1=Bearish, 0=Neutral)")
            print(f"   HA Doji: {ha_doji}")
            
            # Pattern detection
            bullish_pattern = self.pattern_detector.bullish_engulfing(df)
            bearish_pattern = self.pattern_detector.bearish_engulfing(df)
            print(f"   Bullish Pattern: {bullish_pattern}")
            print(f"   Bearish Pattern: {bearish_pattern}")
            
            # Volume analysis
            volume_ok, volume_ratio = self._check_volume(df)
            print(f"   Volume Ratio: {volume_ratio:.2f} (Need > {self.volume_threshold})")
            print(f"   Volume OK: {volume_ok}")
            
            # Trend strength
            trend_strength = self._calculate_trend_strength(ha_df, df)
            print(f"   Trend Strength: {trend_strength:.2f} (Need > {self.min_trend_strength})")
            
            # Generate final signal with condition breakdown
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
            return None
    
    def _generate_signal_debug(self, signals):
        """Generate signal with detailed condition debugging"""
        print(f"\n🎯 SIGNAL GENERATION DEBUG:")
        
        # Check trend strength first
        if signals['trend_strength'] < self.min_trend_strength:
            print(f"   ❌ Trend strength {signals['trend_strength']:.2f} < {self.min_trend_strength}")
            return 'HOLD'
        else:
            print(f"   ✅ Trend strength {signals['trend_strength']:.2f} >= {self.min_trend_strength}")
        
        # Bullish conditions
        bullish_conditions = []
        bullish_conditions.append(f"HA Trend == 1: {signals['ha_trend'] == 1}")
        bullish_conditions.append(f"EMA Trend == 1: {signals['ema_trend'] == 1}")
        bullish_conditions.append(f"Bullish Pattern or Strong Trend: {signals['bullish_pattern'] or signals['trend_strength'] > 0.6}")
        bullish_conditions.append(f"Not HA Doji: {not signals['ha_doji']}")
        bullish_conditions.append(f"Volume OK: {signals['volume_ok']}")
        
        bullish_all_met = all([
            signals['ha_trend'] == 1,
            signals['ema_trend'] == 1,
            (signals['bullish_pattern'] or signals['trend_strength'] > 0.6),
            not signals['ha_doji'],
            signals['volume_ok']
        ])
        
        print(f"   🔼 BULLISH CONDITIONS:")
        for condition in bullish_conditions:
            print(f"      {condition}")
        print(f"   🔼 ALL BULLISH MET: {bullish_all_met}")
        
        # Bearish conditions
        bearish_conditions = []
        bearish_conditions.append(f"HA Trend == -1: {signals['ha_trend'] == -1}")
        bearish_conditions.append(f"EMA Trend == -1: {signals['ema_trend'] == -1}")
        bearish_conditions.append(f"Bearish Pattern or Strong Trend: {signals['bearish_pattern'] or signals['trend_strength'] > 0.6}")
        bearish_conditions.append(f"Not HA Doji: {not signals['ha_doji']}")
        bearish_conditions.append(f"Volume OK: {signals['volume_ok']}")
        
        bearish_all_met = all([
            signals['ha_trend'] == -1,
            signals['ema_trend'] == -1,
            (signals['bearish_pattern'] or signals['trend_strength'] > 0.6),
            not signals['ha_doji'],
            signals['volume_ok']
        ])
        
        print(f"   🔽 BEARISH CONDITIONS:")
        for condition in bearish_conditions:
            print(f"      {condition}")
        print(f"   🔽 ALL BEARISH MET: {bearish_all_met}")
        
        if bullish_all_met:
            print("   🎯 GENERATING BUY_CALL SIGNAL!")
            return 'BUY_CALL'
        elif bearish_all_met:
            print("   🎯 GENERATING BUY_PUT SIGNAL!")
            return 'BUY_PUT'
        else:
            print("   ❌ No conditions met - HOLD")
            return 'HOLD'

def main():
    print("🚀 Strategy Condition Debugger")
    print("=" * 35)
    
    # Test with our signal data
    test_files = [
        'data/historical/SPY_bullish_signal.csv',
        'data/historical/SPY_bearish_signal.csv',
        'data/historical/SPY_1min.csv'  # Original data for comparison
    ]
    
    strategy = DebugScalpingStrategy()
    
    for filepath in test_files:
        print(f"\n" + "="*50)
        print(f"🔍 DEBUGGING: {filepath}")
        print("="*50)
        
        try:
            data = pd.read_csv(filepath, index_col=0, parse_dates=True)
            
            if len(data) >= 120:
                # Test at the pattern point
                test_data = data.iloc[:120]
                analysis = strategy.analyze_market(test_data)
                
                if analysis:
                    print(f"\n🎯 FINAL RESULT: {analysis['signal']}")
                else:
                    print("❌ No analysis returned")
            else:
                print("⚠️ Not enough data")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()