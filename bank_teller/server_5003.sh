#!/usr/bin/env bash
# Add raft package to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../"

# Start
python3 run_server.py -p 5003 -n 5001 5002 5000 5004
