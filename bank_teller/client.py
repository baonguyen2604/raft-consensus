from curio import run, spawn, socket

import asyncio
import curio
import sys


class UDP_Client(asyncio.DatagramProtocol):
    def __init__(self, queue, loop):
        self._queue = queue
        self._loop = loop
        self.transport = None

    def __call__(self):
        return self

    async def start(self):
        while not self.transport.is_closing():
            message = await self._queue.get()
            self.transport.sendto(message)

    def connection_made(self, transport):
        self.transport = transport
        asyncio.ensure_future(self.start(), loop=self._loop)


async def run_client(port):
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue(loop=loop)
    udp = UDP_Client(
        queue=queue,
        loop=loop,
    )

    cmd = ''
    while cmd != 'exit'.encode('utf8'):
        connect = loop.create_datagram_endpoint(udp, remote_addr=('localhost', int(sys.argv[1])))
        cmd = input('Enter command: ').encode('utf8')
        print('Message:', cmd)
        await queue.put(cmd)
        loop.run_until_complete(connect)

    loop.stop()

# async def run_client(port=5000):
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     await sock.connect(port)
#
#     cmd = ''
#     while cmd != 'exit'.encode('utf8'):
#         cmd = input("Enter command: ").encode('utf8')
#         print('Message:', cmd)
#         await sock.send(cmd)
#         #resp = await sock.recv(1000)
#         #print('Response:', resp)
#     await sock.close()

if __name__ == '__main__':
    curio.run(run_client, ('localhost', int(sys.argv[1])))
