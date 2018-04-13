from collections import defaultdict
from .base_state import State
from ..messages.append_entries import AppendEntriesMessage


class Leader(State):

    def __init__(self):
        self._nextIndexes = defaultdict(int)
        self._matchIndex = defaultdict(int)

    def set_server(self, server):
        self._server = server
        # send heartbeat immediately
        self._send_heartbeat()

        for n in self._server._neighbours:
            self._nextIndexes[n._name] = self._server._lastLogIndex + 1
            self._matchIndex[n._name] = 0

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
                "learderCommit": self._server._commitIndex,
            }
        )
        self._server.send_message(message)

    def on_client_command(self, message, client_port):
        print('Leader received command')
        self._server._sock.sendto(message, client_port)
