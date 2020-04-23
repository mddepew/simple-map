import socket
import configparser
import json


print('parsing config...')
conf = configparser.ConfigParser()
conf.read('config.ini')

host = conf.get('Server', 'Hostname')
port = int(conf.get('Server', 'Port'))

closed = False

server_con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_con.connect((host, port))
print('connected to server')
while not closed:
    cmd = input('>')
    if len(cmd.split(' ')) == 1:
        if cmd == 'quit' or cmd == 'exit':
            closed=True
    else:
        op, arg = cmd.split(' ', 1)
        if op == 'map':
            print('changing map to %s' % arg)
            server_con.sendall(json.dumps({'op':'admin', 'arg':'set_map', 'data':arg}).encode())
            resp_len = int(server_con.recv(8).decode())
            data = server_con.recv(resp_len)
            if data.decode() != 'ack':
                print('Update not acknowledged by server')
server_con.close()
