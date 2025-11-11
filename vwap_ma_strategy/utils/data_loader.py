# vwap_ma_strategy/utils/data_loader.py
import pandas as pd
import os
import logging
import glob

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, data_path):
        self.data_path = data_path
    
    def load_symbol_data(self, symbol):
        """Load historical data for a symbol"""
        try:
            # Try multiple filename patterns
            patterns = [
                f"{symbol}_IBKR_1min_1year_20251110.csv",
                f"{symbol}_IBKR_1min_1year20251110.csv",
                f"{symbol}_IBKR_1min_*.csv"
            ]
            
            for pattern in patterns:
                file_path = os.path.join(self.data_path, pattern)
                matching_files = glob.glob(file_path)
                
                if matching_files:
                    actual_file = matching_files[0]
                    df = pd.read_csv(actual_file)
                    
                    # Handle different datetime column names
                    datetime_columns = ['datetime', 'date', 'time', 'timestamp']
                    found_datetime_col = None
                    
                    for col in datetime_columns:
                        if col in df.columns:
                            found_datetime_col = col
                            break
                    
                    if found_datetime_col:
                        df['datetime'] = pd.to_datetime(df[found_datetime_col])
                        df.set_index('datetime', inplace=True)
                        
                        # Standardize column names
                        column_mapping = {
                            'open': 'open', 'Open': 'open', 'OPEN': 'open',
                            'high': 'high', 'High': 'high', 'HIGH': 'high', 
                            'low': 'low', 'Low': 'low', 'LOW': 'low',
                            'close': 'close', 'Close': 'close', 'CLOSE': 'close',
                            'volume': 'volume', 'Volume': 'volume', 'VOLUME': 'volume'
                        }
                        
                        for old_col, new_col in column_mapping.items():
                            if old_col in df.columns and new_col not in df.columns:
                                df[new_col] = df[old_col]
                        
                        logger.info(f"Loaded {len(df)} rows for {symbol} from {os.path.basename(actual_file)}")
                        return df
                    else:
                        logger.error(f"No datetime column found in {actual_file}. Columns: {df.columns.tolist()}")
                        return None
            
            logger.error(f"No data file found for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading data for {symbol}: {e}")
            return None
    
    def validate_data(self, df, symbol):
        """Validate data quality"""
        if df is None or df.empty:
            return False
            
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Missing columns in {symbol} data: {missing_columns}. Available: {df.columns.tolist()}")
            return False
            
        return True