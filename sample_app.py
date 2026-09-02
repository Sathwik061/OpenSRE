#!/usr/bin/env python3
"""Root wrapper for sample_app.py — forwards to graphify/sample_app.py"""
import os
import sys
from pathlib import Path

GRAPHIFY_DIR = Path(__file__).parent / "graphify"
os.chdir(GRAPHIFY_DIR)
sys.path.insert(0, str(GRAPHIFY_DIR))

import sample_app
if __name__ == "__main__":
    sample_app.main()
