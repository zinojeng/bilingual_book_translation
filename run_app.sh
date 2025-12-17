#!/bin/bash

# Define virtual environment name
VENV_NAME="venv"

# Check if virtual environment exists
if [ ! -d "$VENV_NAME" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_NAME
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
source $VENV_NAME/bin/activate

# Install requirements
echo "Installing/Updating dependencies..."
pip install --upgrade pip setuptools wheel maturin
# Install project in editable mode to get fresh dependencies from pyproject.toml
# This avoids potential conflicts from an outdated requirements.txt with strict pins
pip install -e .
pip install streamlit

# Run Streamlit app
echo "Starting Streamlit app..."
streamlit run streamlit_app.py
