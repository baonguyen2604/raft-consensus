from .append_entries import AppendEntriesMessage
from .request_vote import *
from .response import ResponseMessage

import msgpack


class Serializer:
    @staticmethod
    def serialize(message):
        data = {
            'type': message._type,
            'sender': message.sender,
            'receiver': message.receiver,
            'data': message.data,
            'term': message.term,
        }
        return msgpack.packb(data, use_bin_type=True)

    @staticmethod
    def deserialize(data):
        message = msgpack.unpackb(data, use_list=True, encoding='utf-8')
        type = message['type']
        if type == 'append_entries':
            return AppendEntriesMessage(message['sender'], message['receiver'], message['term'], message['data'])
        elif type == 'request_vote':
            return RequestVoteMessage(message['sender'], message['receiver'], message['term'], message['data'])
        elif type == 'request_vote_response':
            return RequestVoteResponseMessage(message['sender'], message['receiver'], message['term'], message['data'])
        elif type == 'response':
            return ResponseMessage(message['sender'], message['receiver'], message['term'], message['data'])

        return None

    @staticmethod
    def serialize_client(message, client_port):
        data = {
            'command': message,
            'client_port': client_port,
        }
        return msgpack.packb(data, use_bin_type=True)

    @staticmethod
    def deserialize_client(data):
        message = msgpack.unpackb(data, use_list=True, encoding='utf8')
        return message
