#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.httpadapter
~~~~~~~~~~~~~~~~~

This module provides a http adapter object to manage and persist 
http settings (headers, bodies). The adapter supports both
raw URL paths and RESTful route definitions, and integrates with
Request and Response objects to handle client-server communication.
"""

import json # <-- ĐÃ THÊM: Cần thiết để xử lý phản hồi API
from .request import Request
from .response import Response
from .dictionary import CaseInsensitiveDict

class HttpAdapter:
    """
    A mutable :class:`HTTP adapter <HTTP adapter>` for managing client connections
    and routing requests.
    ...
    """

    __attrs__ = [
        "ip",
        "port",
        "conn",
        "connaddr",
        "routes",
        "request",
        "response",
    ]

    def __init__(self, ip, port, conn, connaddr, routes):
        """
        Initialize a new HttpAdapter instance.
        ...
        """

        #: IP address.
        self.ip = ip
        #: Port.
        self.port = port
        #: Connection
        self.conn = conn
        #: Conndection address
        self.connaddr = connaddr
        #: Routes
        self.routes = routes
        #: Request
        self.request = Request()
        #: Response
        self.response = Response()

    def handle_client(self, conn, addr, routes):
        """
        Handle an incoming client connection.
        ...
        """

        # Connection handler.
        self.conn = conn        
        # Connection address.
        self.connaddr = addr
        # Request handler
        req = self.request
        # Response handler
        resp = self.response

        # Handle the request
        # Tăng kích thước buffer để nhận cả header và body (nếu có)
        msg = conn.recv(4096).decode() 
        
        # Tách header và body
        try:
            header_part, body_part = msg.split('\r\n\r\n', 1)
        except ValueError:
            header_part = msg
            body_part = "" # Không có body
            
        req.prepare(header_part, routes) # Chỉ parse header
        req.body = body_part # Lưu body riêng

        #
        # --- BẮT ĐẦU PHẦN SỬA ĐỔI CHÍNH ---
        #
        response = None # Khởi tạo response

        # Handle request hook
        if req.hook:
            print("[HttpAdapter] hook in route-path METHOD {} PATH {}".format(req.hook._route_path, req.hook._route_methods))
            
            #
            # TODO: handle for App hook here
            try:
                api_response_dict = req.hook(headers=req.headers, body=req.body)
                
                json_body = json.dumps(api_response_dict)
                content_length = len(json_body)
                
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: application/json\r\n"
                    f"Content-Length: {content_length}\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                    f"{json_body}"
                ).encode('utf-8')

            except Exception as e:
                print(f"[HttpAdapter] Lỗi khi xử lý hook: {e}")
                # Xây dựng phản hồi lỗi 500 Internal Server Error
                error_body = json.dumps({"error": "Internal Server Error", "message": str(e)})
                response = (
                    "HTTP/1.1 500 Internal Server Error\r\n"
                    "Content-Type: application/json\r\n"
                    f"Content-Length: {len(error_body)}\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                    f"{error_body}"
                ).encode('utf-8')

        else:
            response = resp.build_response(req)

        #print(response)
        conn.sendall(response)
        conn.close()

    @property
    def extract_cookies(self, req, resp):
        """
        Build cookies from the :class:`Request <Request>` headers.
        ...
        """
        cookies = {}
        cookie_header = req.headers.get('cookie', '')
        if cookie_header:
            for pair in cookie_header.split(';'):
                try:
                    key, value = pair.strip().split("=")
                    cookies[key] = value
                except ValueError:
                    pass
        return cookies

    def build_response(self, req, resp):
        """Builds a :class:`Response <Response>` object 
        ...
        """
        response = Response()

        response.raw = resp
        response.reason = "OK"

        if isinstance(req.url, bytes):
            response.url = req.url.decode("utf-8")
        else:
            response.url = req.url

        response.cookies = self.extract_cookies(req, resp)
        response.request = req
        response.connection = self

        return response

    # def get_connection(self, url, proxies=None):
        # ... (giữ nguyên)

    def add_headers(self, request):
        """
        Add headers to the request.
        ...
        """
        pass

    def build_proxy_headers(self, proxy):
        """Returns a dictionary of the headers to add to any request sent
        through a proxy. 
        ...
        """
        headers = {}
        #
        # TODO: build your authentication here
        #       username, password =...
        # we provide dummy auth here
        #
        username, password = ("user1", "password")

        if username:
            # Cần chuẩn bị auth, không phải gán tuple
            # Ví dụ: Basic Auth (cần base64)
            # import base64
            # auth_str = f"{username}:{password}"
            # auth_b64 = base64.b64encode(auth_str.encode()).decode()
            # headers["Proxy-Authorization"] = f"Basic {auth_b64}"
            pass # Giữ nguyên logic TODO

        return headers