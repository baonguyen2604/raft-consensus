from ..messages.serializer import Serializer

from curio import run, spawn, socket

import sys
import curio
import asyncio
import threading


class Server(object):

    def __init__(self, name, state, log, neighbours, port):
        self._name = name
        self._state = state
        self._log = log
        self._port = ('localhost', int(port))
        self._neighbours = neighbours
        self._neiports = []

        # create UDP socket
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(self._port)

        # TODO: check
        self._total_nodes = 0
        self._commitIndex = 0
        self._currentTerm = 0
        self._lastApplied = 0
        self._lastLogIndex = 0
        self._lastLogTerm = None

        self._state.set_server(self)
        thread = UDP_Server(self, self._sock)
        thread.start()
        print('Listening on port', self._port[1])

    def broadcast(self, message):
        for n in self._neighbours:
            message._receiver = n._port
            asyncio.ensure_future(self.post_message(message, n._port), loop=asyncio.get_event_loop())

    def send_message_response(self, message, port):
        # TODO: copied from simpleRaft. check logic
        n = [n for n in self._neiports if n == message.receiver[1]]
        if (len(n) > 0):
            asyncio.ensure_future(self.post_message(message, port), loop=asyncio.get_event_loop())

    async def post_message(self, message, port):
        data = Serializer.serialize(message)
        await self._sock.sendto(data, port)

    def on_message(self, message):
        state, response = self._state.on_message(message)
        self._state = state

    def print_neighbours(self):
        for i in range(0, len(self._neighbours)):
            print(self._neighbours[i]._port)


class UDP_Server(threading.Thread):
    def __init__(self, server, sock, daemon=True):
        threading.Thread.__init__(self)
        self._server = server
        self._sock = sock
        self._neiports =[]

    def run(self):
        curio.run(self._wait_message())

    async def _wait_message(self):
        while True:
            data, addr = await self._sock.recvfrom(10000)

            if (addr[1] not in self._server._neiports) and (len(self._server._neiports) != 0):
                command = data.decode('utf8')
                print('Server at', self._server._port, 'Received data from', addr, command)
                print('Server state from thread is', self._server._state)
                self._server._state.on_client_command(command, addr)
            elif addr[1] in self._server._neiports:
                message = Serializer.deserialize(data)
                self._server.on_message(message)
