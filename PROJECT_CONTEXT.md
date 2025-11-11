# PROJECT CONTEXT - SPY/QQQ 0DTE Options Scalping

## 🎯 CURRENT FOCUS: VWAP + MA Simple Scalping System
**Last Updated**: 11 nov 2025
**Status**: ACTIVE DEVELOPMENT - Phase 1 Backtesting

## STRATEGY DECISION
✅ **ACTIVE**: Simple VWAP + Moving Average System  
❌ **ABANDONED**: Complex Heiken Ashi multi-indicator system

## CORE STRATEGY RULES

### Entry Conditions:
**LONG (Call Options):**
- MA9 > MA21 (uptrend)
- Price above VWAP  
- After pullback (1+ red candles)
- Green candle closes above MA9 → BUY CALL

**SHORT (Put Options):**
- MA9 < MA21 (downtrend)
- Price below VWAP
- After pullback (1+ green candles) 
- Red candle closes below MA9 → BUY PUT

### Trading Parameters:
- **Instruments**: SPY/QQQ 0DTE options, ~0.40 delta
- **Position**: 1 contract (~$150-200)
- **Profit Target**: 20%
- **Max Loss**: 50% with hedge at 25%
- **Daily Trades**: 4-5 max

### Trading Hours:
- 9:35-11:00 EST (avoid first 5 mins)
- 1:30-3:30 EST (avoid last 30 mins)

## DEVELOPMENT ROADMAP

### Phase 1 (CURRENT): Simple Backtesting
- VWAP+MA core strategy
- Volatility-based option pricing
- Basic market filters (ATR, volume)
- Accurate win rate validation

### Phase 2: Enhanced Features
- Hedge mechanism
- Advanced filters
- IBKR integration ready

### Phase 3: Live Trading
- Real-time execution
- Performance monitoring
- Scaling to multi-contract

## TECHNICAL SPECS
- **Data**: Existing 1-min SPY/QQQ data (2024-2025)
- **Pricing**: Volatility-based using historical vol
- **Focus**: Realistic backtesting before live trading

## SUCCESS METRICS
- Win rate > 65%
- Daily profit: $150-200 (Phase 1)  
- Monthly target: $20,000 (scaled)
- Simple, testable, iterative development
