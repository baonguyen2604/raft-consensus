# Add raft package to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../"

# Start
python3 run_cluster.py 5000 5001 5002 5003 5004
