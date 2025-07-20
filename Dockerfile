FROM python:3.11-slim

WORKDIR /app

# Copy application code
COPY src/ ./src/
RUN pip install --no-cache-dir -r src/requirements.txt

# Expose port for Flask/Gunicorn
EXPOSE 8000

# Set environment variables for Flask
ENV PYTHONUNBUFFERED=1

# Run the app with Gunicorn for production
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "src.app:app"]