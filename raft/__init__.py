from .servers.server import Server
from .states.follower import Follower


__all__ = [
    'create_server',
    'state_follower'
]

create_server = Server
state_follower = Follower
