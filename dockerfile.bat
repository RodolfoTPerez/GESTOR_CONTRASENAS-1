FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get install -y \
    build-essential libsqlcipher-dev sqlcipher && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements-secure.txt .
RUN pip install --no-cache-dir -r requirements-secure.txt
COPY . .
CMD ["python", "-m", "src.bootstrap"]