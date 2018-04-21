#!/usr/bin/env bash
# Add raft package to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../"

case $1 in
  5000)
    echo Running server on port 5000
    echo Expects neighbours to be on 5001, 5002, 5003, 5004
    python3 run_server.py -p 5000 -n 5001 5002 5003 5004
    ;;
  5001)
    echo Running server on port 5001
    echo Expects neighbours to be on 5000, 5002, 5003, 5004
    python3 run_server.py -p 5001 -n 5000 5002 5003 5004
    ;;
  5002)
    echo Running server on port 5002
    echo Expects neighbours to be on 5001, 5000, 5003, 5004
    python3 run_server.py -p 5002 -n 5000 5001 5003 5004
    ;;
  5003)
    echo Running server on port 5003
    echo Expects neighbours to be on 5001, 5002, 5000, 5004
    python3 run_server.py -p 5003 -n 5001 5002 5000 5004
    ;;
  5004)
    echo Running server on port 5004
    echo Expects neighbours to be on 5001, 5002, 5003, 5000
    python3 run_server.py -p 5004 -n 5001 5002 5003 5000
    ;;
  *)
    echo Usage: ./run_server <server_port> where port can be 5000, 5001, 5002, 5003, or 5004
    ;;
esac
