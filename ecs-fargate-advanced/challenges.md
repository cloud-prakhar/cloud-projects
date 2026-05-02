# Challenges — ECS Fargate Advanced

Completed the project? These challenges extend the architecture into real production patterns.

---

## Challenge 1 — HTTPS with ACM Certificate

**Goal:** Add HTTPS to the ALB using a free AWS Certificate Manager certificate.

**Steps:**
1. In AWS Certificate Manager, request a public certificate for a domain you own (or use a wildcard `*.yourdomain.com`).
2. Validate via DNS (add a CNAME record to your domain's DNS).
3. Wait for the certificate to become **Issued**.
4. In EC2 → Load Balancers → `ecs-advanced-alb`, add a **HTTPS listener** on port 443 using the certificate.
5. Add a redirect rule: HTTP 80 → HTTPS 443.
6. Update `alb-sg` to allow inbound 443 from `0.0.0.0/0`.

**What you'll learn:** TLS termination at the ALB; how ACM certificates integrate with load balancers; zero-cost managed certificate renewal.

---

## Challenge 2 — Private Subnets with NAT Gateway

**Goal:** Move ECS tasks to private subnets so they are never directly reachable from the internet.

**Steps:**
1. Add 2 private subnets (e.g., `10.0.3.0/24` and `10.0.4.0/24`) to `ecs-advanced-vpc`.
2. Create a NAT Gateway in one public subnet with an Elastic IP.
3. Create a private route table with `0.0.0.0/0 → NAT Gateway`.
4. Associate the private subnets with the private route table.
5. Update the ECS Service to use the private subnets.
6. Set **Auto-assign public IP: DISABLED** on the service.

**What you'll learn:** Private subnet architecture; NAT Gateway for outbound internet access; defense in depth (tasks unreachable from internet).

**Cost note:** NAT Gateway costs ~$0.045/hour + data transfer. Delete promptly after the exercise.

---

## Challenge 3 — Blue/Green Deployment with CodeDeploy

**Goal:** Replace rolling deployments with blue/green to achieve zero-downtime deploys with a traffic shift.

**Steps:**
1. Create a second target group: `ecs-advanced-tg-green`.
2. Add a second listener on the ALB on port 8080 → forward to `ecs-advanced-tg-green`.
3. Create a CodeDeploy application and deployment group targeting the ECS service.
4. Update the ECS service to use `CODE_DEPLOY` deployment controller.
5. Trigger a deployment by pushing a new image and creating an `appspec.yaml`.

**What you'll learn:** Blue/green vs rolling deployments; traffic shifting strategies (canary, linear, all-at-once); automatic rollback on health check failures.

---

## Challenge 4 — Secrets Manager for App Configuration

**Goal:** Move the `APP_VERSION` environment variable from plaintext in the Task Definition to AWS Secrets Manager.

**Steps:**
1. Create a secret in Secrets Manager: `ecs-advanced/config` with value `{"APP_VERSION": "2.0.0"}`.
2. Add a policy to `ECSAdvancedTaskExecutionRole` allowing `secretsmanager:GetSecretValue` on the specific secret ARN.
3. Update the Task Definition to use `valueFrom` syntax instead of `value`:
   ```json
   {
     "name": "APP_VERSION",
     "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:ecs-advanced/config:APP_VERSION::"
   }
   ```
4. Register a new Task Definition revision and update the Service.

**What you'll learn:** How ECS retrieves secrets at task startup; the difference between environment variable injection via plaintext vs Secrets Manager; why the Execution Role (not the Task Role) handles secret retrieval.

---

## Challenge 5 — Multi-Container Task

**Goal:** Add a sidecar container (e.g., an nginx reverse proxy) to the same Task Definition.

**Steps:**
1. Create a simple nginx configuration that proxies requests to `localhost:5000`.
2. Build and push an nginx image with the custom config.
3. Add a second container definition to the Task Definition:
   - Image: your custom nginx
   - Port: 80 (exposed to ALB)
   - Depends on: `ecs-advanced-container` to be `HEALTHY`
4. Update the target group to use port 80.
5. Update `ecs-sg` to allow port 80 from `alb-sg`.

**What you'll learn:** Multi-container tasks in Fargate; container ordering with `dependsOn`; sidecar pattern (proxy, logging agent, secret injector).

---

## Challenge 6 — Scheduled Scaling

**Goal:** Add a scheduled scaling action that scales the service to 4 tasks every weekday at 8 AM and back to 1 task at 8 PM.

**Steps:**
1. Create two scheduled actions on the scalable target:
   ```bash
   aws application-autoscaling put-scheduled-action \
     --service-namespace ecs \
     --resource-id service/ECSAdvancedCluster/ecs-advanced-service \
     --scalable-dimension ecs:service:DesiredCount \
     --scheduled-action-name scale-up-morning \
     --schedule "cron(0 13 ? * MON-FRI *)" \
     --scalable-target-action MinCapacity=4,MaxCapacity=4 \
     --region us-east-1
   ```
   (8 AM EST = 13:00 UTC)
2. Create the scale-down action for 8 PM EST (00:00 UTC next day).

**What you'll learn:** Scheduled scaling for predictable traffic patterns; cron expression syntax in Application Auto Scaling; combining scheduled + dynamic scaling.

---

## Challenge 7 — Centralized Structured Logging

**Goal:** Update the Flask app to output structured JSON logs and write a CloudWatch Logs Insights query that parses them.

**Steps:**
1. Update `src/app.py` to log in JSON format using Python's `logging` module:
   ```python
   import logging, json
   logging.basicConfig(format='%(message)s', level=logging.INFO)

   @app.before_request
   def log_request():
       logging.info(json.dumps({
           "event": "request",
           "method": request.method,
           "path": request.path,
           "remote_addr": request.remote_addr,
       }))
   ```
2. Rebuild, push, update the Service.
3. Write a Logs Insights query that parses the JSON fields and counts requests per path.

**What you'll learn:** Structured logging best practice; Logs Insights JSON field parsing; how to build request analytics from container logs.
