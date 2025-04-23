# Start with a small, secure base image
FROM python:3.12.10-slim-bookworm

# Set working directory
WORKDIR /app

# Copy discovery server source and requirements
COPY ./discovery_server /app/discovery_server
COPY ./requirements.txt /app/requirements.txt

# Install only what’s in requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Expose the port FastAPI runs on
EXPOSE 8000

# Run the server as a module from its package
CMD ["uvicorn", "discovery_server.main:app", "--host", "0.0.0.0", "--port", "8000"]
