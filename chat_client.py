# chat_client.py (Da cap nhat cho Python 3)
import socket
import threading
import argparse
import http.client  # <--- DA SUA: Thu vien HTTP client cua Python 3
import json
import time

class ChatClient:
    def __init__(self, username, client_port, tracker_ip, tracker_port):
        self.username = username
        self.client_port = client_port
        self.tracker_ip = tracker_ip
        self.tracker_port = tracker_port
        self.peer_list = {}
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self.client_ip = s.getsockname()[0]
            s.close()
        except Exception:
            self.client_ip = '127.0.0.1'
            
        self.server_socket = None
        self.running = True

    def register_with_tracker(self):
        """
        Giai doan 1: Dang ky voi may chu Tracker (Client-Server)
        """
        print(f"[Client] Dang ky voi tracker tai {self.tracker_ip}:{self.tracker_port}...")
        
        payload = {
            "username": self.username,
            "ip": self.client_ip,
            "port": self.client_port
        }
        headers = {"Content-type": "application/json"}
        
        try:
            # <--- DA SUA: Su dung http.client.HTTPConnection
            conn = http.client.HTTPConnection(self.tracker_ip, self.tracker_port)
            
            # <--- DA SUA: body phai duoc encode sang bytes
            conn.request("POST", "/submit-info", json.dumps(payload).encode('utf-8'), headers)
            response = conn.getresponse()
            
            if response.status == 200:
                print("[Client] Dang ky thanh cong!")
            else:
                print(f"[Client] Loi dang ky: {response.status} {response.reason}")
            conn.close()
        except Exception as e:
            print(f"[Client] Khong the ket noi duoc tracker: {e}")

    def get_peer_list(self):
        """
        Giai doan 1: Lay danh sach peer tu Tracker (Client-Server)
        """
        try:
            # <--- DA SUA: Su dung http.client.HTTPConnection
            conn = http.client.HTTPConnection(self.tracker_ip, self.tracker_port)
            conn.request("GET", "/get-list")
            response = conn.getresponse()
            
            if response.status == 200:
                # <--- DA SUA: response.read() tra ve bytes, can decode
                data = json.loads(response.read().decode('utf-8'))
                self.peer_list = data.get("peers", {})
                print(f"[Client] Da cap nhat danh sach peer: {len(self.peer_list)} peers")
            conn.close()
        except Exception as e:
            print(f"[Client] Loi khi lay danh sach peer: {e}")

    def start_server(self):
        """
        Khoi chay may chu P2P de lang nghe tin nhan
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', self.client_port))
        self.server_socket.listen(5)
        print(f"[Client] Dang lang nghe P2P tren port {self.client_port}")
        
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_peer_connection, args=(conn, addr)).start()
            except socket.error:
                if self.running:
                    print("[Client] Loi server P2P")
                break
        print("[Client] Da dong server P2P.")

    def handle_peer_connection(self, conn, addr):
        """
        Xu ly tin nhan P2P den.
        """
        try:
            # <--- DA SUA: data nhan ve la bytes, can decode
            data = conn.recv(1024).decode('utf-8')
            if data:
                # \r de dua con tro ve dau dong, \n de xuong hang
                # flush=True de in ra ngay lap tuc
                print(f"\r[Tin nhan P2P tu {addr[0]}]: {data}\n[Ban]: ", end="", flush=True)
        except Exception as e:
            print(f"\r[Client] Loi khi nhan tin nhan P2P: {e}")
        finally:
            conn.close()

    def broadcast_message(self, message):
        """
        Giai doan 2: Gui tin nhan Broadcast den tat ca peer khac (P2P)
        """
        print("[Client] Dang broadcast...")
        self.get_peer_list()
        
        full_message = f"[{self.username}]: {message}"
        
        for peer_id, info in self.peer_list.items():
            if peer_id == self.username:
                continue
            
            peer_ip = info.get("ip")
            peer_port = int(info.get("port"))
            
            try:
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.connect((peer_ip, peer_port))
                # <--- DA SUA: Gui di du lieu da encode sang bytes
                peer_socket.sendall(full_message.encode('utf-8'))
                peer_socket.close()
            except Exception as e:
                print(f"[Client] Khong the gui den {peer_id} ({peer_ip}:{peer_port}): {e}")

    def start(self):
        """
        Khoi chay toan bo client
        """
        self.register_with_tracker()
        
        server_thread = threading.Thread(target=self.start_server)
        server_thread.daemon = True
        server_thread.start()
        
        try:
            while True:
                # <--- DA SUA: Su dung input() thay vi raw_input()
                msg = input("[Ban]: ")
                if msg.lower() == '/quit':
                    break
                if msg.lower() == '/list':
                    self.get_peer_list()
                    print(self.peer_list)
                    continue
                
                self.broadcast_message(msg)
        except KeyboardInterrupt:
            print("\n[Client] Dang thoat...")
        finally:
            self.running = False
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.client_ip, self.client_port))
                s.close()
            except:
                pass
            server_thread.join(1.0)
            print("[Client] Da thoat.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='P2P Chat Client')
    parser.add_argument('--username', required=True, help='Ten cua ban (bat buoc)')
    parser.add_argument('--port', type=int, required=True, help='Port P2P de ban lang nghe (bat buoc)')
    parser.add_argument('--tracker_ip', default='127.0.0.1', help='IP cua may chu tracker')
    parser.add_argument('--tracker_port', type=int, default=8001, help='Port cua may chu tracker (mac dinh 8001)')
    
    args = parser.parse_args()
    
    client = ChatClient(args.username, args.port, args.tracker_ip, args.tracker_port)
    client.start()