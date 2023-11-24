# Use an official Python runtime as a parent image
FROM python:3.11.4-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system-level dependencies
RUN apt-get update && \
    apt-get install -y \
    libsm6 \
    libxext6 \
    libxrender-dev \
    build-essential \
    cmake \
    pkg-config \
    libcairo2-dev \
    libgl1-mesa-glx

# Set the working directory in the container
WORKDIR /app

# Copy the local code to the container
COPY . /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y libpq-dev
    
# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Expose the port the app runs on
EXPOSE 8000

# Start the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]