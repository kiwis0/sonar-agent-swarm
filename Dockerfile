FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY sonar_agent/ sonar_agent/
CMD ["python", "sonar_agent/main.py"]