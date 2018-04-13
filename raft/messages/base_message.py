import time


class BaseMessage(object):
    AppendEntries = 'append_entries'
    RequestVote = 'request_vote'
    RequestVoteResponse = 'request_vote_response'
    Response = 'response'

    def __init__(self, sender, receiver, term, data):
        self._timestamp = int(time.time())

        self._sender = sender
        self._receiver = receiver
        self._data = data
        self._term = term

    @property
    def receiver(self):
        return self._receiver

    @property
    def sender(self):
        return self._sender

    @property
    def data(self):
        return self._data

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def term(self):
        return self._term

    @property
    def type(self):
        return self._type
