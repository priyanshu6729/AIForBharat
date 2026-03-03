FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for models (optional)
RUN mkdir -p models

# Make start script executable
RUN chmod +x start.sh

# Expose port (Railway will override with $PORT)
EXPOSE 8000

# Use start script that properly handles PORT
CMD ["sh", "start.sh"]
