import json
import argparse

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
#

@app.route('/submit-info', methods=['POST'])
def submit_info(headers, body):
    """
    API để một peer mới tham gia và đăng ký thông tin (IP, port)
    với máy chủ tracker.
    [cite: 245, 262]
    """
    print(f"[ChatServer] Nhận yêu cầu /submit-info...")
    
    try:
        data = json.loads(body)
        
        peer_id = data.get("username")
        peer_ip = data.get("ip")
        peer_port = data.get("port")
        
        if peer_id and peer_ip and peer_port:
            peer_list[peer_id] = {"ip": peer_ip, "port": peer_port}
            print(f"[ChatServer] Peer đã đăng ký: {peer_id} -> {peer_ip}:{peer_port}")
            # Trả về thông báo thành công
            return {"status": "registered", "peer_id": peer_id}
        else:
            return {"status": "error", "message": "Missing username, ip, or port"}
            
    except json.JSONDecodeError:
        print("[ChatServer] Lỗi: Body không phải là JSON hợp lệ")
        return {"status": "error", "message": "Invalid JSON body"}
    except Exception as e:
        print(f"[ChatServer] Lỗi không xác định: {e}")
        return {"status": "error", "message": str(e)}

@app.route('/get-list', methods=['GET'])
def get_list(headers, body):
    """
    API để một peer yêu cầu danh sách tất cả các peer 
    khác đang hoạt động từ tracker.
    [cite: 247, 263]
    """
    print(f"[ChatServer] Nhận yêu cầu /get-list. Đang trả về {len(peer_list)} peers.")
    
    return {"status": "success", "peers": peer_list}

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