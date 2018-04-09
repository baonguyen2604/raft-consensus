import raft
import sys
import asyncio


def run_cluster():
    loop = asyncio.get_event_loop()

    nodes = []
    for i in range(1, len(sys.argv)):
        state = raft.state_follower()
        server = raft.create_server(i, state, [], [], sys.argv[i])
        nodes.append(server)

    update_neighbours(nodes)
    loop.run_forever()
    loop.stop()


def update_neighbours(nodes):
    for i in range(0, len(nodes)):
        for j in range(0, len(nodes)):
            if i != j:
                nodes[i]._neighbours.append(nodes[j])


if __name__ == '__main__':
    run_cluster()
