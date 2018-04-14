from collections import defaultdict
from .base_state import State
from ..messages.append_entries import AppendEntriesMessage
from .timer import Timer

import random


class Leader(State):

    def __init__(self, heartbeat_timeout=0.5):
        self._nextIndexes = defaultdict(int)
        self._matchIndex = defaultdict(int)
        self._heatbeat_timeout = heartbeat_timeout

    def set_server(self, server):
        self._server = server
        # send heartbeat immediately
        self._send_heartbeat()
        self.heartbeat_timer = Timer(self._heartbeat_interval(), self._send_heartbeat)
        self.heartbeat_timer.start()

        for n in self._server._neighbours:
            self._nextIndexes[n._name] = self._server._lastLogIndex + 1
            self._matchIndex[n._name] = 0

    def _heartbeat_interval(self):
        return random.uniform(0, self._heatbeat_timeout)

    def on_response_received(self, message):
        # check if last append_entries good?
        if (not message.data["response"]):
            # if not, back up log for this node
            self._nextIndexes[message.sender] -= 1

            # get next log entry to send to client
            prevIndex = max(0, self._nextIndexes[message.sender] - 1)
            prev = self._server._log[prevIndex]
            current = self._server._log[self._nextIndexes[message.sender]]

            # send new log to client and wait for respond
            appendEntry = AppendEntriesMessage(
                self._server._port,
                message.sender,
                self._server._currentTerm,
                {
                    "leaderId": self._server._name,
                    "leaderPort": self._server._port,
                    "prevLogIndex": prevIndex,
                    "prevLogTerm": prev["term"],
                    "entries": [current],
                    "leaderCommit": self._server._commitIndex,
                })
            self._send_response_message(appendEntry)
        else:
            # last append was good -> increase index
            self._nextIndexes[message.sender] += 1

            # check if caught up?
            if (self._nextIndexes[message.sender] > self._server._lastLogIndex):
                self._nextIndexes[message.sender] = self._server._lastLogIndex

        return self, None

    def _send_heartbeat(self):
        # print('Sending heartbeat from', self._server._port)
        message = AppendEntriesMessage(
            self._server._port,
            None,
            self._server._currentTerm,
            {
                "leaderId": self._server._name,
                "leaderPort": self._server._port,
                "prevLogIndex": self._server._lastLogIndex,
                "prevLogTerm": self._server._lastLogTerm,
                "entries": [],
                "leaderCommit": self._server._commitIndex,
            }
        )
        self._server.broadcast(message)

    def on_client_command(self, message, client_port):
        print('Leader received command')
        entries = [message]
        message = AppendEntriesMessage(
            self._server._port,
            None,
            self._server._currentTerm,
            {
                "leaderId": self._server._name,
                "leaderPort": self._server._port,
                "prevLogIndex": self._server._lastLogIndex,
                "prevLogTerm": self._server._lastLogTerm,
                "entries": entries,
                "leaderCommit": self._server._commitIndex,
            }
        )
        self._server.broadcast(message)
