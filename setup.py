from setuptools import setup, find_packages

setup(
    name="ibkr_scalper",
    version="1.0.0",
    description="SPY/QQQ Options Scalping Bot with IBKR Integration",
    packages=find_packages(),
    install_requires=[
        "ib_insync>=0.9.86",
        "pandas>=1.5.0", 
        "numpy>=1.21.0",
        "yfinance>=0.2.18",
        "matplotlib>=3.5.0",
        "scipy>=1.9.0",
    ],
    python_requires=">=3.8",
)