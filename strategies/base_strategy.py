import logging
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    def __init__(self, ib_client=None):
        self.ib_client = ib_client
        self.logger = logging.getLogger(__name__)
        
    @abstractmethod
    def analyze_market_condition(self, df):
        """Analyze market and return trading signals"""
        pass
        
    @abstractmethod
    def generate_trade_signal(self, signals):
        """Generate trade signal based on analysis"""
        pass