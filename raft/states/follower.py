from .voter import Voter
from .timer import Timer
from .candidate import Candidate

import random


# concrete class for follower state
class Follower(Voter):

    def __init__(self, timeout=0.5):
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

        if message.data != {}:
            log = self._server._log
            data = message.data
            self._leaderPort = data["leaderPort"]

            # TODO: copied from simpleRaft. check logic
            # Check if leader is too far ahead in log
            if data['leaderCommit'] != self._server._commitIndex:
                # if so then we use length of log - 1
                self._server._commitIndex = min(data['leaderCommit'], len(log) - 1)

            # If log is smaller than prevLogIndex -> not up-to-date
            if (len(log) < data["prevLogIndex"]):
                self._send_response_message(message, votedYes=False)
                return self, None

            # make sure prevLogIndex term is always equal to the server
            if (len(log) > 0 and log[data["prevLogIndex"]]["term"] != data["prevLogTerm"]):
                # conflict detected -> resync and delete everythiing from this
                # prevLogIndex and forward (extraneous entries)
                # send a failure to server
                log = log[:data["prevLogIndex"]]
                self._send_response_message(message, votedYes=False)
                self._server._log = log
                self._server._lastLogIndex = data["prevLogIndex"]
                self._server._lastLogTerm = data["prevLogTerm"]
                return self, None
            else:
                # check if commitIndex is the same as the leader's
                # make sure leaderCommit > 0 and data is different
                # print('Data is: ', data)
                if (len(log) > 0 and data["leaderCommit"] > 0 and
                log[data["leaderCommit"]-1]["term"] != message.term):
                    # data is different
                    # fix by taking current log and slicing it to leaderCommit + 1
                    # set the last value to commitValue
                    log = log[:self._server._commitIndex]
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
                        for entry in data["entries"]:
                            log.append(entry)
                            self._server._commitIndex += 1

                        self._server._lastLogIndex = len(log) - 1
                        self._server._lastLogTerm = log[-1]["term"]
                        self._commitIndex = len(log) - 1
                        self._server._log = log
                        self._send_response_message(message)
            self._send_response_message(message)
            # print('Follower at', self._server._port, 'log is:', self._server._log)
            return self, None
        else:
            return self, None

    def on_client_command(self, message, client_port):
        neis = self._server._neighbours
        for nei in neis:
            if nei._port[1] == self._leaderPort[1]:
                nei._state.on_client_command(message, client_port)

    def on_vote_received(self, message):
        return self, None

    def on_vote_request(self, message):
        self.election_timer.stop()
        if self._last_vote is None and message.data["lastLogIndex"] >= self._server._lastLogIndex:
            self._last_vote = message.sender
            self._send_vote_response_message(message)
        else:
            self._send_vote_response_message(message, votedYes=False)

        self.election_timer.start()
        return self, None
