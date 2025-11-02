FROM locustio/locust:latest

WORKDIR /mnt/locust

# Install additional requirements if needed
COPY requirements.txt /mnt/locust/
RUN pip install --no-cache-dir -r /mnt/locust/requirements.txt || true

EXPOSE 8089 5557

# Default command (can be overridden in docker-compose)
# locustfile.py is mounted as volume in docker-compose
# Note: Command is overridden in docker-compose.yml

