# Use a slim Python image for a smaller footprint
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required for compilation and git
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install 'uv' for ultra-fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first to leverage Docker cache
COPY pyproject.toml .
COPY requirements.txt .

# Install Python dependencies using uv
RUN uv pip install --system -r requirements.txt

# Pre-download NLTK resources to avoid runtime latency
RUN python -c "import nltk; nltk.download('stopwords')"

# Copy the rest of the application code
COPY . .

# Expose the default Streamlit port
EXPOSE 8501

# Command to run the application
# We use --server.address=0.0.0.0 to allow external access to the container
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
