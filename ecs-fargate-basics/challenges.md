# Challenges — ECS Fargate Basics

Completed the project? These challenges will deepen your understanding of ECS and Fargate.

---

## Challenge 1 — Add a Second Environment Variable

**Goal:** Pass an `APP_OWNER` environment variable to the container and return it in the `/` response.

**Steps:**
1. Update `src/app.py` to read `os.environ.get("APP_OWNER", "unknown")` and include it in the JSON response.
2. Rebuild the Docker image and push it to ECR with a new tag (e.g., `v1.1`).
3. Register a new Task Definition revision with the updated image URI and the new env var.
4. Run a new task with revision 2 and verify `APP_OWNER` appears in the response.

**What you'll learn:** Task Definition revisions and how environment variables flow from AWS to your container code.

---

## Challenge 2 — Run 3 Tasks Simultaneously

**Goal:** Run 3 tasks at the same time and observe that each returns a different `container_id`.

**Steps:**
1. Run 3 separate tasks (3 separate `aws ecs run-task` calls or Console launches).
2. Curl each Public IP and compare the `container_id` values.
3. Check CloudWatch Logs — you should see 3 separate log streams.

**What you'll learn:** Each Fargate task gets its own isolated container environment, its own IP, and its own log stream.

---

## Challenge 3 — Use a Private ECR Repository Instead of Public

**Goal:** Create a private ECR repository, push the same image, and update the Task Definition to pull from it.

**Steps:**
1. Create a private ECR repository in us-east-1.
2. Authenticate Docker: `aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com`
3. Tag and push the image to the private URI.
4. Update the Task Definition to use the private image URI.
5. Verify `AmazonECSTaskExecutionRolePolicy` already covers private ECR pulls (it does).

**What you'll learn:** The difference between public and private ECR; how the Execution Role enables private image pulls.

---

## Challenge 4 — Add a `/version` Endpoint

**Goal:** Add a new Flask route `/version` that returns the image tag from an environment variable.

**Steps:**
1. Add `APP_VERSION` env var to `app.py`.
2. Add a `/version` route returning `{"version": APP_VERSION}`.
3. Rebuild, push, and run. Access `/version` on the public IP.

**What you'll learn:** How to use environment variables in containerized applications for dynamic configuration.

---

## Challenge 5 — Simulate a Container Crash

**Goal:** Make the container crash intentionally and observe ECS behavior.

**Steps:**
1. Add an `/crash` endpoint to `app.py` that calls `sys.exit(1)`.
2. Rebuild and push; run a new task.
3. Call `/crash` with curl.
4. Observe the task status — it will go to STOPPED.
5. Check the `stoppedReason` and the CloudWatch Logs for exit information.

**What you'll learn:** What happens to a standalone task when the container exits. (Hint: standalone tasks are not restarted — that's what ECS Services are for, which you'll learn in the Advanced project.)

---

## Challenge 6 — Task with FARGATE_SPOT

**Goal:** Run the same task using the cheaper `FARGATE_SPOT` launch type.

**Steps:**
1. Update the cluster to add `FARGATE_SPOT` as a capacity provider.
2. Run the task using `FARGATE_SPOT` instead of `FARGATE`.
3. Observe — it should behave identically (for short-lived tasks, interruptions are rare).

**What you'll learn:** The cost difference between FARGATE and FARGATE_SPOT; when each is appropriate.
