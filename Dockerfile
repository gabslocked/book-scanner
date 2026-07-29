FROM python:3.11-slim

WORKDIR /app

# Copiar arquivos da app
COPY book-scanner.html .
COPY server.py .
COPY README.md .

# Exposar porta
EXPOSE 8000

# Comando pra rodar
CMD ["python3", "server.py"]
