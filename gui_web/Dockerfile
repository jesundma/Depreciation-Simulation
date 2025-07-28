# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . .

# Expose port (default Flask port)
EXPOSE 8080

# Set environment variable for Flask
ENV FLASK_APP=gui_web/app.py

# Use gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "gui_web.app:app"]