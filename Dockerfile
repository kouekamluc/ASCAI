# Multi-stage Dockerfile for ASCAI Platform
# Stage 1: Frontend build stage
FROM node:20-alpine as frontend-builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./
COPY tailwind.config.js postcss.config.js ./

# Install Node dependencies
RUN npm ci --only=production

# Copy source files
COPY static/src/tailwind.css static/src/

# Build Tailwind CSS
RUN npm run build

# Stage 2: Python build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 3: Runtime stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/ascai/.local/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq-dev \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 ascai && \
    mkdir -p /app /app/staticfiles /app/media /app/logs && \
    chown -R ascai:ascai /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/ascai/.local

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=ascai:ascai . .

# Copy built Tailwind CSS from frontend builder
COPY --from=frontend-builder --chown=ascai:ascai /app/static/css/tailwind-built.css static/css/tailwind-built.css

# Switch to non-root user
USER ascai

# Expose port
EXPOSE 8000

# Make start.sh executable
RUN chmod +x start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Default command (runs migrations, collectstatic, and starts Gunicorn)
CMD ["./start.sh"]

