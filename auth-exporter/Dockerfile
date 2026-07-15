FROM python:3.13-alpine

RUN apk --no-cache add tzdata

WORKDIR /app
COPY requirements.txt app.py ./
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1
EXPOSE 9101
CMD ["python3", "app.py"]
