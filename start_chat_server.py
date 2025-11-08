import json
import argparse
from db.account import select_user, create_connection
from daemon.request import Request
from daemon.response import Response
from urllib.parse import *
import subprocess

# Import lớp WeApRous từ module daemon
from daemon.weaprous import WeApRous

# Đặt một cổng mặc định cho máy chủ chat, khác với các máy chủ khác
PORT = 8001 

# Khởi tạo ứng dụng WeApRous
app = WeApRous()

# -------------------------------------------------------------------
# Đây là "database" tạm thời của máy chủ tracker 
# Nó sẽ lưu danh sách các peer đang hoạt động.
#
# Cấu trúc dữ liệu:
# peer_list = {
#     "username_cu_peer_A": {"ip": "192.168.1.10", "port": 9001},
#     "username_cu_peer_B": {"ip": "192.168.1.11", "port": 9002},
# }
# -------------------------------------------------------------------
peer_list = {}


# --- Giai đoạn 1: Client-Server (Tracker) ---

@app.route("/login", methods=["POST"])
def login(req):
    from urllib.parse import parse_qs
    parsed = parse_qs(req.body, keep_blank_values=True)

    username = parsed.get("username", [""])[0]
    password = parsed.get("password", [""])[0]

    conn = create_connection("db/account.db")
    auth = select_user(conn, username)
    resp = Response()
    print(f"[Server] Login attempt: {username}")
    if auth:
        if  password == auth[1]:
            # build login-success response (sets cookie + returns index)
            resp.cookies.clear()
            resp.cookies["auth"] = "true; Path=/"
            resp.cookies["username"] = username
            # Ensure request points to index for building content
            req.path = "/index.html"
            req.method = "GET"
            print(f"[Tracker] Login success: {username}")
            return resp.build_response(req)
        
    print(f"[Tracker] Login failed: {username}")
    return resp.build_unauthorized()

@app.route('/login', methods=['GET'])
def login_form(req):
    """
    Trả form đăng nhập (username, password)
    """
    print(f"[ChatServer] Nhận yêu cầu /submit-info...")
    
    try:
        req.path = "/login.html"
        return Response().build_response(req)
    except Exception as e:
        print(f"[ChatServer] Lỗi không xác định: {e}")
        return {"status": "error", "message": str(e)}


@app.route('/submit-info',methods=['GET'])
def submit_form(req):
    """
    Trả form một peer mới tham gia và đăng ký thông tin (IP, port)
    """
    try:
        req.path = "/submit.html"
        return Response().build_response(req)
    except Exception as e:
        print(f"[ChatServer] Lỗi không xác định: {e}")
        return {"status": "error", "message": str(e)}
    
@app.route('/submit-info', methods=['POST'])
def submit_info(req):
    """
    API để một peer mới tham gia và đăng ký thông tin (IP, port)
    với máy chủ tracker.
    [cite: 245, 262]
    """
    print(f"[ChatServer] Nhận yêu cầu /submit-info...")
    
    try:
        body = req.body
        data = parse_qs(body)
        # data = json.loads(body)
        peer_id = req.cookies.get("username")
        peer_ip = data.get("ip")[0]
        peer_port = data.get("port")[0]
        
        # subprocess.Popen([
        #     "gnome-terminal", "--", "python3", "start_chat_server.py",
        #     "--server-ip", peer_ip, "--server-port", peer_port
        # ])

        
        if peer_id and peer_ip and peer_port:
            peer_list[peer_id] = {"ip": peer_ip, "port": peer_port}
            print(peer_list)
            print(f"[ChatServer] Peer đã đăng ký: {peer_id} -> {peer_ip}:{peer_port}")
            resp = Response()
            return resp.build_success({"status": "success", "message": "Submit successfully."})
        else:
            return Response().build_bad_request({"status": "error", "message": "Missing ip, or port"})
            
    except json.JSONDecodeError:
        print("[ChatServer] Lỗi: Body không phải là JSON hợp lệ")
        return Response().build_bad_request({"status": "error", "message": "Invalid JSON body"})
    except Exception as e:
        print(f"[ChatServer] Lỗi không xác định: {e}")
        return Response().build_internal_error({"status": "error", "message": str(e)})

# @app.route('/get-list', methods=['GET'])
# def get_list(req):
#     """
#     API để một peer yêu cầu danh sách tất cả các peer 
#     khác đang hoạt động từ tracker.
#     [cite: 247, 263]
#     """
#     print(f"[ChatServer] Nhận yêu cầu /get-list. Đang trả về {len(peer_list)} peers.")
    
#     return Response().build_success({"status": "success", "peers": peer_list})

