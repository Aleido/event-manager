FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install netcat for the entrypoint script's database wait logic
RUN apt-get update && apt-get install -y netcat-traditional && rm -rf /var/lib/apt/lists/*

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# {{ edit_1 }}
# Copy your application code AFTER dependencies are installed
COPY . /app/
# {{ /edit_1 }}

# Set the entrypoint for the container
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

CMD ["gunicorn", "eventmanagement.wsgi:application", "--bind", "0.0.0.0:8000"]

EXPOSE 8000