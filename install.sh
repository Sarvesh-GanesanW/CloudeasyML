#!/bin/bash

echo "================================================"
echo "Housing Crisis Prediction Ensemble - Installation"
echo "================================================"

echo -e "\nStep 1: Installing core dependencies..."
pip install -r requirements.txt

echo -e "\nStep 2: Installing PyTorch Geometric dependencies..."
pip install torch-scatter torch-sparse torch-cluster torch-spline-conv -f https://data.pyg.org/whl/torch-2.0.0+cu118.html

echo -e "\nStep 3: Installing foundation models (TimesFM and Chronos)..."
pip install git+https://github.com/google-research/timesfm.git
pip install git+https://github.com/amazon-science/chronos-forecasting.git

echo -e "\nStep 4: Installing AutoGluon (optional, for advanced ensemble)..."
read -p "Install AutoGluon? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    pip install autogluon.tabular autogluon.timeseries
fi

echo -e "\nStep 5: Creating necessary directories..."
mkdir -p data/raw data/processed data/cache models/saved

echo -e "\n================================================"
echo "Installation Complete!"
echo "================================================"
echo -e "\nNext steps:"
echo "1. Get a FRED API key from: https://fred.stlouisfed.org/docs/api/api_key.html"
echo "2. Run quick start: python notebooks/quickstart.py"
echo "3. Run full pipeline: python main.py --fred-api-key YOUR_KEY --mode full"
echo -e "\nFor more information, see the documentation."
