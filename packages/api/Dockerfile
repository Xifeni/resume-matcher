
FROM nvidia/cuda:12.8.0-cudnn-runtime-ubuntu22.04


WORKDIR /app

RUN apt-get update && apt-get install -y python3-pip git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip pip3 install --default-timeout=1000 -r requirements.txt

RUN --mount=type=cache,target=/root/.cache/huggingface \
    python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/e5-large-v2')"

COPY . .