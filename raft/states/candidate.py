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
        self.candidate_timer.start()
        self._start_election()

    def candidate_interval(self):
        return random.uniform(self._timeout, 2 * self._timeout)

    def on_vote_request(self, message):
        return self, None

    def on_vote_received(self, message):
        # reset timer
        self.candidate_timer.reset()

        if message.sender not in self._votes:
            self._votes[message.sender] = message

            # check if received majorities
            if len(self._votes.keys()) > (self._server._total_nodes - 1) / 2:
                leader = Leader()
                self._server._state = leader
                leader.set_server(self._server)
                return leader, None

        # check if received all the votes -> resign
        if len(self._votes) == len(self._server._neighbours):
            self._resign()
        else:
            return self, None

    def _start_election(self):
        self._server._currentTerm += 1
        election = RequestVoteMessage(
            self._server._name,
            None,
            self._server._currentTerm,
            {
                "lastLogIndex": self._server._lastLogIndex,
                "lastLogTerm": self._server._lastLogTerm,
            }
        )
        self._server.broadcast(election)
        self._last_vote = self._server._name

    def _resign(self):
        self.candidate_timer.stop()
        from .follower import Follower
        follower = Follower()
        self._server._state = follower
        follower.set_server(self._server)
        return follower, None
