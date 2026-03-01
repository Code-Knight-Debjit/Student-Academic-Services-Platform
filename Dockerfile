# Use official Python image
FROM python:3.12-slim

# Prevent Python from writing pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies (optional but recommended)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Collect static files (optional but common)
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run using Gunicorn (recommended for production)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "student_results.wsgi:application"]