"""Serve only a disposable local account-screen preview; no auth provider is used."""
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PreviewHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if self.path in ('/', '/account-preview'):
            page = (ROOT / 'extension/popup.html').read_text(encoding='utf-8')
            page = page.replace('<head>', '<head><base href="/extension/">')
            page = page.replace('src="popup.js"', 'src="/preview/account-preview.mjs"')
            content = page.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        # Only serve the preview's public assets, never repository/config files.
        if not self.path.startswith(('/extension/', '/preview/')) or '..' in self.path:
            self.send_error(404)
            return
        resolved = Path(self.translate_path(self.path)).resolve()
        allowed = [(ROOT / folder).resolve() for folder in ('extension', 'preview')]
        if not any(resolved.is_relative_to(folder) for folder in allowed) or not resolved.is_file():
            self.send_error(404)
            return
        super().do_GET()


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', int(os.environ.get('ACCOUNT_PREVIEW_PORT', '8766'))), PreviewHandler)
    print(f'Mock account UI: http://127.0.0.1:{server.server_port}/account-preview', flush=True)
    server.serve_forever()
