from collections import defaultdict
from .base_state import State
from ..messages.append_entries import AppendEntriesMessage
from .timer import Timer

import random
import asyncio

# TODO: check lastApplied and commitIndex


class Leader(State):

    def __init__(self, heartbeat_timeout=0.5):
        self._nextIndexes = defaultdict(int)
        self._matchIndex = defaultdict(int)
        self._heartbeat_timeout = heartbeat_timeout

    def set_server(self, server):
        self._server = server
        # send heartbeat immediately
        print('Leader on ', self._server._port, 'in term', self._server._currentTerm)
        self._send_heartbeat()
        self.heartbeat_timer = Timer(self._heartbeat_interval(), self._send_heartbeat)
        self.heartbeat_timer.start()

        for neiport in self._server._neiports:
            self._nextIndexes[neiport[1]] = self._server._lastLogIndex + 1
            self._matchIndex[neiport[1]] = 0

    def _heartbeat_interval(self):
        return random.uniform(0, self._heartbeat_timeout)

    def on_response_received(self, message):
        # check if last append_entries good?
        if (not message.data["response"]):
            # if not, back up log for this node
            self._nextIndexes[message.sender[1]] -= 1
            # get next log entry to send to follower
            prevIndex = max(0, self._nextIndexes[message.sender[1]] - 1)
            prev = self._server._log[prevIndex]
            current = self._server._log[self._nextIndexes[message.sender[1]]]

            # send new log to client and wait for respond
            append_entry = AppendEntriesMessage(
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
            asyncio.ensure_future(self._server.post_message(append_entry), loop=self._server._loop)
        else:
            # last append was good -> increase index
            self._nextIndexes[message.sender[1]] += 1
            self._matchIndex[message.sender[1]] += 1

            # check if caught up?
            if (self._nextIndexes[message.sender[1]] > self._server._lastLogIndex):
                self._nextIndexes[message.sender[1]] = self._server._lastLogIndex + 1
                self._matchIndex[message.sender[1]] = self._server._lastLogIndex

            majority_response_received = 0

            for follower, matchIndex in self._matchIndex.items():
                if matchIndex == (self._server._lastLogIndex):
                    majority_response_received += 1

            if majority_response_received > (self._server._total_nodes - 1) / 2 \
                    and self._server._lastLogIndex > 0 and self._server._lastLogIndex == self._server._commitIndex+1:
                # committing next index
                self._server._commitIndex += 1

                client_addr = 'localhost', self._server.client_port
                last_log = self._server._log[self._server._lastLogIndex]
                response = last_log['response']
                message = {
                    'receiver': client_addr,
                    'value': response
                }
                asyncio.ensure_future(self._server.post_message(message), loop=self._server._loop)

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
                "leaderCommit": self._server._commitIndex,
            }
        )
        self._server.broadcast(message)

    def on_client_command(self, message, client_port):
        self._server.client_port = client_port
        response, balance = self.execute_command(message)
        entries = [{
            "term": self._server._currentTerm,
            "command": message,
            "balance": balance,
            "response": response
        }]
        self._server._log.append(entries[-1])

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

        self._server._lastLogTerm = self._server._currentTerm
        self._server._lastLogIndex += 1
        self._server.broadcast(message)

    def execute_command(self, command):
        command = command.split()
        balance = self._server._log[self._server._lastLogIndex]['balance'] or 0
        if len(command) == 0:
            response = "Invalid command"
        elif len(command) == 1 and command[0] == 'query':
            response = "Your current account balance is: " + str(balance)
        elif len(command) == 2 and command[0] == 'credit':
            if int(command[1]) <= 0:
                response = "Credit amount must be positive"
            else:
                response = "Successfully credited " + command[1] + " to your account"
                balance += int(command[1])
        elif len(command) == 2 and command[0] == 'debit':
            if balance >= int(command[1]):
                if int(command[1]) <= 0:
                    response = "Debit amount must be positive"
                else:
                    response = "Successfully debited " + command[1] + " from your account"
                    balance -= int(command[1])
            else:
                response = "Insufficient account balance"
        else:
            response = "Invalid command"
        return response, balance
