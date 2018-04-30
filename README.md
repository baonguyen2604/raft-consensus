# Raft Distributed Consensus
Simple implementation of ![Raft Consensus Algorithm](raft.github.io) using Python for fault-tolerant distributed systems. Supports proper leader election and log replication.

Note: 
- Only supports Python 3
- This implementation is specific to the bank ledger example. Feel free to modify the source code to fit your use

## Requirements installation
`pip install -r requirements.txt`

## Bank ledger example

- Run 5 servers from bank_teller

  - `./run_server <server_port>`

- If python3 is not found, change the run_server.sh to use python instead

- Run bank client connecting to a specific server

  - `python client.py <server_port>`

## References
- ![raftos](https://github.com/zhebrak/raftos)
- ![simpleRaft](https://github.com/streed/simpleRaft/tree/master/simpleRaft)
- ![Raft visualization](http://thesecretlivesofdata.com/raft/)
