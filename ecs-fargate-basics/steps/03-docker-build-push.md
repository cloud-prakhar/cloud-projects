# Step 3 — Docker: Build the Image and Push to ECR

You will build the Docker image from the `Dockerfile` in this project, test it locally, and then push it to the ECR Public repository you created in Step 2.

---

## 3.1 Understand the Dockerfile

Open `Dockerfile` in the project root:

```dockerfile
FROM python:3.12-slim          # Start from official Python slim image (~50 MB)

WORKDIR /app                   # All subsequent commands run from /app

COPY src/requirements.txt .    # Copy deps file first (Docker cache layer)
RUN pip install --no-cache-dir -r requirements.txt

COPY src/app.py .              # Copy application code

EXPOSE 5000                    # Document that the app listens on 5000

ENV ENVIRONMENT=production     # Default environment variable

CMD ["python", "app.py"]       # Start the Flask server when container runs
```

**Why copy `requirements.txt` before `app.py`?**
Docker caches each layer. If you copy `app.py` and `requirements.txt` together, every code change re-installs all dependencies. By copying `requirements.txt` first, pip only re-runs when the dependency list actually changes — much faster rebuilds.

---

## 3.2 Build the Image

From the project root directory (`ecs-fargate-basics/`):

```bash
# Navigate to the project root
cd /path/to/ecs-fargate-basics

# Build the image and tag it with your ECR repository URI
# Replace YOUR_ALIAS with your actual ECR Public alias
docker build -t public.ecr.aws/YOUR_ALIAS/ecs-basics-app:latest .

# Verify the image was built
docker images | grep ecs-basics-app
```

Expected output:
```
REPOSITORY                                    TAG       IMAGE ID       CREATED         SIZE
public.ecr.aws/a1b2c3d4/ecs-basics-app       latest    abc123def456   5 seconds ago   125MB
```

---

## 3.3 Test the Image Locally

Before pushing, always verify the container works on your machine:

```bash
# Run the container locally, mapping port 5000
docker run -d \
  --name ecs-basics-test \
  -p 5000:5000 \
  public.ecr.aws/YOUR_ALIAS/ecs-basics-app:latest

# Wait 2 seconds, then test the app
curl http://localhost:5000/

# Also test the health endpoint
curl http://localhost:5000/health
```

Expected response from `/`:
```json
{
  "container_id": "a8f3b1c2d4e5",
  "environment": "production",
  "message": "Hello from ECS Fargate!",
  "version": "1.0.0"
}
```

Expected response from `/health`:
```json
{"status": "healthy"}
```

```bash
# View the container logs
docker logs ecs-basics-test

# Stop and remove the test container
docker stop ecs-basics-test
docker rm ecs-basics-test
```

---

## 3.4 Push the Image to ECR Public

```bash
# Push the image to ECR Public
docker push public.ecr.aws/YOUR_ALIAS/ecs-basics-app:latest
```

You will see Docker uploading each layer. The first push takes longer; subsequent pushes only upload changed layers.

Expected output:
```
The push refers to repository [public.ecr.aws/a1b2c3d4/ecs-basics-app]
a8b3c1d2e4f5: Pushed
...
latest: digest: sha256:abc123... size: 1234
```

---

## 3.5 Verify in the Console

1. In the AWS Console, open **ECR → Public registries**.
2. Click on `ecs-basics-app`.
3. You should see the `latest` tag with a recent **Pushed at** timestamp.

---

## Quick Reference: Common Docker Commands

| Command | What It Does |
|---------|-------------|
| `docker build -t NAME .` | Build image from `Dockerfile` in current directory |
| `docker images` | List all local images |
| `docker run -d -p 5000:5000 NAME` | Run container in background, map port |
| `docker ps` | List running containers |
| `docker logs CONTAINER` | View container stdout/stderr |
| `docker stop CONTAINER` | Stop a running container |
| `docker rm CONTAINER` | Delete a stopped container |
| `docker push IMAGE:TAG` | Push image to a registry |
| `docker pull IMAGE:TAG` | Pull image from a registry |

---

## Checkpoint

- [ ] Image builds without errors
- [ ] `curl http://localhost:5000/` returns the JSON response
- [ ] `docker push` succeeds
- [ ] Image appears in ECR Public console with `latest` tag

---

**Next:** [Step 4 — Create an ECS Cluster](./04-ecs-cluster.md)
