from collections import defaultdict
from .base_state import State
from ..messages.append_entries import AppendEntriesMessage
from .timer import Timer
from socket import *

import random
import asyncio

# TODO: check lastApplied and commitIndex

class Leader(State):

    def __init__(self, heartbeat_timeout=0.5):
        self._nextIndexes = defaultdict(int)
        self._matchIndex = defaultdict(int)
        self._heatbeat_timeout = heartbeat_timeout

    def set_server(self, server):
        print('Leader on ', server._port)
        self._server = server
        # send heartbeat immediately
        self._send_heartbeat()
        self.heartbeat_timer = Timer(self._heartbeat_interval(), self._send_heartbeat)
        self.heartbeat_timer.start()

        for n in self._server._neighbours:
            self._nextIndexes[n._port[1]] = self._server._lastLogIndex + 1
            self._matchIndex[n._port[1]] = 0

    def _heartbeat_interval(self):
        return random.uniform(0, self._heatbeat_timeout)

    def on_response_received(self, message):
        # check if last append_entries good?
        if (not message.data["response"]):
            # if not, back up log for this node
            self._nextIndexes[message.sender[1]] -= 1

            # get next log entry to send to client
            prevIndex = max(0, self._nextIndexes[message.sender[1]] - 1)
            prev = self._server._log[prevIndex]
            current = self._server._log[self._nextIndexes[message.sender[1]]]

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
            self._nextIndexes[message.sender[1]] += 1

            # check if caught up?
            if (self._nextIndexes[message.sender] > self._server._lastLogIndex):
                self._nextIndexes[message.sender] = self._server._lastLogIndex

            all_response_received = True
            for nei in self._server._neighbours:
                if nei._lastLogIndex != self._server._lastLogIndex or nei._lastLogTerm != self._server._lastLogTerm:
                    all_response_received = False

            if all_response_received and self._server._lastLogIndex >= 0 and self._server._lastLogIndex >= self._server._commitIndex:
                self.execute_command()
                self._server._commitIndex += 1

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
        self._server.client_port = client_port
        entries = [{
            "term": self._server._currentTerm,
            "command": message,
            "balance": self._server.balance
        }]
        self._server._log.append(entries[-1])
        self._server._lastLogTerm = self._server._currentTerm
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
        self._server._lastLogIndex += 1
        self._server.broadcast(message)

        print('Client request. Leader log is:')
        log = self._server._log
        for i in log:
            print(i)

    def execute_command(self):
        command = self._server._log[self._server._lastLogIndex]["command"]
        command = command.split()
        client_addr = 'localhost', self._server.client_port

        if len(command) == 0:
            response = "Invalid command"
        elif len(command) == 1 and command[0] == 'query':
            response = "Your current account balance is: " + str(self._server.balance)
        elif len(command) == 2 and command[0] == 'credit':
            if int(command[1]) <= 0:
                response = "Credit amount must be positive"
            else:
                response = "Successfully credited " + command[1] + " to your account"
                self._server.balance += int(command[1])
        elif len(command) == 2 and command[0] == 'debit':
            if self._server.balance >= int(command[1]):
                if int(command[1]) <= 0:
                    response = "Debit amount must be positive"
                else:
                    response = "Successfully debited " + command[1] + " from your account"
                    self._server.balance -= int(command[1])
            else:
                response = "Insufficient account balance"
        else:
            response = "Invalid command"

        message = {
            'receiver': client_addr,
            'value': response
        }
        asyncio.ensure_future(self._server.post_message(message), loop=self._server._loop)
