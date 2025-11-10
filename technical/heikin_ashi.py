import pandas as pd
import numpy as np

class HeikinAshi:
    @staticmethod
    def calculate_heikin_ashi(df):
        """Convert regular OHLC to Heikin Ashi OHLC"""
        ha_df = df.copy()
        
        # Heikin Ashi calculations
        ha_df['HA_Close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        
        # Initialize HA_Open
        ha_df['HA_Open'] = (df['open'] + df['close']) / 2
        for i in range(1, len(ha_df)):
            ha_df.loc[ha_df.index[i], 'HA_Open'] = (
                ha_df.loc[ha_df.index[i-1], 'HA_Open'] + 
                ha_df.loc[ha_df.index[i-1], 'HA_Close']
            ) / 2
        
        ha_df['HA_High'] = ha_df[['high', 'HA_Open', 'HA_Close']].max(axis=1)
        ha_df['HA_Low'] = ha_df[['low', 'HA_Open', 'HA_Close']].min(axis=1)
        
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
            return 1
        elif bearish_count > bullish_count:
            return -1
        else:
            return 0
    
    @staticmethod
    def is_ha_doji(ha_df, threshold=0.1):
        """Detect Doji patterns in Heikin Ashi"""
        if len(ha_df) == 0:
            return False
            
        recent = ha_df.iloc[-1]
        body_size = abs(recent['HA_Close'] - recent['HA_Open'])
        total_range = recent['HA_High'] - recent['HA_Low']
        
        if total_range == 0:
            return False
            
        return (body_size / total_range) < threshold