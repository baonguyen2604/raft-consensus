from ..messages.serializer import Serializer

from socket import *

import copy
import asyncio
import threading
import errno


class Server(object):

    def __init__(self, name, state, log, neiports, port, loop):
        self._name = name
        self._state = state
        self._log = log
        self._port = port
        self._neiports = neiports
        self._loop = loop
        self._queue = asyncio.Queue()
        self._sock = socket(AF_INET, SOCK_DGRAM)
        self._sock.bind(self._port)
        self._nei_portnum = []
        for port in self._neiports:
            self._nei_portnum.append(port[1])

        self.client_port = None
        self._total_nodes = len(self._neiports) + 1
        self._commitIndex = 0
        self._currentTerm = 0
        self._lastLogIndex = 0
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
            self._loop.create_datagram_endpoint(udp, sock=self._sock),
            loop=self._loop
        )

    def broadcast(self, message):
        for n in self._neiports:
            # Have to create a deep copy of message to have different receivers
            send_message = copy.deepcopy(message)
            send_message._receiver = n
            asyncio.ensure_future(self.post_message(send_message), loop=self._loop)

    def send_message_response(self, message):
        n = [n for n in self._neiports if n == message.receiver]
        if len(n) > 0:
            asyncio.ensure_future(self.post_message(message), loop=self._loop)

    async def post_message(self, message):
        await self._queue.put(message)

    def on_message(self, data, addr):
        addr = addr[1]
        if (addr not in self._nei_portnum) and (len(self._neiports) != 0):
            command = data.decode('utf8')
            self._state.on_client_command(command, addr)
        elif addr in self._nei_portnum:
            try:
                message = Serializer.deserialize(data)
                message._receiver = message.receiver[0], message.receiver[1]
                message._sender = message.sender[0], message.sender[1]
                state, response = self._state.on_message(message)
                self._state = state

            except KeyError:
                message = Serializer.deserialize_client(data)
                self._state.on_client_command(message['command'], message['client_port'])


# async class to send messages between server
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
                try:
                    data = message['value'].encode('utf8')
                    addr = message['receiver']
                    print('Returning client request')
                    self._server._sock.sendto(data, addr)
                except KeyError:
                    print('Redirecting client request')
                    data = Serializer.serialize_client(message['command'], message['client_port'])
                    addr = self._server._state._leaderPort
                    self.transport.sendto(data, (addr[0], addr[1]))

    def connection_made(self, transport):
        self.transport = transport
        asyncio.ensure_future(self.start(), loop=self._loop)

    def datagram_received(self, data, addr):
        self.message_handler(data, addr)


# thread to wait for message from user client
class UDP_Server(threading.Thread):
    def __init__(self, sock, loop, server, daemon=True):
        threading.Thread.__init__(self, daemon=daemon)
        self._sock = sock
        self._loop = loop
        self._server = server

    def run(self):
        while True:
            try:
                data, addr = self._sock.recvfrom(1024)
                self._loop.call_soon_threadsafe(self._server.on_message, data, addr)
            except IOError as exc:
                if exc.errno == errno.EWOULDBLOCK:
                    pass
