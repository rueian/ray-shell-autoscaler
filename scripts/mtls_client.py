import os
import sys
import ssl
import json
import socket

import util
import click

@click.command()
@click.option('-n', '--node-id', type=str, required=True)
def proxy(node_id):
    dir = os.path.join(os.getcwd(), '.ray-delegate')
    cfg = json.load(open(os.path.join(dir, node_id)))

    server_crt = util.tempwrite(cfg['server_crt'].encode('ascii'))
    client_crt = util.tempwrite(cfg['client_crt'].encode('ascii'))
    client_key = util.tempwrite(cfg['client_key'].encode('ascii'))

    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=server_crt.name)
    context.load_cert_chain(certfile=client_crt.name, keyfile=client_key.name)

    with socket.create_connection((cfg['ip'], cfg['port'])) as sock:
        with context.wrap_socket(sock, server_hostname=cfg['sni']) as ssock:
            sys.stdout = ssock.makefile('w')
            while True:
                b = sys.stdin.buffer.read()
                if not b:
                    return
                ssock.write(b)

if __name__ == '__main__':
    proxy()