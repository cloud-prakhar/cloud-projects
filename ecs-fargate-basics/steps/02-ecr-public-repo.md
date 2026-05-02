# Step 2 — ECR Public: Create a Container Image Repository

**Amazon ECR (Elastic Container Registry)** stores Docker images. You will use **ECR Public** which:
- Is always free to push and pull
- Requires no authentication to pull (publicly accessible)
- Is hosted at `public.ecr.aws`

> ECR Public repositories must be created in **us-east-1**, regardless of where your ECS cluster runs.

---

## 2.1 What You're Creating

```
Repository type:  Public
Repository name:  ecs-basics-app
Registry alias:   Assigned by AWS (e.g., a1b2c3d4)
Full URI:         public.ecr.aws/a1b2c3d4/ecs-basics-app
```

---

## 2.2 Console — Create the Repository

1. Open the AWS Console and search for **Elastic Container Registry**.
2. In the left sidebar, make sure you are on **Public registries** (not Private).
3. Click **Create repository**.
4. Fill in the form:

   | Field | Value |
   |-------|-------|
   | Repository name | `ecs-basics-app` |
   | Short description | `Hello World Flask app for ECS Fargate Basics` |
   | Content types | Check **Operating systems: Linux** and **Architecture: x86-64** |

5. Click **Create repository**.

> **Note:** AWS assigns you a **registry alias** (e.g., `a1b2c3d4`). Your repository URI will be `public.ecr.aws/YOUR_ALIAS/ecs-basics-app`. Copy this URI — you'll need it in Step 3.

---

## 2.3 Console — Find Your Repository URI

1. After creation, click on the repository name.
2. At the top you'll see **Repository URI** — copy it. It looks like:
   ```
   public.ecr.aws/a1b2c3d4/ecs-basics-app
   ```

---

## 2.4 AWS CLI (Alternative)

```bash
# Create the public repository (must be in us-east-1)
aws ecr-public create-repository \
  --repository-name ecs-basics-app \
  --catalog-data 'description="Hello World Flask app for ECS Fargate Basics",operatingSystems=["Linux"],architectures=["x86-64"]' \
  --region us-east-1

# The output includes repositoryUri — save it
# e.g.: public.ecr.aws/a1b2c3d4/ecs-basics-app
```

To retrieve it later:
```bash
aws ecr-public describe-repositories \
  --repository-names ecs-basics-app \
  --region us-east-1 \
  --query 'repositories[0].repositoryUri' \
  --output text
```

---

## 2.5 Authenticate Docker with ECR Public

Before you can push images, Docker needs to authenticate with ECR Public. Run this once:

```bash
# Authenticate Docker with ECR Public (always us-east-1)
aws ecr-public get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin public.ecr.aws
```

Expected output:
```
Login Succeeded
```

> This token is valid for 12 hours. If you get an authentication error later, re-run this command.

---

## Checkpoint

- [ ] ECR Public repository `ecs-basics-app` is created
- [ ] You have the full Repository URI copied (`public.ecr.aws/YOUR_ALIAS/ecs-basics-app`)
- [ ] `docker login` succeeded for `public.ecr.aws`

---

**Next:** [Step 3 — Build the Docker Image and Push to ECR](./03-docker-build-push.md)
