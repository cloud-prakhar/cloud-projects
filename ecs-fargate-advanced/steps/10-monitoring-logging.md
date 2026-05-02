# Step 10 — Monitoring and Logging

This step shows you where to find metrics, how to read container logs, and how to write CloudWatch Logs Insights queries to analyze your application.

---

## 10.1 CloudWatch Container Insights — Metrics

Container Insights is enabled on the cluster (Step 5). It automatically publishes metrics to CloudWatch under the `ECS/ContainerInsights` namespace.

### Console — View Metrics

1. Open **CloudWatch** → **Container Insights**.
2. In the dropdown, select **ECS Services**.
3. Select `ECSAdvancedCluster` from the cluster dropdown.
4. You'll see a dashboard showing:
   - **CPU Utilization** per service
   - **Memory Utilization** per service
   - **Running Task Count**
   - **Network I/O**

### Key Metrics to Watch

| Metric | Namespace | What It Tells You |
|--------|-----------|------------------|
| `CpuUtilized` | `ECS/ContainerInsights` | CPU cores used per task (for scaling) |
| `CpuReserved` | `ECS/ContainerInsights` | CPU allocated per task |
| `MemoryUtilized` | `ECS/ContainerInsights` | Memory used per task |
| `MemoryReserved` | `ECS/ContainerInsights` | Memory allocated per task |
| `RunningTaskCount` | `ECS/ContainerInsights` | Number of running tasks in the service |
| `HealthyHostCount` | `AWS/ApplicationELB` | ALB: healthy targets in the target group |
| `RequestCount` | `AWS/ApplicationELB` | ALB: total requests per minute |
| `TargetResponseTime` | `AWS/ApplicationELB` | ALB: p95 response latency |

### CLI — Retrieve a Metric

```bash
# Get average CPU utilization over the last 5 minutes
aws cloudwatch get-metric-statistics \
  --namespace ECS/ContainerInsights \
  --metric-name CpuUtilized \
  --dimensions Name=ClusterName,Value=ECSAdvancedCluster Name=ServiceName,Value=ecs-advanced-service \
  --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics Average \
  --region us-east-1

# Check ALB healthy host count
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name HealthyHostCount \
  --dimensions Name=LoadBalancer,Value=$(aws elbv2 describe-load-balancers \
    --names ecs-advanced-alb \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text \
    --region us-east-1 | sed 's|arn:aws:elasticloadbalancing:[^:]*:[^:]*:loadbalancer/||') \
    Name=TargetGroup,Value=$(aws elbv2 describe-target-groups \
    --names ecs-advanced-tg \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text \
    --region us-east-1 | sed 's|arn:aws:elasticloadbalancing:[^:]*:[^:]*:||') \
  --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics Average \
  --region us-east-1
```

---

## 10.2 Container Logs — CloudWatch Logs

Every line printed to stdout by the Flask app is automatically sent to CloudWatch Logs.

### Log Group Structure

```
/ecs/ecs-advanced-task
└── ecs/ecs-advanced-container/TASK_ID_1
└── ecs/ecs-advanced-container/TASK_ID_2
```

Each running task gets its own log stream.

### Console — View Logs

1. Open **CloudWatch** → **Log groups** → `/ecs/ecs-advanced-task`.
2. Click a log stream to see the container output.
3. Use **Log Insights** for powerful queries across all streams.

### CLI — View Recent Logs

```bash
# List log streams (sorted by most recent)
aws logs describe-log-streams \
  --log-group-name /ecs/ecs-advanced-task \
  --order-by LastEventTime \
  --descending \
  --region us-east-1 \
  --query 'logStreams[*].{Stream:logStreamName, LastEvent:lastEventTimestamp}'

# Read the most recent stream
LATEST_STREAM=$(aws logs describe-log-streams \
  --log-group-name /ecs/ecs-advanced-task \
  --order-by LastEventTime \
  --descending \
  --query 'logStreams[0].logStreamName' \
  --output text \
  --region us-east-1)

aws logs get-log-events \
  --log-group-name /ecs/ecs-advanced-task \
  --log-stream-name $LATEST_STREAM \
  --limit 50 \
  --region us-east-1 \
  --query 'events[*].message' \
  --output text
```

