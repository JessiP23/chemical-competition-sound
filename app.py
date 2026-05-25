"""
Main application entry point for Chemical-to-Audio Intelligent Monitoring System.

This is the primary entry point that launches the Streamlit dashboard.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.dashboard import main

if __name__ == "__main__":
    main()
