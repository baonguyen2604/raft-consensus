from .voter import Voter
from .leader import Leader
from ..messages.request_vote import RequestVoteMessage
from .timer import Timer

import random


class Candidate(Voter):

    def __init__(self, timeout=0.5):
        Voter.__init__(self)
        self._timeout = timeout

    def set_server(self, server):
        self._server = server
        self._votes = {}
        self.candidate_timer = Timer(self.candidate_interval(), self._resign)
        self._start_election()

    def candidate_interval(self):
        # return random.uniform(self._timeout, 2 * self._timeout)
        return random.uniform(0, self._timeout)

    def on_append_entries(self, message):
        self._resign()

    def on_vote_request(self, message):
        self._send_vote_response_message(message, votedYes=False)
        return self, None

    def on_vote_received(self, message):
        # reset timer
        self.candidate_timer.reset()
        # print(self._server._port, 'received vote ', message.data, 'from', message.sender, 'in term', message.term)
        # print(self._server._port, 'votes are', self._votes)

        if message.sender[1] not in self._votes and message.data['response']:
            self._votes[message.sender[1]] = message.data['response']

            # check if received majorities
            if len(self._votes.keys()) > (self._server._total_nodes - 1) / 2:
                self.candidate_timer.stop()
                # print('Candidate at', self._server._port, 'turning to Leader')
                leader = Leader()
                self._server._state = leader
                leader.set_server(self._server)
                return leader, None

        # check if received all the votes -> resign
        if len(self._votes) == len(self._server._neiports):
            self._resign()
        else:
            return self, None

    def _start_election(self):
        # self.candidate_timer.reset()
        self.candidate_timer.start()
        self._server._currentTerm += 1
        election = RequestVoteMessage(
            self._server._port,
            None,
            self._server._currentTerm,
            {
                "lastLogIndex": self._server._lastLogIndex,
                "lastLogTerm": self._server._lastLogTerm,
            }
        )
        self._server.broadcast(election)
        self._last_vote = self._server._port

    def _resign(self):
        # print('Candidate at', self._server._port, 'turning to Follower')
        self.candidate_timer.stop()

        from .follower import Follower
        follower = Follower()
        self._server._state = follower
        follower.set_server(self._server)
        return follower, None

    # TODO:
    # If other candidates receive AppendEntries RPC, they check for the term number
    # If the term number is greater than their own, they accept the server as the leader and return to follower state
    # If the term number is smaller, they reject the RPC and still remain a candidate
