FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /backend

# Copy application code
COPY . .

# Install uv deps
RUN uv sync --frozen

# Expose the API port
EXPOSE 9999

# Start the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9999"]
