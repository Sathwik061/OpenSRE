#!/usr/bin/env python3
"""Root wrapper for trigger.py — forwards to graphify/trigger.py"""
import os
import sys
from pathlib import Path

GRAPHIFY_DIR = Path(__file__).parent / "graphify"
os.chdir(GRAPHIFY_DIR)
sys.path.insert(0, str(GRAPHIFY_DIR))

import trigger
if __name__ == "__main__":
    trigger.main()
