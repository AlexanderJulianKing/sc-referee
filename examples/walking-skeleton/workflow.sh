#!/bin/sh
opaque-normalizer data.csv > normalized.csv
python analysis.py
