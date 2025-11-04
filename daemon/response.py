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
daemon.response
~~~~~~~~~~~~~~~~~

This module provides a :class: `Response <Response>` object to manage and persist 
response settings (cookies, auth, proxies), and to construct HTTP responses
based on incoming requests. 

The current version supports MIME type detection, content loading and header formatting
"""
import datetime
import os
import mimetypes
from .dictionary import CaseInsensitiveDict

# <--- ĐÃ SỬA: BASE_DIR được đặt là "" để biểu thị thư mục gốc
# Nơi start_backend.py được chạy.
# Các thư mục con www/ và static/ sẽ được nối vào đây.
BASE_DIR = ""

class Response():   
    """The :class:`Response <Response>` object, which contains a
    server's response to an HTTP request.
    ...
    """

    __attrs__ = [
        "_content",
        "_header",
        "status_code",
        "method",
        "headers",
        "url",
        "history",
        "encoding",
        "reason",
        "cookies",
        "elapsed",
        "request",
        "body",
        "reason",
    ]


    def __init__(self, request=None):
        """
        Initializes a new :class:`Response <Response>` object.

        : params request : The originating request object.
        """

        self._content = b"" # <--- ĐÃ SỬA: Khởi tạo là bytes
        self._content_consumed = False
        self._next = None

        #: Integer Code of responded HTTP Status, e.g. 404 or 200.
        self.status_code = None

        #: Case-insensitive Dictionary of Response Headers.
        #: For example, ``headers['content-type']`` will return the
        #: value of a ``'Content-Type'`` response header.
        self.headers = {}

        #: URL location of Response.
        self.url = None

        #: Encoding to decode with when accessing response text.
        self.encoding = None

        #: A list of :class:`Response <Response>` objects from
        #: the history of the Request.
        self.history = []

        #: Textual reason of responded HTTP Status, e.g. "Not Found" or "OK".
        self.reason = None

        #: A of Cookies the response headers.
        # <--- ĐÃ SỬA: Khởi tạo CaseInsensitiveDict cho cookies
        # Điều này rất quan trọng cho Task 2.1 (Cookie Session)
        self.cookies = CaseInsensitiveDict() 

        #: The amount of time elapsed between sending the request
        self.elapsed = datetime.timedelta(0)

        #: The :class:`PreparedRequest <PreparedRequest>` object to which this
        #: is a response.
        self.request = None


    def get_mime_type(self, path):
        """
        Determines the MIME type of a file based on its path.

        "params path (str): Path to the file.

        :rtype str: MIME type string (e.g., 'text/html', 'image/png').
        """

        try:
            mime_type, _ = mimetypes.guess_type(path)
        except Exception:
            return 'application/octet-stream'
        
        # <--- ĐÃ SỬA: Xử lý trường hợp .ico
        if path.endswith('.ico'):
            return 'image/x-icon'
            
        return mime_type or 'application/octet-stream'


    def prepare_content_type(self, mime_type='text/html'):
        """
        Prepares the Content-Type header and determines the base directory
        for serving the file based on its MIME type.
        ...
        """
        
        base_dir = ""

        # <--- ĐÃ SỬA: Logic xử lý MIME type được viết lại cho rõ ràng
        
        # Đặt header Content-Type trước
        self.headers['Content-Type'] = str(mime_type)

        # Xác định thư mục dựa trên MIME type
        if mime_type == 'text/html':
            base_dir = BASE_DIR + "www/"
        elif mime_type == 'text/css' or mime_type == 'application/javascript':
            base_dir = BASE_DIR + "static/"
        elif mime_type.startswith('image/'):
            base_dir = BASE_DIR + "static/"
        elif mime_type.startswith('application/'):
            # Dành cho các tệp ứng dụng (ví dụ: /login API trả về JSON)
            # Nhưng logic đó đã được xử lý trong httpadapter.py
            # Ở đây chúng ta giả định là file tĩnh
            base_dir = BASE_DIR + "apps/"
        else:
            # Các loại file khác không được hỗ trợ
            raise ValueError(f"Invalid MIME type: {mime_type}")

        print(f"[Response] processing MIME {mime_type} from base_dir {base_dir}")
        return base_dir


    def build_content(self, path, base_dir):
        """
        Loads the objects file from storage space.
        ...
        """

        # filepath = os.path.join(base_dir, path.lstrip('/'))
        # Lược bỏ dấu / ở đầu path
        rel_path = path.lstrip('/')

        # Tạo đường dẫn mục tiêu và chuẩn hóa
        target = os.path.join(base_dir, rel_path)

        # SỬA: thay vì kiểm tra chuỗi '..', dùng realpath + commonpath để an toàn
        base_real = os.path.realpath(base_dir)
        target_real = os.path.realpath(target)

        # Nếu target không nằm trong base -> từ chối

        # Đảm bảo đường dẫn là an toàn (không đi ngược thư mục)
        # if '..' in filepath:
        if not os.path.commonpath([base_real]) == os.path.commonpath([base_real, target_real]):
            # Không cho phép truy cập ra ngoài base_dir
            raise IOError("File path is not allowed")

        # print("[Response] serving the object at location {}".format(filepath))
        print("[Response] serving the object at location {}".format(target_real))
            
        #
        #  TODO: implement the step of fetch the object file
        #        store in the return value of content
        #
        # <--- ĐÃ SỬA: Hoàn thành TODO ---
        content = b""
        # Mở tệp ở chế độ 'rb' (read binary) vì chúng ta cần gửi bytes
        with open(target_real, 'rb') as f:
            content = f.read()
        
        return len(content), content


    def build_response_header(self, request):
        """
        Constructs the HTTP response headers based on the class:`Request <Request>
        and internal attributes.
        ...
        """
        
        # <--- ĐÃ SỬA: Viết lại toàn bộ logic xây dựng header
        
        # 1. Tạo dòng trạng thái (Status Line)
        status_line = f"HTTP/1.1 {self.status_code} {self.reason}\r\n"
        
        # 2. Thêm các header từ self.headers (đã được đặt ở các hàm khác)
        header_lines = []
        
        # Thêm header 'Date'
        self.headers['Date'] = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        self.headers['Server'] = "BKSysNet-Server (Python)"
        
        for key, value in self.headers.items():
            header_lines.append(f"{key}: {value}")
            
        # 3. Thêm các cookie (Rất quan trọng cho Task 2.1)
        for key, value in self.cookies.items():
            # Ví dụ: Set-Cookie: auth=true
            header_lines.append(f"Set-Cookie: {key}={value}")
            
        # 4. Ghép tất cả lại
        # Nối các dòng header bằng \r\n, và kết thúc bằng một dòng trống \r\n
        fmt_header = status_line + "\r\n".join(header_lines) + "\r\n\r\n"
        
        return fmt_header.encode('utf-8')


    def build_notfound(self):
        """
        Constructs a standard 404 Not Found HTTP response.
        ...
        """

        return (
                "HTTP/1.1 404 Not Found\r\n"
                "Accept-Ranges: bytes\r\n"
                "Content-Type: text/html\r\n"
                "Content-Length: 13\r\n"
                "Cache-Control: max-age=86000\r\n"
                "Connection: close\r\n"
                "\r\n"
                "404 Not Found"
            ).encode('utf-8')


    def build_response(self, request):
        """
        Builds a full HTTP response including headers and content based on the request.
        ...
        """

        path = request.path
        mime_type = self.get_mime_type(path)
        print("[Response] {} path {} mime_type {}".format(request.method, request.path, mime_type))

        base_dir = ""
        c_len = 0

        # <--- ĐÃ SỬA: Logic được viết lại để xử lý lỗi và các loại tệp
        try:
            # 1. Chuẩn bị content-type và thư mục
            base_dir = self.prepare_content_type(mime_type)
            
            # 2. Tải nội dung tệp
            c_len, self._content = self.build_content(path, base_dir)

            # 3. Nếu thành công, đặt status 200 OK
            self.status_code = 200
            self.reason = "OK"
            self.headers['Content-Length'] = c_len
            self.headers['Connection'] = "close" # Đóng kết nối sau khi gửi

        except (IOError, FileNotFoundError, ValueError) as e:
            # 4. Nếu có lỗi (Không tìm thấy tệp, MIME không hỗ trợ)
            print(f"[Response] Error serving file {path}: {e}")
            return self.build_notfound()
        
        # 5. Xây dựng header
        self._header = self.build_response_header(request)

        # 6. Trả về header + nội dung
        return self._header + self._content
    
    def build_unauthorized(self):
        """
        Xây dựng phản hồi 401 Unauthorized (Task 1A & 1B).
        [cite: 174, 178]
        """
        self.status_code = 401
        self.reason = "Unauthorized"
        content = b"401 Unauthorized"

        headers = (
            f"HTTP/1.1 {self.status_code} {self.reason}\r\n"
            "Content-Type: text/plain\r\n"
            f"Content-Length: {len(content)}\r\n"
            "Connection: close\r\n"
            "\r\n"
        )

        return headers.encode('utf-8') + content

    def build_login_success(self, request):
        """
        Xây dựng phản hồi cho việc đăng nhập thành công (Task 1A).
        Phản hồi này sẽ trả về trang index VÀ đặt cookie.
        [cite: 173]
        """

        # 1. Đặt cookie 'auth=true' [cite: 173]
        # Hàm build_response_header sẽ tự động đọc từ self.cookies
        self.cookies['auth'] = 'true; Path=/'

        # 2. "Giả mạo" request để làm cho build_response
        # trả về trang /index.html [cite: 173]
        request.path = "/index.html"
        request.method = "GET"

        # 3. Gọi hàm build_response thông thường
        # Hàm này sẽ đọc path mới, lấy tệp index.html
        # và build_response_header sẽ đọc cookie chúng ta vừa set
        return self.build_response(request)