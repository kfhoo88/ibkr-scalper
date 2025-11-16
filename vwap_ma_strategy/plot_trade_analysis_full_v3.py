def load_trade_data(self, symbol):
    """Load saved trade data - PROPER FIX"""
    filename = f'trade_data_{symbol}.pkl'
    try:
        trades_df = pd.read_pickle(filename)
        print(f"✅ Loaded {len(trades_df)} {symbol} trades")
        
        # DEBUG: Check what we're dealing with
        print(f"🔍 entry_time dtype: {trades_df['entry_time'].dtype}")
        print(f"🔍 sample entry_time: {trades_df['entry_time'].iloc[0]} (type: {type(trades_df['entry_time'].iloc[0])})")
        
        # Method 1: If it's already datetime with timezone
        if hasattr(trades_df['entry_time'].dtype, 'tz'):
            print("🕒 Converting timezone-aware datetime to naive...")
            trades_df['entry_time'] = trades_df['entry_time'].dt.tz_convert('US/Eastern').dt.tz_localize(None)
            trades_df['exit_time'] = trades_df['exit_time'].dt.tz_convert('US/Eastern').dt.tz_localize(None)
        # Method 2: If it's string or object
        else:
            print("📅 Converting to datetime...")
            trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time']).dt.tz_localize(None)
            trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time']).dt.tz_localize(None)
            
        print(f"🔍 After conversion: {trades_df['entry_time'].iloc[0]} (type: {type(trades_df['entry_time'].iloc[0])})")
        return trades_df
    except Exception as e:
        print(f"❌ Error loading {symbol} trade data: {e}")
        import traceback
        traceback.print_exc()
        return None

def load_price_data(self, symbol):
    """Load historical price data - PROPER FIX"""
    filename = f"../data/historical/{symbol}_IBKR_1min_1year_20251110.csv"
    try:
        df = pd.read_csv(filename)
        print(f"🔍 Price data date dtype: {df['date'].dtype}")
        
        df['date'] = pd.to_datetime(df['date'])
        
        # If price data has timezone, remove it
        if hasattr(df['date'].dtype, 'tz'):
            df['date'] = df['date'].dt.tz_localize(None)
            
        df = df.set_index('date')
        column_map = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}
        result = df.rename(columns=column_map)[['Open', 'High', 'Low', 'Close', 'Volume']]
        print(f"🔍 Price index after: {result.index.dtype}")
        return result
    except Exception as e:
        print(f"❌ Error loading price data: {e}")
        import traceback
        traceback.print_exc()
        return None