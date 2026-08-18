FROM python:3.11-slim

# Install FFmpeg and required system tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 user

WORKDIR /app

# Install Python dependencies first
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . /app

# Make the app directory accessible
RUN chown -R user:user /app

USER user

ENV HOME=/home/user
ENV PATH=/home/user/.local/bin:$PATH

EXPOSE 7860

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "1", "--threads", "1", "app:app"]