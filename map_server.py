import asyncio
import json
import csv
import sys

HOST = '192.168.2.26'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

mapfile = sys.argv[1]

tokens = {}

async def handle_client(reader, writer):
    global tokens
    global mapfile
    request = None
    while request != 'quit':
        request = (await reader.read(255)).decode('utf8')
        req = json.loads(request)
        if 'op' in req and 'arg' in req:
            if req['op'] == 'get':
                if req['arg'] == 'map':
                    response = json.dumps(mapfile)
                elif req['arg'] == 'tokens':
                    response = json.dumps(tokens)
                else:
                    response = 'err'
            elif req['op'] == 'set':
                if req['arg'] == 'place_token':
                    token_name = req['data']['name']
                    row = req['data']['row']
                    col = req['data']['col']
                    img = req['data']['img']
                    tokens[token_name] = {'row':row, 'col':col, 'img':img}
                    response = 'ack'
            elif req['op'] == 'admin':
                print(req)
                if req['arg'] == 'set_map':
                    mapfile = req['data']
                    tokens = {}
                response = 'ack'
        else:
            response = 'err'
        resp_len = len(response.encode('utf8'))
        writer.write(((u'%08d' % resp_len) + response).encode('utf8'))
        await writer.drain()
    writer.close()

loop = asyncio.get_event_loop()
loop.create_task(asyncio.start_server(handle_client, HOST, PORT))
loop.run_forever()

