FROM python:3.12-slim

# Install dependencies as a separate layer for Docker cache efficiency
WORKDIR /app

COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/app.py .

EXPOSE 5000

# Non-root user for security best practice
RUN adduser --disabled-password --gecos "" appuser
USER appuser

ENV ENVIRONMENT=production
ENV APP_VERSION=2.0.0
ENV SERVICE_NAME=ecs-advanced-app

CMD ["python", "app.py"]
