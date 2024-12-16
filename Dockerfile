FROM python:3.12-slim
LABEL authors="a.golepour"

# Set the working directory
WORKDIR /app

# Install build-essential package which includes make and other build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Generate protobuf files
RUN make generate-protos

# Expose the port the app runs on
EXPOSE 50051

# Command to run the application
CMD ["python", "main.py"]