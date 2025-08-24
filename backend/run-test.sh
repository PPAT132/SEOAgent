#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python tests/test_full_pipeline.py
