FROM python:3.10-slim

ENV PORT=5051
ENV HOST=localhost
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

EXPOSE $PORT

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY .. .

CMD gunicorn main:app -b 0.0.0.0:$PORT -k uvicorn.workers.UvicornWorker -w 1

#HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD curl -f $HOST:$PORT/health

# docker build . -t toxic_ort_api:latest
# docker run --name='toxic_ort_api' -d -p 5555:5051 toxic_ort_api:latest
