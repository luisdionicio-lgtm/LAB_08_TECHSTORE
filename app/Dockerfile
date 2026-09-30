FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/lab07

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY docker-entrypoint.sh /usr/local/bin/lab07-entrypoint
RUN chmod +x /usr/local/bin/lab07-entrypoint

EXPOSE 80 8081 8082 8083

CMD ["/usr/local/bin/lab07-entrypoint"]
