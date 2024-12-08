# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install necessary packages
RUN apt-get update && apt-get install -y \
    python3-tk \
    xvfb \
    ghostscript \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . /usr/src/app

# Set the working directory
WORKDIR /usr/src/app

# Expose the port
EXPOSE 5001

# Run the application
CMD ["python", "app.py"]
