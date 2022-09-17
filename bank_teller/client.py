import sys
from socket import *


def run_client(server_host, server_port):
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.settimeout(5)

    server_addr = server_host, server_port

    cmd = ''

    print('Welcome to your ATM! You can check your balance, credit to or debit from your account')
    print('Your starting balance is 0')
    print('Available commands are: query, credit <amount>, debit <amount>')

    while cmd != 'exit'.encode('utf8'):
        cmd = input('Enter command: ').encode('utf8')
        sock.sendto(cmd, server_addr)
        try:
            data = sock.recv(1024)
        except OSError:
            print('Timed out. Server is not responding')
            continue
        print(data.decode('utf8'))


if __name__=="__main__":
    import argparse
    def create_parser():
        parser = argparse.ArgumentParser()
        parser.add_argument('-p', '--port', required=False, default=5000,
                            help="port on which server listens")
        parser.add_argument('-i', '--ip_addr', required=False, default="localhost",
                            help="IPV4 address of server")
        return parser
        
    parser = create_parser()
    args = parser.parse_args()
    try:
        run_client(args.ip_addr, args.port)
    except KeyboardInterrupt:
        print('\nClient terminated')
        pass
