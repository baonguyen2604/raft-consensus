#!/usr/bin/env bash
# Add raft package to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../"

if [ $# -ne 1 ]; then
  echo "Invalid number of arguments"
  echo "Usage: ./run_server <server_port> where port can be 5000, 5001, 5002"
  exit
fi

case $1 in
  5000)
    echo Running server on port 5000
    echo Expects other nodes to be on 5001, 5002
    python3 run_server.py -p 5000 -n localhost:5001,locahost:5002 
    ;;
  5001)
    echo Running server on port 5001
    echo Expects other nodes to be on 5000, 5002
    python3 run_server.py -p 5001 -n localhost:5000,localhost:5002 
    ;;
  5002)
    echo Running server on port 5002
    echo Expects other nodes to be on 5001, 5000
    python3 run_server.py -p 5002 -n localhost:5000,localhost:5001 
    ;;
  *)
    echo Usage: ./run_server <server_port> where port can be 5000, 5001, 5002
    ;;
esac
