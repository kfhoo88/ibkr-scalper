import pandas as pd
import yfinance as yf
import logging
from datetime import datetime, timedelta
import pickle
import os

class DataManager:
    def __init__(self, ib_client=None, data_path='data/historical'):
        self.ib_client = ib_client
        self.data_path = data_path
        self.logger = logging.getLogger(__name__)
        os.makedirs(data_path, exist_ok=True)
        
    def download_historical_data(self, symbols, start_date, end_date, interval='1h'):
        """Download historical data using yfinance (works offline)"""
        historical_data = {}
        
        for symbol in symbols:
            try:
                self.logger.info(f"Downloading data for {symbol}...")
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date, interval=interval)
                
                if data.empty:
                    self.logger.warning(f"No data found for {symbol}")
                    continue
                    
                historical_data[symbol] = data
                self.logger.info(f"✅ Downloaded {symbol}: {len(data)} bars")
                
            except Exception as e:
                self.logger.error(f"Download failed for {symbol}: {e}")
                
        # Save to file
        filename = f"{self.data_path}/historical_data_{datetime.now().strftime('%Y%m%d')}.pkl"
        with open(filename, 'wb') as f:
            pickle.dump(historical_data, f)
            
        self.logger.info(f"Data saved to {filename}")
        return historical_data
        
    def load_historical_data(self, filename=None):
        """Load previously downloaded historical data"""
        if filename is None:
            # Find most recent file
            files = [f for f in os.listdir(self.data_path) if f.startswith('historical_data')]
            if not files:
                return None
            filename = sorted(files)[-1]
            
        filepath = os.path.join(self.data_path, filename)
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            
        self.logger.info(f"Loaded historical data from {filepath}")
        return data
        
    def get_current_price(self, symbol):
        """Get current price (works with IBKR or yfinance)"""
        if self.ib_client and self.ib_client.connected:
            # Use IBKR for real-time data
            contract = Stock(symbol, 'SMART', 'USD')
            ticker = self.ib_client.ib.reqMktData(contract)
            self.ib_client.ib.sleep(2)
            return ticker.close if ticker.close else ticker.last
        else:
            # Use yfinance as fallback
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d')
            return data['Close'].iloc[-1] if not data.empty else 0