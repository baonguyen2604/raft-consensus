import raft
import sys
import asyncio

def run_server():
    argc = len(sys.argv)
    if argc < 3:
        print('Usage: python run_server.py -p <server_port> -n <list_of_neighbour_ports>')
        exit(-1)

    if sys.argv[1] == '-p':
        server_port = 'localhost', int(sys.argv[2])
    else:
        print('Usage: python server.py -p <server_port> -n <list_of_neighbour_ports>')
        exit(-1)

    neis = []
    if argc > 3 and sys.argv[3] == '-n':
        for i in range(4, argc):
            neis.append(('localhost', int(sys.argv[i])))

    loop = asyncio.get_event_loop()
    state = raft.state_follower()
    log = []
    dummy_index = {
        'term': None,
        'command': None,
        'balance': None
    }
    log.append(dummy_index)
    server = raft.create_server(name='raft', state=state, log=log, neiports=neis, port=server_port, loop=loop)
    loop.run_forever()
    loop.stop()


if __name__ == '__main__':
    try:
        run_server()
    except KeyboardInterrupt:
        print('Server terminated')
        pass
