#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# ...
#

"""
start_sampleapp
~~~~~~~~~~~~~~~~~
...
"""

import json
import socket
import argparse

from daemon.weaprous import WeApRous

PORT = 8000  # Default port

app = WeApRous()

@app.route('/login', methods=['POST'])
def login(headers="guest", body="anonymous"):
    """
    Handle user login via POST request.
    ...
    """
    print(f"[SampleApp] Logging in {headers} to {body}")
    return {"status": "login_called", "headers": str(headers), "body": body}

@app.route('/hello', methods=['PUT'])
def hello(headers, body):
    """
    Handle greeting via PUT request.
    ...
    """
    print(f"[SampleApp] ['PUT'] Hello in {headers} to {body}")
    return {"status": "hello_called", "headers": str(headers), "body": body}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Backend', description='', epilog='Beckend daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PORT)
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port
    
    app.prepare_address(ip, port)
    app.run()