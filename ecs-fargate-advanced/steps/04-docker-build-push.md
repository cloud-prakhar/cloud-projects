# Step 4 — Docker: Build, Test Locally, and Push to ECR

This step covers building a production-ready Docker image, testing it locally with Docker Compose, and pushing it to ECR Public.

---

## 4.1 The Dockerfile — Production Best Practices

Open `Dockerfile` in the project root:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Copy deps first — Docker cache: only reinstalls when requirements.txt changes
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/app.py .

EXPOSE 5000

# Non-root user — security best practice
RUN adduser --disabled-password --gecos "" appuser
USER appuser

ENV ENVIRONMENT=production
ENV APP_VERSION=2.0.0
ENV SERVICE_NAME=ecs-advanced-app

CMD ["python", "app.py"]
```

### Key differences from Project 1

| Feature | Basics | Advanced |
|---------|--------|---------|
| Non-root user | No | Yes (`appuser`) |
| Default env vars | 1 | 3 |
| Health check endpoint | Yes | Yes |
| `/info` endpoint | No | Yes |
| Docker Compose support | No | Yes |

**Why non-root user?**  
Running containers as root means any container escape vulnerability gives an attacker root on the host. Running as an unprivileged user limits the blast radius.

---

## 4.2 Build the Image

From the `ecs-fargate-advanced/` project root:

```bash
# Replace YOUR_ALIAS with your ECR Public alias
REPO_URI="public.ecr.aws/YOUR_ALIAS/ecs-advanced-app"

# Build the image
docker build -t ${REPO_URI}:latest -t ${REPO_URI}:v2.0.0 .

# Confirm both tags exist locally
docker images | grep ecs-advanced-app
```

> Tagging with both `latest` and a version tag (`v2.0.0`) is a best practice — `latest` for convenience, the version tag for rollback capability.

---

## 4.3 Test Locally with Docker (Single Container)

```bash
# Run the container
docker run -d \
  --name ecs-advanced-test \
  -p 5000:5000 \
  -e ENVIRONMENT=local \
  -e APP_VERSION=2.0.0 \
  ${REPO_URI}:latest

# Test all three endpoints
curl http://localhost:5000/
curl http://localhost:5000/health
curl http://localhost:5000/info

# View logs
docker logs ecs-advanced-test

# Clean up
docker stop ecs-advanced-test && docker rm ecs-advanced-test
```

Expected response from `/`:
```json
{
  "container_id": "abc123def456",
  "environment": "local",
  "message": "ECS Fargate Advanced — Running",
  "region": "us-east-1",
  "service": "ecs-advanced-app",
  "version": "2.0.0"
}
```

---

## 4.4 Test Locally with Docker Compose

Docker Compose lets you define the full container configuration in a file (`docker-compose.yml`) rather than a long `docker run` command. This mirrors how you'd run the app in a local development environment.

Open `docker-compose.yml` in the project root:

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: ecs-advanced-app:local
    container_name: ecs-advanced-app
    ports:
      - "5000:5000"
    environment:
      - ENVIRONMENT=local
      - APP_VERSION=2.0.0
      - SERVICE_NAME=ecs-advanced-app
      - AWS_DEFAULT_REGION=us-east-1
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    restart: unless-stopped
```

### Docker Compose Commands

```bash
# Build the image defined in docker-compose.yml
docker compose build

# Start the service in the background (detached)
docker compose up -d

# Check status (shows health check state)
docker compose ps

# View live logs
docker compose logs -f

# Test the running service
curl http://localhost:5000/
curl http://localhost:5000/health
curl http://localhost:5000/info

# Restart the service (e.g., after a code change)
docker compose restart

# Stop and remove containers (keeps the image)
docker compose down

# Stop, remove containers AND delete the image
docker compose down --rmi all
```

### Docker Compose vs Docker Run

| docker run | docker compose |
|-----------|----------------|
| All config in a command-line flag | Config in a versioned YAML file |
| Hard to repeat exactly | Reproducible: same config every run |
| No built-in health checks | Health check built into the file |
| Manual restart after crash | `restart: unless-stopped` policy |
| One container per command | Can start multiple services at once |

---

## 4.5 Push the Image to ECR Public

```bash
# Push both tags
docker push ${REPO_URI}:latest
docker push ${REPO_URI}:v2.0.0
```

### Verify in the Console

1. Open **ECR** → **Public registries** → `ecs-advanced-app`.
2. You should see two tags: `latest` and `v2.0.0`.

### Verify via CLI

```bash
aws ecr-public describe-images \
  --repository-name ecs-advanced-app \
  --region us-east-1 \
  --query 'imageDetails[*].{Tags:imageTags, PushedAt:imagePushedAt}'
```

---

## 4.6 Quick Reference: All Docker Commands Used in This Project

| Command | What It Does |
|---------|-------------|
| `docker build -t NAME:TAG .` | Build image from Dockerfile in current directory |
| `docker build -t NAME:T1 -t NAME:T2 .` | Build and assign two tags at once |
| `docker run -d -p 5000:5000 NAME` | Run container detached, map host:container port |
| `docker run -e KEY=VALUE NAME` | Pass environment variable into container |
| `docker ps` | List running containers |
| `docker ps -a` | List all containers including stopped |
| `docker logs NAME` | View container output |
| `docker logs -f NAME` | Follow (tail) container output |
| `docker stop NAME` | Gracefully stop container (SIGTERM → SIGKILL) |
| `docker rm NAME` | Delete stopped container |
| `docker rmi IMAGE:TAG` | Delete a local image |
| `docker push IMAGE:TAG` | Push to registry |
| `docker inspect NAME` | View full container configuration |
| `docker exec -it NAME bash` | Open a shell inside a running container |
| `docker compose up -d` | Start all services defined in docker-compose.yml |
| `docker compose down` | Stop and remove all services |
| `docker compose logs -f` | Follow logs from all services |
| `docker compose ps` | Show service status |
| `docker compose build` | Build/rebuild images |
| `docker compose restart` | Restart all services |

---

## Checkpoint

- [ ] Image builds without errors
- [ ] `docker compose up -d` starts the service and `/health` returns 200
- [ ] Both `latest` and `v2.0.0` are pushed to ECR Public
- [ ] ECR Public console shows both tags

---

**Next:** [Step 5 — Create ECS Cluster with Container Insights](./05-ecs-cluster.md)
