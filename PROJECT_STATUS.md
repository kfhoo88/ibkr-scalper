# SPY/QQQ Scalping Project - Status Tracker

## 🎯 ULTIMATE GOAL
$20k/month profit trading SPY/QQQ OPTIONS only

## 🔄 CURRENT TESTING APPROACH
- Testing entry signals on SHARES data (SPY/QQQ) with options conversion
- Using 1-year historical 1-minute data for backtesting
- Focus: Achieve >60% win rate on shares first, then scale to options

## ⚡ CURRENT STRATEGY VERSION
**Breakout Strategy with Dynamic Support/Resistance**
- **Entry:** Break above/below 5-period high/low with MA trend confirmation
- **Filters:** Candle color alignment, MA distance limit (<$0.20), volume confirmation
- **SL:** Previous candle extreme (testing)
- **TP:** 1.5× ATR target

## 📊 LATEST RESULTS (Pre-Breakout Strategy)
SHARES PERFORMANCE:

SPY: 447 trades, 32.7% win rate, +$920.45 total

QQQ: 380 trades, 30.3% win rate, -$2,099.00 total

Total Portfolio: -$1,178.55

OPTIONS CONVERSION (BROKEN):

SPY: -$12,945 total (-$28.96/trade)

QQQ: -$21,235 total (-$55.88/trade)


## ✅ RECENT ACHIEVEMENTS
- **Fixed P&L calculation** (was showing impossible losses)
- **Improved win rate** from 0% to 32% with strategic filters
- **Identified critical issues** with stop loss consistency
- **Added comprehensive debug logging** for trade analysis
- **Discovered promising alternative strategies** in sample code

## 🔧 CURRENT DEVELOPMENT FOCUS
**Testing Breakout Strategy Implementation:**
- Dynamic 5-period support/resistance levels
- Breakout entries instead of MA crossovers
- Maintaining proven filters (candle color, MA distance, volume)

## 🐛 CRITICAL ISSUES IDENTIFIED
1. **Stop Loss Inconsistency** - Previous candle SL causes wild variations ($0.65 to $98.65)
2. **QQQ Underperformance** - Same strategy works on SPY but fails on QQQ
3. **Options Conversion Broken** - Losing 28x more than shares (math error)
4. **Timezone Display Issues** - Local time conversion makes trades appear outside hours

## 📁 CRITICAL WORKING FILES
- `vwap_ma_strategy/backtester/engine.py` - MAIN TRADING ENGINE
- `vwap_ma_strategy/config/vwap_ma_config.yaml` - PARAMETERS
- `vwap_ma_strategy/main_clean.py` - TEST RUNNER
- `sample/Easy_AlgoTrading_Strategy.ipynb` - REFERENCE STRATEGIES

## 🚀 IMMEDIATE NEXT STEPS
1. **Test breakout strategy** (just implemented)
2. **If win rate improves**, implement ATR-based SL/TP from sample strategy
3. **Analyze QQQ vs SPY differences** for strategy optimization
4. **Fix options conversion math** once base strategy is solid

## 💡 KEY INSIGHTS & LEARNING
- **Candle color alignment** crucial for entry quality
- **MA distance filters** prevent overextended entries
- **Breakout strategies** often outperform reversal strategies
- **Consistent risk management** more important than entry timing

## ⚠️ RECENTLY FIXED BUGS
- **Column name case sensitivity** ('high' vs 'High')
- **Market hours timezone issues** causing immediate exits
- **Missing pnl_pct field** in trade dictionary

## 📈 SUCCESS METRICS GOING FORWARD
- [ ] Win rate > 60% on shares (current: 32%)
- [ ] Consistent profitability on both SPY and QQQ
- [ ] Options conversion showing realistic scaling
- [ ] Stop loss consistency across all trades

## 🔄 LAST MAJOR UPDATE
Implemented breakout strategy with 5-period dynamic support/resistance levels

