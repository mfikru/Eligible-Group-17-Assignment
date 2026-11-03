# Streamlit app. Build: docker build -t house-price-app .   Run: docker run -p 8501:8501 -v prices_log:/data house-price-app
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY housing.py artifacts.py prediction_log.py app.py ./
COPY models ./models
COPY reports/metrics.json ./reports/metrics.json
ENV PRICE_LOG_DB=/data/predictions.db
VOLUME /data
EXPOSE 8501
HEALTHCHECK CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8501/_stcore/health')"
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
