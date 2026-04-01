FROM python:3.12-slim

WORKDIR /app

# Install system deps for Playwright and BeautifulSoup
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency manifest first — maximises Docker layer cache.
# Re-runs pip only when pyproject.toml changes, not on every code edit.
COPY pyproject.toml .
# Create a minimal stub so hatchling can resolve the package without the full source
RUN mkdir -p app && touch app/__init__.py
RUN pip install --no-cache-dir ".[dev]"

# Playwright browsers (only Chromium needed for careers page scraping)
RUN playwright install chromium --with-deps

# Copy full source code last (layer invalidated only when code changes)
COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
