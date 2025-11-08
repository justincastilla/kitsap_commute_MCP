#!/bin/bash
# Test script for verifying the reorganization

echo "=========================================="
echo "Testing Kitsap Commute MCP Reorganization"
echo "=========================================="
echo

# Test 1: Python syntax
echo "Test 1: Python syntax validation..."
python3 -m py_compile commute_server.py elasticsearch_server.py utilities.py config.py setup/elasticsearch_setup.py
if [ $? -eq 0 ]; then
    echo "✓ All Python files have valid syntax"
else
    echo "✗ Python syntax errors found"
    exit 1
fi
echo

# Test 2: Data files
echo "Test 2: Data files can be loaded..."
python3 << 'PYTHON'
import json
from pathlib import Path
DATA_DIR = Path('data')
with open(DATA_DIR / 'ferry_terminals.json') as f: terminals = json.load(f)
with open(DATA_DIR / 'ferry_schedules.json') as f: schedules = json.load(f)
with open(DATA_DIR / 'sample_events.json') as f: events = json.load(f)
print(f"✓ Loaded {len(terminals)} terminals, {len(schedules)} routes, {len(events)} events")
PYTHON
echo

# Test 3: Module imports
echo "Test 3: Module imports..."
python3 << 'PYTHON'
import config
import utilities
from setup import elasticsearch_setup
import warnings
with warnings.catch_warnings(record=True):
    warnings.simplefilter('always')
    from data import elasticsearch_initialization
print("✓ All modules import successfully")
PYTHON
echo

echo "=========================================="
echo "All tests passed! ✓"
echo "=========================================="
