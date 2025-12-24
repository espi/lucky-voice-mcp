# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY requirements.txt .
COPY lucky_voice_mcp.py .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Define environment variable for the cookie (user should pass this at runtime)
# ENV LUCKY_VOICE_COOKIE=""

# Run the MCP server
ENTRYPOINT ["fastmcp", "run", "lucky_voice_mcp.py"]
