# Stage 1: Build environment
FROM python:3.11 AS builder

WORKDIR /app

# Copy only requirements to leverage Docker caching
COPY requirement.txt ./

# Install dependencies in a temporary directory
RUN pip install --no-cache-dir --prefix=/install -r requirement.txt

# Stage 2: Production-ready image
FROM python:3.11-slim

WORKDIR /app

# Copy installed dependencies from the builder stage
COPY --from=builder /install /usr/local

# Copy application files
COPY . .

# Expose the Flask default port
EXPOSE 5000

# Set environment variables (configured via Docker Compose)
# ENV FLASK_APP=app.py
# ENV FLASK_ENV=production

# Use Gunicorn as the WSGI server
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]