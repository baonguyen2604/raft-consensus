import sys
from socket import *


def run_client(server_port):
    sock = socket(AF_INET, SOCK_DGRAM)

    server_addr = 'localhost', server_port

    cmd = ''

    print('Welcome to your ATM! You can check your balance, credit to or debit from your account')
    print('Your starting balance is 0')
    print('Available commands are: query, credit <amount>, debit <amount>')

    while cmd != 'exit'.encode('utf8'):
        cmd = input('Enter command: ').encode('utf8')
        sock.sendto(cmd, server_addr)
        data = sock.recv(1024)
        print(data.decode('utf8'))


if __name__ == '__main__':
    if len(sys.argv) > 2:
        print("Usage: python client.py <server_port>")
        exit(-1)
    run_client(int(sys.argv[1]))
