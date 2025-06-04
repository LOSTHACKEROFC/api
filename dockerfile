# Use official Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required by Playwright
RUN apt-get update && apt-get install -y \
    wget gnupg curl unzip fonts-liberation \
    libnss3 libatk-bridge2.0-0 libxss1 libasound2 libgtk-3-0 libgbm-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY requirements.txt .
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Install Playwright and its browser dependencies
RUN playwright install --with-deps

# Expose port for Flask
EXPOSE 5000

# Command to run the app
CMD ["python", "api.py"]
