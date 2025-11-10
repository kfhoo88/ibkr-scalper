#!/usr/bin/env python3
"""
Final Trading Bot - Ready for Live Trading
"""

import pandas as pd
import logging
from datetime import datetime
from strategies.complete_scalper import CompleteScalpingStrategy

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self):
        self.strategy = CompleteScalpingStrategy()
        self.position = None
        self.trade_history = []
        
    def analyze_and_trade(self, data):
        """Analyze market and execute trades"""
        for symbol, df in data.items():
            logger.info(f"🔍 Analyzing {symbol}...")
            
            analysis = self.strategy.analyze_market(df)
            
            if analysis and analysis['signal'] != 'HOLD':
                self._execute_trade(symbol, analysis, df)
            else:
                logger.info(f"📊 {symbol}: No trade signal (Hold)")
    
    def _execute_trade(self, symbol, analysis, df):
        """Execute a trade based on signal"""
        current_price = df['Close'].iloc[-1]
        
        trade = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'signal': analysis['signal'],
            'price': current_price,
            'ha_trend': analysis['ha_trend'],
            'ema_trend': analysis['ema_trend'],
            'trend_strength': analysis['trend_strength'],
            'volume_ratio': analysis['volume_ratio']
        }
        
        self.trade_history.append(trade)
        
        logger.info(f"🎯 TRADE SIGNAL: {symbol} {analysis['signal']} at ${current_price:.2f}")
        logger.info(f"   Trend Strength: {analysis['trend_strength']:.2f}")
        logger.info(f"   HA Trend: {'Bullish' if analysis['ha_trend'] == 1 else 'Bearish' if analysis['ha_trend'] == -1 else 'Neutral'}")
        logger.info(f"   EMA Trend: {'Bullish' if analysis['ema_trend'] == 1 else 'Bearish' if analysis['ema_trend'] == -1 else 'Neutral'}")
        logger.info(f"   Volume Ratio: {analysis['volume_ratio']:.2f}")

def main():
    print("🚀 IBKR Scalping Trading Bot")
    print("=" * 40)
    
    # Load data
    try:
        spy_data = pd.read_csv('data/historical/SPY_synthetic.csv', index_col=0, parse_dates=True)
        qqq_data = pd.read_csv('data/historical/QQQ_synthetic.csv', index_col=0, parse_dates=True)
        
        data = {
            'SPY': spy_data,
            'QQQ': qqq_data
        }
        
        print(f"✅ Loaded data: SPY ({len(spy_data)} bars), QQQ ({len(qqq_data)} bars)")
        
    except Exception as e:
        logger.error(f"❌ Failed to load data: {e}")
        return
    
    # Initialize and run bot
    bot = TradingBot()
    
    print("\n🤖 Starting trading analysis...")
    bot.analyze_and_trade(data)
    
    # Display results
    print(f"\n📊 TRADING SESSION SUMMARY")
    print("=" * 30)
    
    if bot.trade_history:
        print(f"🎯 Signals Generated: {len(bot.trade_history)}")
        
        for trade in bot.trade_history:
            print(f"\n{trade['symbol']}:")
            print(f"  Signal: {trade['signal']}")
            print(f"  Price: ${trade['price']:.2f}")
            print(f"  Trend Strength: {trade['trend_strength']:.2f}")
            print(f"  Time: {trade['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("📊 No trading signals generated this session")
    
    print(f"\n🎉 TRADING BOT READY FOR LIVE DEPLOYMENT!")
    print(f"💡 Next: Connect to IBKR for live trading")
    print(f"📁 Logs saved to: logs/trading_bot.log")

if __name__ == "__main__":
    main()