# Step 3 — ECR Public: Create the Container Repository

You will create an ECR Public repository to store the production Docker image for this project.

> **Reminder:** ECR Public repositories must be created in **us-east-1**.

---

## 3.1 What You're Creating

```
Repository type:  Public
Repository name:  ecs-advanced-app
Full URI:         public.ecr.aws/YOUR_ALIAS/ecs-advanced-app
```

---

## 3.2 Console — Create the Repository

1. Open the AWS Console → search **Elastic Container Registry**.
2. In the left sidebar, select **Public registries** (make sure it's not Private).
3. Click **Create repository**.
4. Fill in the form:

   | Field | Value |
   |-------|-------|
   | Repository name | `ecs-advanced-app` |
   | Short description | `Production Flask app for ECS Fargate Advanced project` |
   | Content types | Check **Operating systems: Linux** and **Architecture: x86-64** |
   | About (optional) | Leave blank |

5. Click **Create repository**.
6. After creation, copy the **Repository URI** (e.g., `public.ecr.aws/a1b2c3d4/ecs-advanced-app`).

---

## 3.3 CLI

```bash
# Create the ECR Public repository
aws ecr-public create-repository \
  --repository-name ecs-advanced-app \
  --catalog-data 'description="Production Flask app for ECS Fargate Advanced",operatingSystems=["Linux"],architectures=["x86-64"]' \
  --region us-east-1

# Retrieve the repository URI
REPO_URI=$(aws ecr-public describe-repositories \
  --repository-names ecs-advanced-app \
  --region us-east-1 \
  --query 'repositories[0].repositoryUri' \
  --output text)
echo "REPO_URI=$REPO_URI"
```

---

## 3.4 Authenticate Docker with ECR Public

```bash
# Authenticate Docker with the ECR Public registry
aws ecr-public get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin public.ecr.aws
```

Expected output: `Login Succeeded`

> This token is valid for 12 hours. Re-run if you get authentication errors later.

---

## Checkpoint

- [ ] Repository `ecs-advanced-app` exists in ECR Public
- [ ] Repository URI is copied (format: `public.ecr.aws/ALIAS/ecs-advanced-app`)
- [ ] Docker is authenticated with `public.ecr.aws`

---

**Next:** [Step 4 — Build and Push the Docker Image](./04-docker-build-push.md)
