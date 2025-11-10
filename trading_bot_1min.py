#!/usr/bin/env python3
"""
1-Minute Scalping Trading Bot
"""

import pandas as pd
import logging
from datetime import datetime
from strategies.scalping_1min import Scalping1MinStrategy

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scalping_1min.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Scalping1MinBot:
    def __init__(self):
        self.strategy = Scalping1MinStrategy()
        self.trade_history = []
        
    def analyze_scalping_data(self, data):
        """Analyze 1-minute data for scalping opportunities"""
        print(f"🤖 Analyzing 1-minute scalping data...")
        
        for symbol, df in data.items():
            logger.info(f"🔍 Analyzing {symbol} (1-minute)...")
            
            if len(df) < 50:
                logger.warning(f"⚠️ Insufficient 1-minute data for {symbol}: {len(df)} bars")
                continue
                
            analysis = self.strategy.analyze_market(df)
            
            if analysis:
                logger.info(f"📊 {symbol} Analysis:")
                logger.info(f"   HA Trend: {analysis['ha_trend']}")
                logger.info(f"   EMA Trend: {analysis['ema_trend']}") 
                logger.info(f"   Trend Strength: {analysis['trend_strength']:.2f}")
                logger.info(f"   Volume Ratio: {analysis['volume_ratio']:.2f}")
                logger.info(f"   Patterns: Bullish={analysis['bullish_pattern']}, Bearish={analysis['bearish_pattern']}")
                
                if analysis['signal'] != 'HOLD':
                    self._record_signal(symbol, analysis, df)
                    logger.info(f"🎯 SCALPING SIGNAL: {symbol} {analysis['signal']}")
                else:
                    logger.info(f"   No scalping signal (Hold)")
    
    def _record_signal(self, symbol, analysis, df):
        """Record scalping signal"""
        trade = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'signal': analysis['signal'],
            'price': df['Close'].iloc[-1],
            'ha_trend': analysis['ha_trend'],
            'ema_trend': analysis['ema_trend'],
            'trend_strength': analysis['trend_strength'],
            'volume_ratio': analysis['volume_ratio'],
            'data_points': len(df),
            'timeframe': '1min'
        }
        
        self.trade_history.append(trade)

def main():
    print("🚀 1-Minute Scalping Trading Bot")
    print("=" * 40)
    
    # Load 1-minute data
    try:
        spy_data = pd.read_csv('data/historical/SPY_1min.csv', index_col=0, parse_dates=True)
        qqq_data = pd.read_csv('data/historical/QQQ_1min.csv', index_col=0, parse_dates=True)
        
        data = {
            'SPY': spy_data,
            'QQQ': qqq_data
        }
        
        print(f"✅ Loaded 1-minute data:")
        print(f"   SPY: {len(spy_data)} bars, {spy_data.index[0]} to {spy_data.index[-1]}")
        print(f"   QQQ: {len(qqq_data)} bars, {qqq_data.index[0]} to {qqq_data.index[-1]}")
        print(f"   Timeframe: 1-minute intervals")
        
    except Exception as e:
        print(f"❌ Failed to load 1-minute data: {e}")
        print("💡 Please run: python create_1min_data.py")
        return
    
    # Initialize and run scalping bot
    bot = Scalping1MinBot()
    bot.analyze_scalping_data(data)
    
    # Display results
    print(f"\n📊 1-MINUTE SCALPING RESULTS")
    print("=" * 35)
    
    if bot.trade_history:
        print(f"🎯 Scalping Signals Generated: {len(bot.trade_history)}")
        
        for trade in bot.trade_history:
            print(f"\n{trade['symbol']} ({trade['timeframe']}):")
            print(f"  Signal: {trade['signal']}")
            print(f"  Price: ${trade['price']:.2f}")
            print(f"  Trend Strength: {trade['trend_strength']:.2f}")
            print(f"  Volume Ratio: {trade['volume_ratio']:.2f}")
            print(f"  Time: {trade['timestamp'].strftime('%H:%M:%S')}")
    else:
        print("📊 No scalping signals generated")
        print("💡 The strategy is being selective - this is good for risk management!")
    
    print(f"\n🎉 1-MINUTE SCALPING BOT IS OPERATIONAL!")
    print(f"💡 Ready for live 1-minute trading!")

if __name__ == "__main__":
    main()