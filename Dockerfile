# Stage 1: Build dependencies
FROM python:3.13-alpine AS builder

WORKDIR /app

# Update Alpine packages & install build dependencies
RUN apk update && apk upgrade && \
    apk add --no-cache gcc musl-dev libffi-dev postgresql-dev expat-dev

# Copy only requirements for caching
COPY requirement.txt .

# Install Python dependencies in a temporary directory
RUN pip install --no-cache-dir --prefix=/install -r requirement.txt

# Stage 2: Production image
FROM python:3.13-alpine

WORKDIR /app

# Update system packages & install minimal runtime dependencies
RUN apk update && apk upgrade && \
    apk add --no-cache libpq expat

# Copy installed dependencies from builder stage
COPY --from=builder /install /usr/local

# Copy the application code
COPY . .

# Expose Flask's default port
EXPOSE 5000

# Use Gunicorn as the WSGI server
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
