"""Imita a Drive API (alt=media) com CORS, exigindo o token, e entrega o
vídeo devagar para o teste ver o player começar pelo mp3."""
import json, sys, time, os
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
DIR = sys.argv[1]; PORTA = int(sys.argv[2])
dados = json.load(open(os.path.join(DIR, 'carregar.json')))
ARQ = {m['id']: os.path.join(DIR, m['nome']) for m in dados['midias']}
ARQ.update({p['id']: os.path.join(DIR, 'pdf', p['nome']) for p in dados.get('pdfs', [])})
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Authorization')
    def do_OPTIONS(self):
        self.send_response(204); self.cors(); self.end_headers()
    def do_GET(self):
        u = urlparse(self.path)
        fid = u.path.rsplit('/', 1)[-1]
        if self.headers.get('Authorization') != 'Bearer token-de-teste':
            self.send_response(401); self.cors(); self.end_headers(); self.wfile.write(b'{"error":"auth"}'); return
        if fid not in ARQ or 'alt=media' not in u.query:
            self.send_response(404); self.cors(); self.end_headers(); return
        corpo = open(ARQ[fid], 'rb').read()
        self.send_response(200); self.cors()
        self.send_header('Content-Type', 'video/mp4' if ARQ[fid].endswith('mp4') else 'application/pdf' if ARQ[fid].endswith('pdf') else 'audio/mpeg')
        self.send_header('Content-Length', str(len(corpo))); self.end_headers()
        devagar = ARQ[fid].endswith('.mp4')
        try:
            for i in range(0, len(corpo), 256 * 1024):
                self.wfile.write(corpo[i:i + 256 * 1024])
                if devagar: time.sleep(0.12)     # ~2 MB/s
        except (BrokenPipeError, ConnectionResetError):
            pass                                  # o player cancelou o download (troca de mídia/recarga)
ThreadingHTTPServer(('127.0.0.1', PORTA), H).serve_forever()
