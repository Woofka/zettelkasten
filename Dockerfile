FROM python:3.9.13-slim

ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Yekaterinburg

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY static ./static
COPY templates ./templates
COPY *.py .

ENTRYPOINT ["python3", "main.py"]
