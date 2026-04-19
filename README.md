# AWS Hands-On Projects

A collection of hands-on AWS projects designed for students to build real-world skills through guided, step-by-step exercises in their own AWS accounts.

## Projects

| Project | Services | Description |
|---------|----------|-------------|
| [Event-Driven Messaging with SNS & SQS](./sqs-sns-iam-messaging/README.md) | SNS, SQS, IAM | Build a fanout messaging system using pub/sub architecture |
| [Lambda Triggered by SQS with SNS Notification](./lambda-sqs-sns-trigger/README.md) | Lambda, SQS, SNS, IAM, CloudWatch | Build a serverless order-processing pipeline: SQS triggers Lambda, Lambda publishes results to SNS |

---

## How This Repo Is Organized

Each project lives in its own directory and follows a consistent layout:

```
project-name/
├── README.md           # Architecture overview and what you'll build
├── steps/              # Numbered, sequential step files
│   ├── 01-*.md
│   ├── 02-*.md
│   └── ...
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
