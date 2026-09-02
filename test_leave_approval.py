#!/usr/bin/env python3
"""Root wrapper for test_leave_approval.py — forwards to graphify/test_leave_approval.py"""
import os
import sys
import asyncio
from pathlib import Path

GRAPHIFY_DIR = Path(__file__).parent / "graphify"
os.chdir(GRAPHIFY_DIR)
sys.path.insert(0, str(GRAPHIFY_DIR))

import test_leave_approval
if __name__ == "__main__":
    asyncio.run(test_leave_approval.main())
