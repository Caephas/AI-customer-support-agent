# Use a lightweight Python image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y curl build-essential && rm -rf /var/lib/apt/lists/*

# Install Poetry globally
RUN curl -sSL https://install.python-poetry.org | python3 -

# Ensure Poetry is available in the PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy only dependency files first (better caching)
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root

# Copy the rest of the application files
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run the application
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]