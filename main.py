from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import pathlib
import socket
import datetime
import json
import threading

UDP_IP = '127.0.0.1'
UDP_PORT = 5000

class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):           
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))

        print(data)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(data, (UDP_IP, UDP_PORT))
        sock.close()

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()
            

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):              #статична фуцнкція яка обробляє картиинку і css файл
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

def run(server_class=HTTPServer, handler_class=HttpHandler):  #  Локальний сервер 
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

def run_server(ip, port): # udp сервер
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.bind(server)

    try:
        while True:
            data, address = sock.recvfrom(1024)
            print(f'Received data: {data.decode()} from: {address}')
            data_parse = urllib.parse.unquote_plus(data.decode())
            data_dict = {
                key: value
                for key, value in [
                    element.split('=') for element in data_parse.split('&')
                ]
            }
            print(data_dict)
            path = pathlib.Path('storage')
            
            file_path = path / 'data.json'
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as file:     
                    storage_file = json.load(file)
            storage_file[str(datetime.datetime.now())] = data_dict

            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(storage_file, file, ensure_ascii=False)   # Записуємо у json 

    except KeyboardInterrupt:
        print('Destroy server')

    finally:
        sock.close()

if __name__ == '__main__':
    path = pathlib.Path('storage')
    path.mkdir(exist_ok=True)
    file_path = path / 'data.json'
    if not file_path.exists():
        with open (file_path,"w", encoding="utf-8") as  file: # Якщо немає json - тсворюємо
            json.dump({}, file)

    http_thread = threading.Thread(target=run)                #Робимо два потоки для серверу і udp серверу
    udp_thread = threading.Thread(target=run_server,args=(UDP_IP, UDP_PORT))

    http_thread.start()
    udp_thread.start()

    http_thread.join()
    udp_thread.join()