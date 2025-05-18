# Use Alpine-based Python image for reduced vulnerabilities
FROM python:3.12-alpine

# Set the working directory in the container
WORKDIR /app

# Install build dependencies needed for some Python packages
RUN apk add --no-cache --virtual .build-deps gcc musl-dev python3-dev

# Copy the current directory contents into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Uninstall pip-audit if it gets installed as a transitive dependency
RUN pip uninstall -y pip-audit

# Remove build dependencies to reduce image size
RUN apk del .build-deps

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application
CMD sh -c "gunicorn app:app --bind 0.0.0.0:\${PORT:-8000}"
