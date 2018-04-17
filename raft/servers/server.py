from ..messages.serializer import Serializer

from socket import *

import copy
import asyncio
import threading


class Server(object):

    def __init__(self, name, state, log, neighbours, port, loop):
        self._name = name
        self._state = state
        self._log = log
        self._port = ('localhost', int(port))
        self._neighbours = neighbours
        self._neiports = []
        self._loop = loop
        self._queue = asyncio.Queue(loop=self._loop)
        self._sock = socket(AF_INET, SOCK_DGRAM)
        self._sock.bind(self._port)

        # TODO: check logic
        self.balance = 0
        self.client_port = None
        self._total_nodes = 0
        self._commitIndex = 0
        self._currentTerm = 0
        self._lastApplied = 0
        self._lastLogIndex = -1
        self._lastLogTerm = None

        self._state.set_server(self)
        asyncio.ensure_future(self.start(), loop=self._loop)
        thread = UDP_Server(self._sock, self._loop, self)
        thread.start()

        print('Listening on ', self._port)

    async def start(self):
        udp = UDP_Protocol(
            queue=self._queue,
            message_handler=self.on_message,
            loop=self._loop,
            neiports=self._neiports,
            server=self
        )
        self.transport, _ = await asyncio.Task(
            self._loop.create_datagram_endpoint(udp, local_addr=self._port),
            loop=self._loop
        )

    def broadcast(self, message):
        for n in self._neighbours:
            # Have to create a deep copy of message to have different receivers
            send_message = copy.deepcopy(message)
            send_message._receiver = n._port
            asyncio.ensure_future(self.post_message(send_message), loop=self._loop)

    def send_message_response(self, message):
        n = [n for n in self._neiports if n == message.receiver[1]]
        if (len(n) > 0):
            asyncio.ensure_future(self.post_message(message), loop=self._loop)

    async def post_message(self, message):
        # print('Sending message of type', message.type, 'from', message.sender, 'to', message.receiver)
        await self._queue.put(message)

    def on_message(self, data, addr):
        addr = addr[1]
        if (addr not in self._neiports) and (len(self._neiports) != 0):
            command = data.decode('utf8')
            # print('Server at', self._port, 'Received data from', addr, command)
            # print('Server state is', self._state)
            self._state.on_client_command(command, addr)
        elif addr in self._neiports:
            message = Serializer.deserialize(data)
            message._receiver = message.receiver[0], message.receiver[1]
            message._sender = message.sender[0], message.sender[1]
            # print('Received message of type', message.type, 'from', message.sender, 'to', message.receiver)
            state, response = self._state.on_message(message)
            self._state = state


class UDP_Protocol(asyncio.DatagramProtocol):
    def __init__(self, queue, message_handler, loop, neiports, server):
        self._queue = queue
        self.message_handler = message_handler
        self._loop = loop
        self._neiports = neiports
        self._server = server

    def __call__(self):
        return self

    async def start(self):
        while not self.transport.is_closing():
            message = await self._queue.get()
            if not isinstance(message, dict):
                data = Serializer.serialize(message)
                self.transport.sendto(data, message.receiver)
            else:
                data = message['value'].encode('utf8')
                addr = message['receiver']
                self._server._sock.sendto(data, addr)

    def connection_made(self, transport):
        self.transport = transport
        asyncio.ensure_future(self.start(), loop=self._loop)

    def datagram_received(self, data, addr):
        self.message_handler(data, addr)


class UDP_Server(threading.Thread):
    def __init__(self, sock, loop, server, daemon=True):
        threading.Thread.__init__(self,daemon=daemon)
        self._sock = sock
        self._loop = loop
        self._server = server

    def run(self):
        while True:
            data, addr = self._sock.recvfrom(1024)
            self._loop.call_soon_threadsafe(self._server.on_message, data, addr)


