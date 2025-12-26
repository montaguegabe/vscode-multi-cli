#!/usr/bin/env bash

set -euo pipefail

# Make virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

