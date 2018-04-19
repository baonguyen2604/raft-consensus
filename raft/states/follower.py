from .voter import Voter
from .timer import Timer
from .candidate import Candidate

import random
import asyncio
import copy

# concrete class for follower state
class Follower(Voter):

    def __init__(self, timeout=0.75):
        Voter.__init__(self)
        self._timeout = timeout

    def set_server(self, server):
        self._server = server
        self.election_timer = Timer(self.election_interval(), self._start_election)
        self.election_timer.start()

    def election_interval(self):
        return random.uniform(self._timeout, 2 * self._timeout)

    def _start_election(self):
        # print('Follower at', self._server._port, 'turning to Candidate')
        self.election_timer.stop()
        candidate = Candidate()
        self._server._state = candidate
        candidate.set_server(self._server)
        return candidate, None

    def on_append_entries(self, message):
        # reset timeout
        self.election_timer.reset()
        # print('Received heartbeat from', message.sender)

        if (message.term < self._server._currentTerm):
            self._send_response_message(message, votedYes=False)
            return self, None

        if message.data != {}:
            log = self._server._log
            data = message.data
            self._leaderPort = data["leaderPort"]

            if len(data['entries']) > 0:
                print('received non-empty append')
                print('prevLogIndex:', data['prevLogIndex'])

            # TODO: copied from simpleRaft. check logic
            # Check if leader is too far ahead in log
            if data['leaderCommit'] != self._server._commitIndex:
                # if so then we use length of log - 1
                self._server._commitIndex = min(data['leaderCommit'], len(log) - 1)

            # If log is smaller than prevLogIndex -> not up-to-date
            if (len(log)-1 < data["prevLogIndex"]):
                print(self._server._port, 'log len', len(log), 'is less than leader prevLogIndex', data["prevLogIndex"])
                print('sender:', message.sender)
                print('Follower log:', self._server._log)
                print(data)
                self._send_response_message(message, votedYes=False)
                return self, None

            try:
                if len(log) > 1:
                    test = log[data["prevLogIndex"]]["term"]
            except IndexError:
                print('IndexError in follower')
                print(data)
                print(log)
                exit(-1)

            if len(data['entries']) > 0:
                print('Receiving non heartbeat entries')
            # make sure prevLogIndex term is always equal to the server
            if (len(log) > 1 and log[data["prevLogIndex"]]["term"] != data["prevLogTerm"]):
                # conflict detected -> resync and delete everything from this
                # prevLogIndex and forward (extraneous entries)
                # send a failure to server
                print('Follower conflicting??')
                print(log)
                print(data)
                log = log[:data["prevLogIndex"]]
                self._send_response_message(message, votedYes=False)
                self._server._log = log
                self._server._lastLogIndex = data["prevLogIndex"]
                self._server._lastLogTerm = data["prevLogTerm"]
                return self, None
            else:
                # check if commitIndex is the same as the leader's
                # make sure leaderCommit > 0 and data is different
                try:
                    if False and len(log) > 1 and data["leaderCommit"] > 0:
                        test = log[data["leaderCommit"]]["term"]
                except IndexError:
                    print('Message:')
                    print(message.data)
                    print('Log:')
                    print(log)
                    print('data leaderCommit:' ,data['leaderCommit'])
                    exit(-1)

                if (len(log) > 1 and data["leaderCommit"] > 0 and False and
                log[data["leaderCommit"]]["term"] != message.term):
                    # data is different
                    # fix by taking current log and slicing it to leaderCommit + 1
                    # set the last value to commitValue
                    print('data different')
                    print(log)
                    print('commit index:', self._server._commitIndex)
                    log = log[:self._server._commitIndex+1]
                    for entry in data["entries"]:
                        log.append(entry)
                        self._server._commitIndex += 1

                    self._send_response_message(message)
                    self._server._lastLogIndex = len(log) - 1
                    self._server._lastLogTerm = log[-1]["term"]
                    self._commitIndex = len(log) - 1
                    self._server._log = log
                else:
                    # commit index is not out of range of the log
                    # -> append to the log now
                    # commitIndex = len(log)

                    # check if this is a heartbeat
                    if (len(data["entries"]) > 0):
                        print(self._server._port, 'appending log')
                        for entry in data["entries"]:
                            log.append(entry)
                            self._server._commitIndex += 1

                        self._server._lastLogIndex = len(log) - 1
                        self._server._lastLogTerm = log[-1]["term"]
                        self._commitIndex = len(log) - 1
                        self._server._log = log

                        for entry in self._server._log:
                           print(entry)
                        print(self._server._port, "Follower lastLogIndex is:", self._server._lastLogIndex)

                        self._send_response_message(message)
            self._send_response_message(message)
            # print('Follower at', self._server._port, 'log is:', self._server._log)
            return self, None
        else:
            return self, None

    def on_client_command(self, command, client_port):
        # neis = self._server._neighbours
        # for nei in neis:
        #     if nei._port[1] == self._leaderPort[1]:
        #         nei._state.on_client_command(message, client_port)
        message = {
            'command': command,
            'client_port': client_port,
        }
        asyncio.ensure_future(self._server.post_message(message), loop=self._server._loop)

    def on_vote_received(self, message):
        return self, None

    def on_vote_request(self, message):
        # self.election_timer.stop()
        if self._last_vote is None and message.data["lastLogIndex"] >= self._server._lastLogIndex:
            self._last_vote = message.sender
            # print(message.receiver, 'voted YES for', message.sender, 'in term', message.term)
            self._send_vote_response_message(message)
        else:
            # print(message.receiver, 'voted NO for', message.sender, 'in term', message.term)
            self._send_vote_response_message(message, votedYes=False)

        # self.election_timer.start()
        return self, None
