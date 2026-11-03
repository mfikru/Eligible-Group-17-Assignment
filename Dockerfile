# Optional deployment: build after training so models/ exists.
#   docker build -t house-price .
#   docker run -p 8501:8501 house-price                                  (Streamlit)
#   docker run -p 8000:8000 house-price uvicorn api:app --host 0.0.0.0   (API)
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/
COPY monitoring/ monitoring/
COPY models/ models/
COPY app.py api.py ./
EXPOSE 8501 8000
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