---

## 10.3 CloudWatch Logs Insights Queries

Logs Insights lets you search and analyze logs across all tasks with SQL-like syntax.

**How to use:**
1. Open **CloudWatch** → **Logs Insights**.
2. Select log group `/ecs/ecs-advanced-task`.
3. Paste a query and click **Run query**.

### Query 1 — All log lines in the last 30 minutes

```
fields @timestamp, @message
| sort @timestamp desc
| limit 100
```

### Query 2 — Count requests per endpoint

```
fields @message
| filter @message like /GET /
| parse @message '"GET * HTTP' as path
| stats count(*) as requests by path
| sort requests desc
```

### Query 3 — Find all HTTP errors (4xx and 5xx)

```
fields @timestamp, @message
| filter @message like / 4/ or @message like / 5/
| filter @message like /HTTP/
| sort @timestamp desc
```

### Query 4 — Application startup events

```
fields @timestamp, @message
| filter @message like /Running on/
| sort @timestamp desc
```

### Query 5 — Count events per container (per task)

```
fields @logStream, @message
| stats count(*) as events by @logStream
| sort events desc
```

---

## 10.4 Create a Simple CloudWatch Dashboard

### Console

1. Open **CloudWatch** → **Dashboards** → **Create dashboard**.
2. Name it `ECSAdvancedDashboard`.
3. Add widgets:

   **Widget 1 — Running Tasks**
   - Type: Line
   - Metric: `ECS/ContainerInsights` → `RunningTaskCount` → service `ecs-advanced-service`

   **Widget 2 — CPU Utilization**
   - Type: Line
   - Metric: `ECS/ContainerInsights` → `CpuUtilized` → service `ecs-advanced-service`

   **Widget 3 — ALB Request Count**
   - Type: Bar
   - Metric: `AWS/ApplicationELB` → `RequestCount` → ALB `ecs-advanced-alb`

4. Click **Save dashboard**.

### CLI — Create Dashboard via JSON

```bash
aws cloudwatch put-dashboard \
  --dashboard-name ECSAdvancedDashboard \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "x": 0, "y": 0, "width": 12, "height": 6,
        "properties": {
          "title": "Running Task Count",
          "metrics": [
            ["ECS/ContainerInsights", "RunningTaskCount",
             "ClusterName", "ECSAdvancedCluster",
             "ServiceName", "ecs-advanced-service"]
          ],
          "period": 60,
          "stat": "Average",
          "view": "timeSeries"
        }
      },
      {
        "type": "metric",
        "x": 12, "y": 0, "width": 12, "height": 6,
        "properties": {
          "title": "CPU Utilization",
          "metrics": [
            ["ECS/ContainerInsights", "CpuUtilized",
             "ClusterName", "ECSAdvancedCluster",
             "ServiceName", "ecs-advanced-service"]
          ],
          "period": 60,
          "stat": "Average",
          "view": "timeSeries"
        }
      }
    ]
  }' \
  --region us-east-1
```

---

## 10.5 Check ALB Target Health

```bash
# Get target group ARN
TG_ARN=$(aws elbv2 describe-target-groups \
  --names ecs-advanced-tg \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text \
  --region us-east-1)

# Check health of all registered targets
aws elbv2 describe-target-health \
  --target-group-arn $TG_ARN \
  --region us-east-1 \
  --query 'TargetHealthDescriptions[*].{IP:Target.Id, Port:Target.Port, Health:TargetHealth.State, Reason:TargetHealth.Description}'
```

All targets should show `"Health": "healthy"`.

---

## Checkpoint

- [ ] CloudWatch Container Insights shows CPU/Memory metrics for the service
- [ ] Log group `/ecs/ecs-advanced-task` has 2 log streams (one per task)
- [ ] Logs Insights query returns results
- [ ] ALB target health shows all targets as `healthy`

---

**Next:** [Step 11 — Cleanup](./11-cleanup.md)
