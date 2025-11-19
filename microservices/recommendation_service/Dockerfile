FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for TensorFlow
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install build tools first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements and install Python dependencies
# Install numpy first (TensorFlow dependency), then TensorFlow, then rest
COPY requirements.txt .
RUN pip install --no-cache-dir "numpy<1.24.0" && \
    pip install --no-cache-dir tensorflow==2.13.0 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p checkpoints data

# Expose port
EXPOSE 5001

# Run the application
CMD ["python", "app.py"]
