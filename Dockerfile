FROM python:3.11

# Set working directory
WORKDIR /app

# Install system dependencies needed for Playwright
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files first (better caching)
COPY pyproject.toml poetry.lock ./

# Install dependencies (no virtualenv inside Docker)
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --only main

# Install Playwright browsers
RUN playwright install firefox
RUN playwright install-deps firefox

# Copy project files
COPY . .

CMD ["python3", "Scrapers/main.py"]