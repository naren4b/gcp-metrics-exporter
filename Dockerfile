FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Expose port for Flask/Gunicorn
EXPOSE 8000

# Set environment variables for Flask
ENV PYTHONUNBUFFERED=1

# Run the app with Gunicorn for production
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "src.app:app"]