# SPY/QQQ OPTIONS SCALPING SYSTEM

## PROJECT STATUS
**Current Phase:** Full Refactor Complete - Ready for Testing  
**System Status:** ✅ Operational

## CORE FILES
- 'main.py' - Single entry point
- 'core/options_scalper.py' - HA+MA + Candlestick strategy
- 'core/trade_manager.py' - Rolling & risk management
- 'core/backtester.py' - Options backtesting
- 'config/scalping_config.yaml' - All parameters

## STRATEGY
- **Direction:** Heikin Ashi + Moving Averages
- **Execution:** Candlestick patterns  
- **Trading:** SPY/QQQ Calls/Puts only
- **Risk:** 50% stop loss, hedge at 40%
- **Profit Taking:** Rolling to lower delta

## TARGET
,000/month through scalable options scalping

## CONTINUATION
Say: 'Continue SPY/QQQ scalping project'
Repo: https://github.com/kfhoo88/ibkr-scalper

## QUICK START
python main.py
