# Use a lightweight Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# Set the working directory
WORKDIR /app

# Copy application files
COPY . .

# Expose the required port
EXPOSE 8080

# Start the Flask application using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "main:app"]
