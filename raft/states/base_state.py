import time
import random

from ..messages.base_message import BaseMessage
from ..messages.response import ResponseMessage


# abstract class for all states
class State(object):
    def set_server(self, server):
        self._server = server

    def on_message(self, message):
        """
        Called when receiving a message, then
        calls the corresponding methods based on states
        """

        _type = message.type

        # If the message.term < currentTerm -> tell the sender to update term
        if (message.term > self._server._currentTerm):
            self._server._currentTerm = message.term
        elif (message.term < self._server._currentTerm):
            self._send_response_message(message, votedYes=False)
            return self, None

        if (_type == BaseMessage.AppendEntries):
            return self.on_append_entries(message)
        elif (_type == BaseMessage.RequestVote):
            return self.on_vote_request(message)
        elif (_type == BaseMessage.RequestVoteResponse):
            return self.on_vote_received(message)
        elif (_type == BaseMessage.Response):
            return self.on_response_received(message)

    def on_leader_timeout(self, message):
        """Called when leader timeout is reached"""

    def on_vote_request(self, message):
        """Called when there is a vote request"""

    def on_vote_received(self, message):
        """Called when this node receives a vote"""
        return self, None

    def on_append_entries(self, message):
        """Called when there is a request for this node to append entries"""

    def on_response_received(self, message):
        """Called when a response is sent back to the leader"""

    def on_client_command(self, message, client_port):
        """Called when there is a client request"""

    def _send_response_message(self, msg, votedYes=True):
        response = ResponseMessage(
            self._server._port,
            msg.sender,
            msg.term,
            {
                "response": votedYes,
                "currentTerm": self._server._currentTerm,
            }
        )
        self._server.send_message_response(response, msg.sender)
