#!/bin/bash
echo "🚀 IBKR Scalper - Clean Installation"
echo "======================================"

# Deactivate conda if active
conda deactivate 2>/dev/null

# Create clean virtual environment
echo "🔧 Creating clean virtual environment..."
python3 -m venv ibkr_scalper_env

# Activate environment
echo "🔧 Activating virtual environment..."
source ibkr_scalper_env/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install compatible packages
echo "📦 Installing Python 3.8 compatible packages..."
pip install -r requirements_py38.txt

# Test the installation
echo "🧪 Testing installation..."
python main_py38.py

echo ""
echo "🎉 Installation complete!"
echo "💡 To activate this environment in the future, run:"
echo "   source ibkr_scalper_env/bin/activate"