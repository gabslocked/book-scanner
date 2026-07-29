#!/usr/bin/env python3
"""Servidor do Parábola Scanner — serve o app e bloqueia listagem de diretório."""

import http.server
import os
import socketserver
from pathlib import Path

PORT = int(os.environ.get("PORT", 8000))
ROOT = Path(__file__).parent

ALLOWED = {"/index.html", "/books.js", "/books.json", "/favicon.ico"}


class AppHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/" or path == "/book-scanner.html":
            self.path = "/index.html"
        elif path not in ALLOWED:
            self.send_error(404)
            return
        super().do_GET()

    def end_headers(self):
        # sempre servir versão fresca do app após deploy
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def list_directory(self, path):
        self.send_error(404)
        return None


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), AppHandler) as httpd:
        print(f"Parábola Scanner rodando na porta {PORT}")
        httpd.serve_forever()
