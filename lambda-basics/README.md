# Lambda Basics — Your First Serverless Function

## What You'll Build

You will create, configure, test, and invoke your very first **AWS Lambda function** — entirely from the AWS Console and CLI. By the end of this project you will understand:

- What a Lambda function is and how it gets invoked
- The anatomy of the Python handler: `event`, `context`, and the return value
- How to attach an IAM execution role
- How to pass configuration through **environment variables**
- How to read **CloudWatch Logs** after an invocation
- How to invoke a Lambda synchronously from the command line

This is the foundation for every subsequent Lambda project in this repo.

---

## Architecture

```
                ┌──────────────────────────────┐
                │   You (Console / CLI / SDK)  │
                └─────────────┬────────────────┘
                              │  Invoke (sync)
                              ▼
                ┌─────────────────────────────┐
                │      Lambda Function         │
                │      "HelloWorldLambda"      │
                │       Runtime: Python 3.14   │
                └────────────┬────────────────┘
                             │  Writes logs
                             ▼
                ┌─────────────────────────────┐
                │      CloudWatch Logs         │
                │  /aws/lambda/HelloWorldLambda│
                └─────────────────────────────┘
```

---

## Key Concepts

| Concept | What it means |
|---------|--------------|
| **Handler** | The Python function AWS calls — always `def handler(event, context)` |
| **Event** | A dict containing the trigger's input data; shape varies by trigger source |
| **Context** | A runtime object: function name, request ID, memory limit, timeout remaining |
| **Execution Role** | The IAM role Lambda assumes; controls what AWS services the function can call |
| **Cold Start** | First invocation after deploy/idle — container initialisation adds latency |
| **Warm Start** | Subsequent invocations reuse the running container — much faster |
| **CloudWatch Logs** | Every `print()` and `logging.*` call in your handler is captured here automatically |

---

## Project Structure

```
lambda-basics/
├── README.md                   ← You are here
├── steps/
│   ├── 01-iam-role.md          ← Create the Lambda execution role
│   ├── 02-create-function.md   ← Deploy the Hello World function
│   ├── 03-test-invoke.md       ← Invoke and read logs
│   ├── 04-environment-variables.md ← Add config via env vars
│   └── 05-cleanup.md           ← Delete everything
├── src/
│   ├── hello_world.py          ← Handler code (Step 2)
│   ├── with_env_vars.py        ← Handler with env vars (Step 4)
│   └── test_invoke.py          ← Boto3 invocation script (Step 3)
├── troubleshooting.md
└── challenges.md
```

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| AWS account | Console access with permissions to create Lambda, IAM roles, and view CloudWatch Logs |
| AWS CLI | `aws --version` should return 2.x |
| Python | 3.9+ locally (for running the test script) |
| Boto3 | `pip install boto3` |
| Region | All steps use **us-east-1** — adjust if needed |

---

## What You'll Learn Step by Step

| Step | File | Goal |
|------|------|------|
| 1 | `01-iam-role.md` | Create a least-privilege execution role |
| 2 | `02-create-function.md` | Package and deploy your first Lambda |
| 3 | `03-test-invoke.md` | Invoke it and inspect CloudWatch Logs |
| 4 | `04-environment-variables.md` | Configure the function without touching code |
| 5 | `05-cleanup.md` | Remove all resources to avoid charges |

Start with **Step 1 →** [`steps/01-iam-role.md`](steps/01-iam-role.md)

---

## Estimated Time

45 – 60 minutes for a first-time learner.

## Estimated Cost

Free Tier covers this project entirely:
- Lambda: first 1 million requests/month free
- CloudWatch Logs: first 5 GB ingestion free

---

## What's Next

After completing this project, continue to:
- [Lambda with S3 Event Processing](../lambda-s3-event-processing/README.md) — trigger Lambda from S3 uploads
- [Lambda Layers](../lambda-layers/README.md) — share dependencies across functions
