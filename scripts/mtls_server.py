import os
import ssl
import json
import secrets
import subprocess
import socketserver

import util
import click
from ray.util import get_node_ip_address

@click.command()
@click.option('-n', '--node-id', type=str, required=True)
@click.option('-s', '--shell', type=str, default='bash')
def serve(node_id, shell):
    ip = get_node_ip_address()
    dir = os.path.join(os.getcwd(), '.ray-delegate')
    cfg = os.path.join(dir, node_id)
    os.makedirs(dir, exist_ok=True)

    sni = secrets.token_hex(16)
    client_tls = util.generate_tls_certificate(sni, sni)
    server_tls = util.generate_tls_certificate(sni, sni)
    client_crt = util.tempwrite(client_tls['crt'])
    server_crt = util.tempwrite(server_tls['crt'])
    server_key = util.tempwrite(server_tls['key'])

    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_cert_chain(certfile=server_crt.name, keyfile=server_key.name)
    context.load_verify_locations(cafile=client_crt.name)

    class Delegator(socketserver.BaseRequestHandler):
        def handle(self):
            subprocess.run([shell], stdin=self.request, stdout=self.request, stderr=self.request)

    with socketserver.TCPServer((ip, 0), Delegator) as server:
        server.socket = context.wrap_socket(server.socket, server_side=True)
        with open(cfg, 'x') as f:
            json.dump({
                'sni': sni, 'ip': ip, 'port': server.socket.getsockname()[1], 
                'server_crt': server_tls['crt'].decode('ascii'),
                'client_crt': client_tls['crt'].decode('ascii'),
                'client_key': client_tls['key'].decode('ascii')
            }, f)
        try:
            server.serve_forever()
        finally:
            os.remove(cfg)

if __name__ == '__main__':
    serve()