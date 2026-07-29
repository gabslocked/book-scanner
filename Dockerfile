FROM python:3.11-slim

WORKDIR /app

COPY index.html books.js server.py sw.js manifest.webmanifest ./
COPY embeddings.bin embeddings.json icon-192.png icon-512.png ./
COPY vendor vendor
COPY model model
COPY thumbs thumbs

EXPOSE 8000

CMD ["python3", "server.py"]
