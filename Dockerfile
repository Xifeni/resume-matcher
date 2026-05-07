FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

WORKDIR /app

RUN apt-get update && apt-get install -y python3-pip git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip pip3 install -r requirements.txt

RUN --mount=type=cache,target=/root/.cache/huggingface \
    python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/e5-large-v2')"

RUN --mount=type=cache,target=/root/.cache/huggingface \
    python3 -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='TheBloke/Llama-2-7B-Chat-AWQ')"

COPY . .