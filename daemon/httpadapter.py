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

    # def handle_client(self, conn, addr, routes):
    #     """
    #     Handle an incoming client connection.
    #     ...
    #     """

    #     # Connection handler.
    #     self.conn = conn        
    #     # Connection address.
    #     self.connaddr = addr
    #     # Request handler
    #     req = self.request
    #     # Response handler
    #     resp = self.response

    #     # Handle the request
    #     # Tăng kích thước buffer để nhận cả header và body (nếu có)
    #     msg = conn.recv(4096).decode() 
        
    #     # Tách header và body
    #     try:
    #         header_part, body_part = msg.split('\r\n\r\n', 1)
    #     except ValueError:
    #         header_part = msg
    #         body_part = "" # Không có body
            
    #     req.prepare(header_part, routes) # Chỉ parse header
    #     req.body = body_part # Lưu body riêng

    #     #
    #     # --- BẮT ĐẦU PHẦN SỬA ĐỔI CHÍNH ---
    #     #
    #     response = None # Khởi tạo response

    #     # Handle request hook
    #     if req.hook:
    #         print("[HttpAdapter] hook in route-path METHOD {} PATH {}".format(req.hook._route_path, req.hook._route_methods))
            
    #         #
    #         # TODO: handle for App hook here
    #         # ĐÃ HIỆN THỰC:
    #         # 1. Gọi hàm hook (ví dụ: submit_info) với header VÀ body của request
    #         # 2. Lấy kết quả trả về (dưới dạng 'dict')
    #         #
    #         try:
    #             api_response_dict = req.hook(headers=req.headers, body=req.body)
                
    #             # 3. Chuyển dict thành chuỗi JSON
    #             json_body = json.dumps(api_response_dict)
    #             content_length = len(json_body)
                
    #             # 4. Xây dựng phản hồi HTTP 200 OK với nội dung là JSON
    #             response = (
    #                 "HTTP/1.1 200 OK\r\n"
    #                 "Content-Type: application/json\r\n"
    #                 f"Content-Length: {content_length}\r\n"
    #                 "Connection: close\r\n"
    #                 "\r\n"
    #                 f"{json_body}"
    #             ).encode('utf-8')

    #         except Exception as e:
    #             print(f"[HttpAdapter] Lỗi khi xử lý hook: {e}")
    #             # Xây dựng phản hồi lỗi 500 Internal Server Error
    #             error_body = json.dumps({"error": "Internal Server Error", "message": str(e)})
    #             response = (
    #                 "HTTP/1.1 500 Internal Server Error\r\n"
    #                 "Content-Type: application/json\r\n"
    #                 f"Content-Length: {len(error_body)}\r\n"
    #                 "Connection: close\r\n"
    #                 "\r\n"
    #                 f"{error_body}"
    #             ).encode('utf-8')

    #     else:
    #         #
    #         # Nếu KHÔNG có hook, đây là yêu cầu file tĩnh (ví dụ: /index.html)
    #         # Giữ nguyên logic cũ:
    #         #
    #         # Build response
    #         response = resp.build_response(req)

    #     # --- KẾT THÚC PHẦN SỬA ĐỔI ---
    #     #

    #     #print(response)
    #     conn.sendall(response)
    #     conn.close()

    def handle_client(self, conn, addr, routes):
        """
        Handle an incoming client connection.
        - read headers and full body (Content-Length aware)
        - parse request and cookies
        - implement POST /login logic (validate credentials, set cookie or 401)
        - implement GET / or /index.html cookie check (auth=true => serve index, else 401)
        - call app hook when present
        - fallback to static file serving via Response.build_response
        """
        self.conn = conn
        self.connaddr = addr
        req = self.request
        resp = self.response

        # Read headers first (until \r\n\r\n)
        conn.settimeout(2)
        raw = b""
        try:
            while b"\r\n\r\n" not in raw:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                raw += chunk
        except Exception:
            pass

        # If no data, close
        if not raw:
            try:
                conn.close()
            except Exception:
                pass
            return

        # Decode headers safely
        header_end = raw.find(b"\r\n\r\n")
        header_bytes = raw[:header_end + 4] if header_end != -1 else raw
        try:
            header_text = header_bytes.decode("utf-8", errors="replace")
        except Exception:
            header_text = header_bytes.decode("latin1", errors="replace")

        # Prepare request (parses request-line, headers)
        req.prepare(header_text, routes)

        # Determine if there's a body to read (Content-Length)
        content_length = 0
        cl = req.headers.get("content-length")
        if cl:
            try:
                content_length = int(cl)
            except Exception:
                content_length = 0

        # Already-read remainder after headers
        body_already = raw[header_end + 4:] if header_end != -1 else b""
        body = body_already
        to_read = content_length - len(body)
        # Read remaining body if needed
        try:
            while to_read > 0:
                chunk = conn.recv(min(4096, to_read))
                if not chunk:
                    break
                body += chunk
                to_read -= len(chunk)
        except Exception:
            pass

        # Store body as decoded string (utf-8 fallback to latin1)
        try:
            req.body = body.decode("utf-8", errors="replace")
        except Exception:
            req.body = body.decode("latin1", errors="replace")

        # Now business logic: login + cookie-protected index
        try:
            # Normalize path: treat "/" as "/index.html"
            path = req.path
            if path == "/":
                path = "/index.html"
                req.path = path

            # Helper: send raw bytes and close
            def send_and_close(data_bytes):
                try:
                    conn.sendall(data_bytes)
                except Exception:
                    pass
                try:
                    conn.close()
                except Exception:
                    pass

            # Task 1A: POST /login
            if req.method == "POST" and req.path == "/login":
                # parse form body (application/x-www-form-urlencoded)
                from urllib.parse import parse_qs
                parsed = parse_qs(req.body, keep_blank_values=True)
                username = parsed.get("username", [""])[0]
                password = parsed.get("password", [""])[0]

                if username == "admin" and password == "password":
                    # build login-success response (sets cookie + returns index)
                    resp.cookies.clear()
                    resp.cookies["auth"] = "true; Path=/"
                    # Ensure request points to index for building content
                    req.path = "/index.html"
                    req.method = "GET"
                    result = resp.build_response(req)
                    send_and_close(result)
                    return
                else:
                    # invalid credentials -> 401
                    result = resp.build_unauthorized()
                    send_and_close(result)
                    return

            # Task 1B: GET /index.html (or /)
            if req.method == "GET" and req.path in ["/index.html"]:
                # check cookie auth
                cookie_val = req.cookies.get("auth", "")
                # handle cases like "true" or "true; Path=/" if set that way
                is_auth = False
                if cookie_val:
                    if cookie_val.split(";", 1)[0].strip() == "true":
                        is_auth = True
                if not is_auth:
                    # not authorized
                    result = resp.build_unauthorized()
                    send_and_close(result)
                    return
                # else authorized -> serve index via build_response
                result = resp.build_response(req)
                send_and_close(result)
                return

            # If a webapp hook is present, call it (we expect a dict -> JSON)
            if req.hook:
                try:
                    api_response = req.hook(headers=req.headers, body=req.body)
                    import json
                    json_body = json.dumps(api_response)
                    content_length = len(json_body.encode("utf-8"))
                    response_bytes = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: application/json\r\n"
                        f"Content-Length: {content_length}\r\n"
                        "Connection: close\r\n"
                        "\r\n"
                        f"{json_body}"
                    ).encode("utf-8")
                    send_and_close(response_bytes)
                    return
                except Exception as e:
                    import json
                    err = json.dumps({"error": "Internal Server Error", "message": str(e)})
                    response_bytes = (
                        "HTTP/1.1 500 Internal Server Error\r\n"
                        "Content-Type: application/json\r\n"
                        f"Content-Length: {len(err.encode('utf-8'))}\r\n"
                        "Connection: close\r\n"
                        "\r\n"
                        f"{err}"
                    ).encode("utf-8")
                    send_and_close(response_bytes)
                    return

            # Fallback: static file serving
            result = resp.build_response(req)
            send_and_close(result)
            return

        except Exception as e:
            # On unexpected error, return 500
            body = b"Internal Server Error"
            header = (
                "HTTP/1.1 500 Internal Server Error\r\n"
                "Content-Type: text/plain\r\n"
                f"Content-Length: {len(body)}\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).encode("utf-8")
            try:
                conn.sendall(header + body)
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
            return

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
                    cookies[key.strip()] = value.strip()
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