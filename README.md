# AWS Hands-On Projects

A collection of hands-on AWS projects designed for students to build real-world skills through guided, step-by-step exercises in their own AWS accounts.

## Projects

### Messaging & Queuing

| Project | Services | Description |
|---------|----------|-------------|
| [Event-Driven Messaging with SNS & SQS](./sqs-sns-iam-messaging/README.md) | SNS, SQS, IAM | Build a fanout messaging system using pub/sub architecture |
| [Lambda Triggered by SQS with SNS Notification](./lambda-sqs-sns-trigger/README.md) | Lambda, SQS, SNS, IAM, CloudWatch | Build a serverless order-processing pipeline: SQS triggers Lambda, Lambda publishes results to SNS |

### Lambda Series (Beginner → Advanced)

Work through these four projects in order. Each builds on the previous.

| # | Project | Services | Description |
|---|---------|----------|-------------|
| 1 | [Lambda Basics](./lambda-basics/README.md) | Lambda, IAM, CloudWatch | Deploy your first Lambda, understand handlers, invoke via Console/CLI/Boto3, and read CloudWatch Logs |
| 2 | [Lambda with S3 Event Processing](./lambda-s3-event-processing/README.md) | Lambda, S3, IAM, CloudWatch | Trigger Lambda automatically on S3 uploads; process text/CSV files and write results to a destination bucket |
| 3 | [Lambda Layers](./lambda-layers/README.md) | Lambda, IAM, CloudWatch | Package third-party libraries (`requests`, `pandas`) as reusable Lambda Layers; attach multiple layers to one function |
| 4 | [Lambda Troubleshooting & Boto3 Automation](./lambda-troubleshooting-monitoring/README.md) | Lambda, S3, EC2, SQS, CloudWatch, Log Insights | Debug 8 failure scenarios, master Log Insights queries, configure DLQs, and automate EC2/S3/SQS with Boto3 |

### ECS & Fargate Series (Beginner → Advanced)

Work through these two projects in order. Project 1 covers fundamentals; Project 2 builds a production-grade deployment.

| # | Project | Services | Description |
|---|---------|----------|-------------|
| 1 | [ECS Fargate Basics](./ecs-fargate-basics/README.md) | ECS, Fargate, ECR Public, IAM, CloudWatch | Containerize a Flask app, push to ECR Public, run as a Fargate task — understand ECS fundamentals |
| 2 | [ECS Fargate Advanced](./ecs-fargate-advanced/README.md) | ECS, Fargate, ECR Public, ALB, VPC, IAM, CloudWatch, Auto Scaling | Production-grade deployment: VPC networking, Application Load Balancer, rolling deployments, Auto Scaling, Container Insights, Docker Compose |

---

## How This Repo Is Organized

Each project lives in its own directory and follows a consistent layout:

```
project-name/
├── README.md           # Architecture overview and what you'll build
├── Dockerfile          # (container projects) How to build the image
├── docker-compose.yml  # (advanced container projects) Local dev setup
├── steps/              # Numbered, sequential step files
│   ├── 01-*.md
│   ├── 02-*.md
│   └── ...
├── src/                # Application source code
├── troubleshooting.md  # Common errors and fixes
└── challenges.md       # Extra challenges to deepen understanding
```

## Prerequisites (All Projects)

- An active AWS account with console access
- A user or role with sufficient permissions (each project specifies exactly what's needed)
- Basic familiarity with the AWS Management Console

## Contributing a New Project

1. Create a new directory using kebab-case naming (e.g., `s3-static-website`)
2. Follow the directory structure above
3. Add an entry to the table in this README
4. Keep steps atomic — one concept per file
