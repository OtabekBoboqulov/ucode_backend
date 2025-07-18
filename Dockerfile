FROM python:3.11-slim

# Install system dependencies for WeasyPrint and psycopg2
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpangoft2-1.0-0 \
    libpango-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run migrations, collect static, and start Gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn ucode.wsgi:application --bind 0.0.0.0:$PORT"]