# @app.route('/get-list', methods=['GET'])
# def api_get_list(req):
#     print(f"[ChatServer] /get-list: {len(peer_list)} peers")
#     return Response().build_success({"status": "success", "peers": peer_list})

@app.route('/get-list', methods=['GET'])
def get_list(req):
    # trả dữ liệu peers
    data = {"status": "success", "peers": peer_list}
    body = json.dumps(data)
    content_length = len (body)
    # Thêm CORS header
    # headers = {
    #     "Content-Type": "application/json\r\n"
    #     "Access-Control-Allow-Origin": "*",  # hoặc chỉ định "http://127.0.0.1:9001"
    #     "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    #     "Access-Control-Allow-Headers": "Content-Type"
    # }
    return (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {content_length}\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        "Access-Control-Allow-Headers: Content-Type\r\n"
        "\r\n"
        f"{body}"
    ).encode("utf-8")

@app.route("/styles.css")
def style(req):
    resp = Response()
    return resp.build_response(req)
@app.route("/favicon.ico")
def style(req):
    resp = Response()
    return resp.build_response(req)

@app.route('/save-tracker', methods=['POST'])
def save_tracker(req):
    print(f"[ChatServer] Nhận yêu cầu /save-tracker...")
    resp = Response()
    try:
        data = json.loads(req.body)
        tracker_ip = data.get("trackerIP")
        tracker_port = data.get("trackerPort")
        if not tracker_ip or not tracker_port:
            return resp.build_bad_request({"error": "Missing tracker info"})
            
        # Lưu vào file tracker.json
        with open("tracker.json", "w") as f:
            json.dump({"trackerIP": tracker_ip, "trackerPort": tracker_port}, f)

        return resp.build_success({"status": "success"})

    except Exception as e:
        return resp.build_internal_error({"error": str(e)})

# def get_list(req):
#     print("get_list")
#     resp = Response()
#     return resp.build_success({"status": "success", "peers": peer_list})

# API trả HTML file
# @app.route('/peer-list', methods=['GET'])
# def peer_list_page(req):
#     print("Peer_list_page")
#     with open("www/peer_table.html", "r", encoding="utf-8") as f:
#         html = f.read()

#     resp = Response()
#     resp.status_code = 200
#     resp.headers = {"Content-Type": "text/html"}
#     resp.body = html
#     return resp.build_response(req)


# @app.route('/logout', methods=['POST'])
# def logout(req):
#     """
#     API để một peer thông báo rằng mình đã thoát (quit).
#     Server sẽ xóa peer này khỏi peer_list.
#     """
#     print(f"[ChatServer] Nhận yêu cầu /logout...")
    
#     try:
#         body = req.body
#         # Tệp httpadapter.py đã chuyển body thành chuỗi
#         data = json.loads(body)
#         peer_id = data.get("username")
        
#         # Kiểm tra xem peer có trong danh sách không
#         if peer_id in peer_list:
#             del peer_list[peer_id] # Xóa peer khỏi danh sách
#             print(f"[ChatServer] Peer đã thoát: {peer_id}. Danh sách còn lại {len(peer_list)} peers.")
#             return {"status": "logged_out", "peer_id": peer_id}
#         else:
#             print(f"[ChatServer] Peer {peer_id} yêu cầu logout nhưng không có trong danh sách.")
#             return {"status": "error", "message": "Peer not found"}
            
#     except json.JSONDecodeError:
#         print("[ChatServer] Lỗi: Body /logout không phải là JSON hợp lệ")
#         return {"status": "error", "message": "Invalid JSON body"}
#     except Exception as e:
#         print(f"[ChatServer] Lỗi /logout không xác định: {e}")
#         return {"status": "error", "message": str(e)}

# --- Khối khởi chạy máy chủ ---
if __name__ == "__main__":
    """
    Phần này tương tự như tệp start_sampleapp.py,
    dùng để parse tham số và khởi chạy máy chủ WeApRous.
   
    """

    parser = argparse.ArgumentParser(
        prog='ChatServer', 
        description='Start the Hybrid Chat Server (Tracker)', 
        epilog='Chat daemon for WeApRous application'
    )
    parser.add_argument('--server-ip', 
        type=str, 
        default='0.0.0.0', 
        help='IP address to bind the server. Default is 0.0.0.0'
    )
    parser.add_argument(
        '--server-port', 
        type=int, 
        default=PORT, 
        help=f'Port number to bind the server. Default is {PORT}.'
    )
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    print(f"[ChatServer] Đang khởi chạy máy chủ tracker tại http://{ip}:{port}")
    app.prepare_address(ip, port)
    app.run()