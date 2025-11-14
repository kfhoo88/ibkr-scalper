import pandas as pd
import pytz

print("=== TIMEZONE REALITY CHECK ===")
print(f"Singapore time now: {pd.Timestamp.now(tz='Asia/Singapore')}")
print(f"New York time now: {pd.Timestamp.now(tz='US/Eastern')}")

# Read CSV with pandas import
df = pd.read_csv('../data/historical/SPY_IBKR_1min_1year_20251110.csv', nrows=50000)

print(f"\n=== CSV COLUMN ANALYSIS ===")
print(f"Columns in CSV: {df.columns.tolist()}")
print(f"First few rows:")
print(df.head(3))

print(f"\n=== LOADING DATA ===")
print(f"Loaded {len(df)} rows from CSV")

# Use the "date" column for timestamps
print(f"Using timestamp column: 'date'")
print(f"Date range: {df['date'].iloc[0]} to {df['date'].iloc[-1]}")

# Show raw datetime info
sample_dt = pd.to_datetime(df['date'].iloc[0])
print(f"First timestamp (naive): {sample_dt}")
print(f"Has timezone: {sample_dt.tz}")

# CRITICAL: Localize naive timestamps as Eastern Time
df['datetime_et'] = pd.to_datetime(df['date']).dt.tz_localize('US/Eastern')

print(f"\n=== AFTER TIMEZONE FIX ===")
print(f"First timestamp: {df['datetime_et'].iloc[0]}")
print(f"Last timestamp: {df['datetime_et'].iloc[-1]}")
print(f"Timezone: {df['datetime_et'].iloc[0].tz}")

# Verify some trading hours
print(f"\n=== TRADING HOURS VERIFICATION ===")
sample_times = df['datetime_et'].head(5)
for time in sample_times:
    print(f"{time} - {time.tz}")
    
print("==============================")