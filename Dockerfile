FROM python:3.11-slim

WORKDIR /app

COPY index.html books.js server.py ./

EXPOSE 8000

CMD ["python3", "server.py"]
