"""Root conftest.py to help pytest find the package."""

import os
import sys

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
