import http.server
import socketserver
import sqlite3
import json
import urllib.parse
from http import cookies
import secrets
import hashlib

# Database initialization
def init_db():
    conn = sqlite3.connect('pharma.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id TEXT PRIMARY KEY, 
                  password TEXT NOT NULL,
                  full_name TEXT NOT NULL,
                  mobile TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

class PharmaHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('static/login.html', 'rb') as f:
                self.wfile.write(f.read())
        elif self.path == '/dashboard':
            # Check session cookie here
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('static/dashboard.html', 'rb') as f:
                self.wfile.write(f.read())
        else:
            super().do_GET()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        data = urllib.parse.parse_qs(post_data)

        if self.path == '/register':
            try:
                user_id = data['user_id'][0]
                password = hash_password(data['password'][0])
                full_name = data['full_name'][0]
                mobile = data['mobile'][0]

                conn = sqlite3.connect('pharma.db')
                c = conn.cursor()
                c.execute('INSERT INTO users VALUES (?, ?, ?, ?)',
                         (user_id, password, full_name, mobile))
                conn.commit()
                conn.close()

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode())
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())

        elif self.path == '/login':
            try:
                user_id = data['user_id'][0]
                password = hash_password(data['password'][0])

                conn = sqlite3.connect('pharma.db')
                c = conn.cursor()
                c.execute('SELECT * FROM users WHERE user_id = ? AND password = ?',
                         (user_id, password))
                user = c.fetchone()
                conn.close()

                if user:
                    session_token = secrets.token_hex(16)
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Set-Cookie', f'session={session_token}')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': True,
                        'user': {
                            'user_id': user[0],
                            'full_name': user[2]
                        }
                    }).encode())
                else:
                    self.send_response(401)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': False,
                        'error': 'Invalid credentials'
                    }).encode())
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())

if __name__ == '__main__':
    init_db()
    PORT = 8000
    with socketserver.TCPServer(("", PORT), PharmaHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        httpd.serve_forever()