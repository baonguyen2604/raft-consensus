import raft
import sys
import asyncio

def run_server(ipv4, port, endpoints):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()

    state = raft.state_follower()
    log = []
    dummy_index = {
        'term': None,
        'command': None,
        'balance': None
    }
    log.append(dummy_index)
    async def main():
        server = raft.create_server(name='raft', state=state, log=log, other_nodes=endpoints, endpoint=(ipv4, port), loop=loop)
        print(f"started server on endpoint {(ipv4, port)} with others at {endpoints}", flush=True)
    loop.run_until_complete(main())
    loop.run_forever()
    loop.stop()


if __name__ == '__main__':
    import argparse
    def create_parser():
        parser = argparse.ArgumentParser()
        parser.add_argument('-p', '--port', required=False, default=5000,
                            help="port on which to listen")
        parser.add_argument('-i', '--ipv4', required=False, default="localhost",
                            help="IPV4 address on which to listen")
        parser.add_argument('-n', '--node_list', required=True,
                            help="Enpoints of other nodes, e.g. 127.0.0.1:5000,127.0.0.1:5001,192.168.100.1:5000")
        
        return parser
        
    parser = create_parser()
    args = parser.parse_args()
    nodes = args.node_list.split(",")
    endpoints = [ (h.split(":")[0],int(h.split(":")[1])) for h in nodes ]
    try:
        run_server(args.ipv4, int(args.port), endpoints)
    except KeyboardInterrupt:
        print('\nServer terminated')
        pass
