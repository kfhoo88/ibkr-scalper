import pandas as pd
import pytz

print("=== TIMEZONE REALITY CHECK ===")
print(f"Singapore time now: {pd.Timestamp.now(tz='Asia/Singapore')}")
print(f"New York time now: {pd.Timestamp.now(tz='US/Eastern')}")

# Read CSV with pandas import
df = pd.read_csv('../data/historical/SPY_IBKR_1min_1year_20251110.csv', nrows=50000)

print(f"\n=== CSV COLUMN ANALYSIS ===")
print(f"Columns in CSV: {df.columns.tolist()}")

print(f"\n=== LOADING DATA ===")
print(f"Loaded {len(df)} rows from CSV")

# Convert string to proper timezone-aware datetime with utc=True
df['datetime_et'] = pd.to_datetime(df['date'], utc=True).dt.tz_convert('US/Eastern')

print(f"\n=== AFTER PROPER CONVERSION ===")
print(f"First timestamp: {df['datetime_et'].iloc[0]}")
print(f"Last timestamp: {df['datetime_et'].iloc[-1]}")
print(f"Timezone: {df['datetime_et'].iloc[0].tz}")

# Verify some trading hours
print(f"\n=== TRADING HOURS VERIFICATION ===")
sample_times = df['datetime_et'].head(5)
for time in sample_times:
    print(f"{time} - {time.tz}")

# Test trading hours filter
print(f"\n=== TRADING HOURS FILTER TEST ===")
def is_trading_hour(dt_et):
    """Check if datetime is within trading hours (9:35-16:00 ET)"""
    time_val = dt_et.time()
    morning_start = pd.Timestamp("09:35:00").time()
    morning_end = pd.Timestamp("16:00:00").time()
    return morning_start <= time_val <= morning_end

trading_hours_count = df[df['datetime_et'].apply(is_trading_hour)].shape[0]
print(f"Rows within trading hours (9:35-16:00): {trading_hours_count}/{len(df)}")
    
print("==============================")