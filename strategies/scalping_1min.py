#!/usr/bin/env python3
"""
1-Minute Scalping Strategy - Optimized for 1-minute timeframe
"""

from strategies.complete_scalper import CompleteScalpingStrategy

class Scalping1MinStrategy(CompleteScalpingStrategy):
    """Scalping strategy optimized for 1-minute timeframe"""
    
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
    
    def _calculate_trend_strength(self, ha_df, regular_df):
        """Trend strength calculation optimized for 1-minute"""
        strength_factors = []
        
        # 1-minute: Focus on recent momentum (last 5-10 bars)
        lookback = min(10, len(ha_df))
        
        if lookback >= 5:
            # HA consistency (last 5 bars)
            recent_ha = ha_df.tail(5)
            ha_bullish = sum(recent_ha['HA_Close'] > recent_ha['HA_Open'])
            ha_strength = abs(ha_bullish - 2.5) / 2.5
            strength_factors.append(ha_strength)
            
            # Price momentum (last 10 bars)
            if len(regular_df) >= 10:
                recent_prices = regular_df['Close'].tail(10)
                price_change = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]
                # For 1-minute, smaller moves are significant
                momentum_strength = min(abs(price_change) * 1000, 1.0)  # Amplified for small moves
                strength_factors.append(momentum_strength)
            
            # Volume spike detection
            if len(regular_df) >= 20:
                recent_volume = regular_df['Volume'].tail(5).mean()
                avg_volume = regular_df['Volume'].tail(20).mean()
                if avg_volume > 0:
                    volume_strength = min(recent_volume / avg_volume / 3, 1.0)  # Normalize
                    strength_factors.append(volume_strength)
        
        return sum(strength_factors) / len(strength_factors) if strength_factors else 0
    
    def _generate_signal(self, signals):
        """Signal generation optimized for 1-minute scalping"""
        if signals['trend_strength'] < self.min_trend_strength:
            return 'HOLD'
        
        # For 1-minute, we can be slightly less strict about patterns
        # but require stronger volume confirmation
        
        bullish_conditions = (
            signals['ha_trend'] == 1 and
            signals['ema_trend'] == 1 and
            (signals['bullish_pattern'] or signals['trend_strength'] > 0.6) and  # Pattern OR strong trend
            not signals['ha_doji'] and
            signals['volume_ok']
        )
        
        bearish_conditions = (
            signals['ha_trend'] == -1 and
            signals['ema_trend'] == -1 and
            (signals['bearish_pattern'] or signals['trend_strength'] > 0.6) and  # Pattern OR strong trend
            not signals['ha_doji'] and
            signals['volume_ok']
        )
        
        if bullish_conditions:
            return 'BUY_CALL'
        elif bearish_conditions:
            return 'BUY_PUT'
        else:
            return 'HOLD'