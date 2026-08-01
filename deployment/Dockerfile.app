FROM python:3.11-slim

WORKDIR /workspace/apps/yemen_complaints
COPY . /workspace/apps/yemen_complaints

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

CMD ["bash", "-lc", "echo 'This image is intended to be used inside a Frappe/Bench environment with the app mounted or copied into apps/' && sleep infinity"]
