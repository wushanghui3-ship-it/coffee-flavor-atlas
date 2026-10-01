FROM node:22-bookworm-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python3 -m pip install --break-system-packages --no-cache-dir -r requirements.txt

COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN npm --prefix frontend ci

COPY frontend ./frontend
RUN npm --prefix frontend run build

COPY server.py render.yaml ./
COPY data ./data

ENV HOST=0.0.0.0
ENV PORT=7860
ENV COOKIE_SECURE=true

EXPOSE 7860
CMD ["python3", "server.py"]
