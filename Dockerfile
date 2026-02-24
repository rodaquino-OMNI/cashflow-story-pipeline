FROM python:3.11-slim

# System dependencies for weasyprint PDF generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy source code
COPY src/ src/
COPY config/ config/
COPY tests/ tests/

# Default: run the CLI
ENTRYPOINT ["python", "-m", "src.main"]
CMD ["--help"]
