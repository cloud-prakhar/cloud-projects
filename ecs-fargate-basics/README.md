# ECS Fargate Basics — Run Your First Container on AWS

## What You'll Build

You will containerize a simple Python Flask application, push the Docker image to **Amazon ECR Public**, and run it as a task on **Amazon ECS with Fargate**. By the end of this project you will understand:

- What ECS, Fargate, and ECR are and how they relate to each other
- How to write a `Dockerfile` for a Python web application
- How to push a Docker image to ECR Public from your local machine
- How to create an ECS Cluster, Task Definition, and run a standalone Task
- How to read container logs from CloudWatch Logs
- How to verify your running container by accessing it over the internet

This project uses the minimum number of AWS services to make the concepts clear before you add complexity.

---

## Architecture

```
  Your Machine
  ┌─────────────────────────────────────┐
  │  docker build  →  docker push       │
  │  (Python Flask app image)           │
  └──────────────────┬──────────────────┘
                     │ push image
                     ▼
  ┌─────────────────────────────────────┐
  │   Amazon ECR Public Registry        │
  │   public.ecr.aws/alias/ecs-basics   │
  └──────────────────┬──────────────────┘
                     │ pull image at runtime
                     ▼
  ┌─────────────────────────────────────┐
  │   Amazon ECS Cluster (Fargate)      │
  │                                     │
  │   ┌─────────────────────────────┐   │
  │   │  ECS Task                   │   │
  │   │  (Container: Flask app)     │   │
  │   │   port 5000 exposed         │   │
  │   └──────────────┬──────────────┘   │
  └──────────────────│──────────────────┘
                     │ writes logs
                     ▼
  ┌─────────────────────────────────────┐
  │   Amazon CloudWatch Logs            │
  │   /ecs/ecs-basics-task              │
  └─────────────────────────────────────┘
```

---

## Services Used

| Service | Role in this Project |
|---------|---------------------|
| **Amazon ECR Public** | Stores your Docker image. Public means no authentication needed to pull. |
| **Amazon ECS** | The container orchestration service. Manages where and how containers run. |
| **AWS Fargate** | The serverless compute engine for ECS. No EC2 instances to manage. |
| **Amazon CloudWatch Logs** | Captures all stdout/stderr from the container automatically. |
| **AWS IAM** | Execution role that gives ECS permission to pull images and write logs. |

---

## Key Concepts

| Concept | What it Means |
|---------|--------------|
| **Container** | A self-contained package: your code + runtime + dependencies. Runs identically everywhere. |
| **Docker Image** | A blueprint for a container. Built from a `Dockerfile`. Immutable once built. |
| **ECR** | Elastic Container Registry. AWS's managed Docker image store. |
| **ECS Cluster** | A logical grouping of capacity where your tasks run. |
| **Task Definition** | A JSON template describing your container: image, CPU, memory, ports, env vars, logging. |
| **Task** | A running instance of a Task Definition. Think: one running container. |
| **Fargate** | A launch type where AWS manages the underlying servers. You only define the container. |
| **Task Execution Role** | IAM role used by ECS to pull the image from ECR and write logs to CloudWatch. |

---

## Project Structure

```
ecs-fargate-basics/
├── README.md                          ← You are here
├── Dockerfile                         ← How to build the container image
├── src/
│   ├── app.py                         ← Flask application (the code that runs in the container)
│   └── requirements.txt               ← Python dependencies
├── steps/
│   ├── 01-iam-setup.md                ← Create the ECS Task Execution Role
│   ├── 02-ecr-public-repo.md          ← Create an ECR Public repository
│   ├── 03-docker-build-push.md        ← Build the image and push to ECR
│   ├── 04-ecs-cluster.md              ← Create an ECS Cluster
│   ├── 05-task-definition.md          ← Define the container task
│   ├── 06-run-task.md                 ← Launch the task and access the app
│   └── 07-cleanup.md                  ← Delete all resources
├── costs.md                           ← Service-by-service cost breakdown
├── troubleshooting.md
└── challenges.md
```

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| AWS account | Console access; permissions for ECS, ECR, IAM, CloudWatch |
| AWS CLI | `aws --version` → 2.x |
| Docker | `docker --version` installed and Docker daemon running |
| Region | All steps use **us-east-1** — adjust if needed |

> **Tip:** ECR Public repositories are created in `us-east-1` only, but your ECS cluster can be in any region.

---

## What You'll Learn Step by Step

| Step | File | Goal |
|------|------|------|
| 1 | `01-iam-setup.md` | Create the ECS Task Execution Role (IAM) |
| 2 | `02-ecr-public-repo.md` | Create a public ECR repository to store your image |
| 3 | `03-docker-build-push.md` | Build the Docker image locally and push it to ECR |
| 4 | `04-ecs-cluster.md` | Create an ECS Cluster with the Fargate launch type |
| 5 | `05-task-definition.md` | Register a Task Definition describing the container |
| 6 | `06-run-task.md` | Run the task and verify the app is accessible |
| 7 | `07-cleanup.md` | Delete all resources to avoid charges |

Start with **Step 1 →** [`steps/01-iam-setup.md`](steps/01-iam-setup.md)

---

## Estimated Time

60 – 90 minutes for a first-time learner.

## Estimated Cost

| Service | Configuration | Cost per Hour | Notes |
|---------|--------------|---------------|-------|
| **AWS Fargate** | 1 task · 0.25 vCPU · 0.5 GB | **~$0.012/hr** | Only charge while task is RUNNING |
| **Amazon ECR Public** | Image push + pull | **Free** | Public repos always free |
| **Amazon CloudWatch Logs** | Container stdout | **Free** | Well within 5 GB/month free tier |
| **ECS, IAM, VPC** | Control plane | **Free** | No charge for these services |

**Typical session cost: $0.02 – $0.05** (1–4 hours)

> ⚠️ Standalone tasks keep running until you manually stop them. Always complete [Step 7 — Cleanup](steps/07-cleanup.md). If left running for a week, cost would reach ~$2.

For a full service-by-service breakdown, pricing formulas, free tier details, and "left running" scenarios → see **[costs.md](costs.md)**.

---

## What's Next

After completing this project, continue to:
- [ECS Fargate Advanced](../ecs-fargate-advanced/README.md) — Add an Application Load Balancer, Auto Scaling, VPC networking, and production-grade monitoring
