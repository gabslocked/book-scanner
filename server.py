#!/usr/bin/env python3
"""Servidor simples para a app de leitura de código de barras"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler

def start_server():
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🚀 Servidor iniciado!")
        print(f"📱 Acesse via navegador do celular:")
        print(f"   http://<seu-ip>:{PORT}/book-scanner.html")
        print(f"\n💡 Para encontrar seu IP, execute em outro terminal:")
        print(f"   ifconfig | grep inet")
        print(f"\n   Ou em Mac:")
        print(f"   ipconfig getifaddr en0")
        print(f"\n🛑 Pressione Ctrl+C para parar o servidor")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✅ Servidor finalizado")
            sys.exit(0)

if __name__ == "__main__":
    start_server()
