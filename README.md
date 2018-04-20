# Raft Distributed Consensus

Simple implementation of Raft Consensus Algorithm using Python

Note: only supports Python 3

## Install
`pip install -r requirements.txt`

## Bank ledger example

- Run 5 servers from bank_teller

  - `./run_server <server_port>`

- If python3 is not found, change the run_server.sh to use python instead

- Run bank client connecting to a specific server

  - `python client.py <server_port>`
