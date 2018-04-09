from curio import run, spawn, socket

import curio
import sys


async def run_client(port=5000):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    await sock.connect(port)

    cmd = ''
    while cmd != 'exit'.encode('utf8'):
        cmd = input("Enter command: ").encode('utf8')
        print('Message:', cmd)
        await sock.send(cmd)
        #resp = await sock.recv(1000)
        #print('Response:', resp)
    await sock.close()

if __name__ == '__main__':
    curio.run(run_client, ('localhost', int(sys.argv[1])))
