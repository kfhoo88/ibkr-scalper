import pandas as pd
import requests
from io import StringIO

# Load the CSV directly from GitHub
url = "https://raw.githubusercontent.com/kfhoo88/ibkr-scalper/main/vwap_ma_strategy/comprehensive_optimization_20251116_070427.csv"
response = requests.get(url)
df = pd.read_csv(StringIO(response.text))

print("📊 FULL DATASET ANALYSIS")
print(f"Total tests: {len(df)}")
print(f"Tests with 100+ trades: {len(df[df['total_trades'] > 100])}")
print(f"Tests with 500+ trades: {len(df[df['total_trades'] > 500])}")
print()

# Show column names to see the actual structure
print("📋 COLUMN NAMES:")
print(df.columns.tolist())
print()

# Filter for robust parameters (high trade count)
robust_df = df[df['total_trades'] > 100].copy()

# Calculate composite score (70% win rate, 30% profit factor)
robust_df['score'] = (
    robust_df['win_rate'] * 0.7 + 
    (robust_df['profit_factor'].clip(upper=5) * 20) * 0.3
)

# Get top 20 robust parameters
top_robust = robust_df.nlargest(20, 'score')

print("🏆 TOP 10 ROBUST PARAMETERS (High Trade Count)")
print("="*100)

# Print the first row to see the actual parameter structure
first_row = top_robust.iloc[0]
print("First row sample:")
for col in top_robust.columns:
    if 'params' in col or col in ['win_rate', 'total_trades', 'total_pnl', 'profit_factor']:
        print(f"  {col}: {first_row[col]}")
print()

# Now print top parameters using correct column names
for i, (_, row) in enumerate(top_robust.head(10).iterrows(), 1):
    # Extract parameters from the nested structure
    params = eval(row['params']) if isinstance(row['params'], str) else row['params']
    
    print(f"{i:2d}. Win Rate: {row['win_rate']:5.1f}% | "
          f"Profit Factor: {row['profit_factor']:4.2f} | "
          f"Trades: {row['total_trades']:3d} | "
          f"Total PnL: ${row['total_pnl']:7.0f} | "
          f"EMA: {params.get('ema_length', 'N/A'):2} | "
          f"EMA_Back: {params.get('ema_backcandles', 'N/A'):2} | "
          f"HL_Back: {params.get('hl_backcandles', 'N/A'):2} | "
          f"ATR_Mult: {params.get('atr_multiplier', 'N/A'):3.1f} | "
          f"TP_Mult: {params.get('tp_multiplier', 'N/A'):3.1f}")

print(f"\n📈 STATISTICS FOR ROBUST PARAMETERS (>100 trades):")
print(f"Average Win Rate: {robust_df['win_rate'].mean():.1f}%")
print(f"Average Trades: {robust_df['total_trades'].mean():.0f}")
print(f"Average PnL: ${robust_df['total_pnl'].mean():.0f}")

# Find best high-frequency parameters (500+ trades)
high_freq = df[df['total_trades'] > 500].nlargest(5, 'win_rate')
print(f"\n🎯 BEST HIGH-FREQUENCY PARAMETERS (500+ trades):")
print("="*100)
for i, (_, row) in enumerate(high_freq.iterrows(), 1):
    params = eval(row['params']) if isinstance(row['params'], str) else row['params']
    print(f"{i:2d}. Win Rate: {row['win_rate']:5.1f}% | "
          f"Trades: {row['total_trades']:3d} | "
          f"Total PnL: ${row['total_pnl']:7.0f} | "
          f"EMA: {params.get('ema_length', 'N/A'):2} | "
          f"EMA_Back: {params.get('ema_backcandles', 'N/A'):2} | "
          f"HL_Back: {params.get('hl_backcandles', 'N/A'):2} | "
          f"ATR_Mult: {params.get('atr_multiplier', 'N/A'):3.1f} | "
          f"TP_Mult: {params.get('tp_multiplier', 'N/A'):3.1f}")