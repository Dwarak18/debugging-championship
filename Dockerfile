FROM python:3.12-slim

# Security: don't run as root
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install deps first (layer cache)
COPY requirements.txt requirements-webapp.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-webapp.txt

# Copy source
COPY --chown=appuser:appuser . .

# Init DB directory
RUN mkdir -p webapp/data && chown appuser:appuser webapp/data

USER appuser

EXPOSE 8000

# Startup: init DB then launch
CMD ["sh", "-c", "python -c 'from webapp.core.database import init_db; init_db()' && \
     uvicorn webapp.app:app --host 0.0.0.0 --port 8000 --workers 2 --proxy-headers"]
