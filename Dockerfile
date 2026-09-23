# WindAgent: agentic 24-48 h wind-power forecasting. Everything needed for the replay
# (weather cache, trained model, SCADA data) is inside the image; no network or keys required.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

# LightGBM needs OpenMP at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN chmod +x docker/entrypoint.sh

EXPOSE 8501
ENTRYPOINT ["docker/entrypoint.sh"]
CMD ["check"]
