FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for building Python packages (including cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      libffi-dev \
      libssl-dev \
      python3-dev \
      && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.4.2
RUN pip install "poetry==$POETRY_VERSION"

# Copy only dependency descriptors first for caching
COPY pyproject.toml poetry.lock ./

# Configure Poetry to create dependencies in the container’s environment (not a virtualenv)
RUN poetry config virtualenvs.create false \
    && poetry install --no-root

# Copy the rest of the application code
COPY . .

# Command to run the FastAPI server
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]