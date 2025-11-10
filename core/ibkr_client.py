from ib_insync import *
import logging
import asyncio
from datetime import datetime

class IBKRClient:
    def __init__(self, host='127.0.0.1', port=7497, client_id=1, paper_trading=True):
        self.ib = IB()
        self.host = host
        self.port = port
        self.client_id = client_id
        self.paper_trading = paper_trading
        self.connected = False
        self.logger = logging.getLogger(__name__)
        
    def connect(self):
        """Connect to IBKR TWS/Gateway"""
        try:
            self.ib.connect(self.host, self.port, self.client_id)
            self.connected = True
            self.logger.info("✅ Connected to IBKR TWS/Gateway")
            
            # Set market data type
            if self.paper_trading:
                self.ib.reqMarketDataType(3)  # Frozen delayed data
            else:
                self.ib.reqMarketDataType(1)  # Live data
                
        except Exception as e:
            self.logger.error(f"❌ Connection failed: {e}")
            raise
            
    def disconnect(self):
        """Disconnect from IBKR"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            self.logger.info("🔌 Disconnected from IBKR")
            
    def create_option_contract(self, symbol, expiry, strike, right, exchange='SMART'):
        """Create and qualify an option contract"""
        contract = Option(
            symbol=symbol,
            lastTradeDateOrContractMonth=expiry,
            strike=strike,
            right=right,
            exchange=exchange,
            currency='USD'
        )
        
        try:
            qualified = self.ib.qualifyContracts(contract)
            return qualified[0] if qualified else None
        except Exception as e:
            self.logger.error(f"Contract qualification failed: {e}")
            return None
            
    def get_historical_data(self, contract, duration='1 D', bar_size='1 min'):
        """Get historical data for backtesting"""
        try:
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1
            )
            return bars
        except Exception as e:
            self.logger.error(f"Historical data error: {e}")
            return []