from .base_state import State
from ..messages.request_vote import RequestVoteResponseMessage


# Base class for follower and candidate states
class Voter(State):

    def __init__(self):
        self._last_vote = None

    def on_vote_request(self, message):
        # if node has not voted and lastLogIndex from message > node's lastLogIndex --> vote Yes
        if self._last_vote is None and message.data["lastLogIndex"] >= self._server._lastLogIndex:
            self._last_vote = message.sender
            self._send_vote_response_message(message)
        else:
            self._send_vote_response_message(message, votedYes=False)

        return self, None

    def _send_vote_response_message(self, message, votedYes=True):
        vote_response = RequestVoteResponseMessage(
            self._server.endpoint,
            message.sender,
            message.term,
            {"response": votedYes})
        self._server.send_message_response(vote_response)
