# Use Python 3.12 slim image as base (more recent than 3.9)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories that might be needed
RUN mkdir -p logs cache reports

# Create a non-root user with proper permissions
RUN useradd --create-home --shell /bin/bash --uid 1000 app \
    && chown -R app:app /app \
    && chmod -R 755 /app
USER app

# Expose port for Streamlit dashboard
EXPOSE 8501

# Default command to run the Streamlit dashboard
CMD ["streamlit", "run", "dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]