FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ ./agent/

ENV PYTHONUNBUFFERED=1
WORKDIR /app/agent

# Pre-download model weights (Silero VAD etc.) so they're baked into the image
RUN python agent.py download-files

CMD ["python", "agent.py", "start"]
