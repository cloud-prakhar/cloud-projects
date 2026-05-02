# Step 9 — Auto Scaling: Scale Tasks Based on CPU

You will configure **ECS Service Auto Scaling** to automatically increase or decrease the number of running tasks based on CPU utilization. This uses **Application Auto Scaling** (a separate AWS service from EC2 Auto Scaling).

---

## 9.1 Scaling Policy Design

```
Metric:  CPUUtilization (from CloudWatch Container Insights)

Scale OUT:  CPU > 60% for 2 consecutive 1-minute periods → add 1 task
Scale IN:   CPU < 20% for 5 consecutive 1-minute periods → remove 1 task
Cooldown:   300 seconds (5 min) between scaling actions

Min tasks:  1
Max tasks:  4
Current:    2
```

**Why 60% scale-out?**  
Scaling out at 60% gives headroom before the new task is ready (30–60s startup). Waiting until 100% is too late — users experience degraded performance during task startup.

**Why 5-minute scale-in delay?**  
Traffic spikes are often brief. Removing a task too quickly might immediately trigger another scale-out. A longer cooldown avoids "flapping."

---

## 9.2 Console — Register the Scalable Target

1. Open **ECS** → **Clusters** → `ECSAdvancedCluster` → **Services** → `ecs-advanced-service`.
2. Click **Update service**.
3. Under **Service auto scaling**:

   | Field | Value |
   |-------|-------|
   | Turn on Service Auto Scaling | Yes |
   | Minimum number of tasks | `1` |
   | Desired number of tasks | `2` |
   | Maximum number of tasks | `4` |

4. Click **Add scaling policy** → choose **Target tracking**.

   | Field | Value |
   |-------|-------|
   | Policy name | `ecs-advanced-cpu-target-tracking` |
   | ECS service metric | **ECSServiceAverageCPUUtilization** |
   | Target value | `60` |
   | Scale-out cooldown | `300` |
   | Scale-in cooldown | `300` |

5. Click **Update**.

---

## 9.3 CLI — Register Scalable Target and Policies

### Register the Scalable Target

```bash
# Register the ECS service as an auto scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/ECSAdvancedCluster/ecs-advanced-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 4 \
  --region us-east-1
```

### Target Tracking Policy (Recommended)

Target tracking is the simplest policy — you define a target metric value and AWS **automatically creates and manages the CloudWatch alarms** for you. You do not need to create alarms manually.

```bash
# Create a target tracking policy on average CPU utilization
# AWS will auto-create two CloudWatch alarms: AlarmHigh and AlarmLow
aws application-autoscaling put-scaling-policy \
  --policy-name ecs-advanced-cpu-target-tracking \
  --service-namespace ecs \
  --resource-id service/ECSAdvancedCluster/ecs-advanced-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 60.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleOutCooldown": 300,
    "ScaleInCooldown": 300,
    "DisableScaleIn": false
  }' \
  --region us-east-1
```

After running this, verify the auto-created alarms:
```bash
aws cloudwatch describe-alarms \
  --alarm-name-prefix TargetTracking-service/ECSAdvancedCluster/ecs-advanced-service \
  --region us-east-1 \
  --query 'MetricAlarms[*].{Name:AlarmName, State:StateValue}'
```

You will see two alarms with state `INSUFFICIENT_DATA` — this is normal initially. They transition to `OK` once Container Insights starts emitting CPU metrics (within 5 minutes).

### Step Scaling Policies (Advanced — Optional)

Step scaling gives you more granular control. Use this if you want different scaling rates at different thresholds.

```bash
# Step scaling: Scale OUT when CPU > 60%
aws application-autoscaling put-scaling-policy \
  --policy-name ecs-advanced-scale-out \
  --service-namespace ecs \
  --resource-id service/ECSAdvancedCluster/ecs-advanced-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type StepScaling \
  --step-scaling-policy-configuration '{
    "AdjustmentType": "ChangeInCapacity",
    "Cooldown": 300,
    "MetricAggregationType": "Average",
    "StepAdjustments": [
      {
        "MetricIntervalLowerBound": 0,
        "MetricIntervalUpperBound": 20,
        "ScalingAdjustment": 1
      },
      {
        "MetricIntervalLowerBound": 20,
        "ScalingAdjustment": 2
      }
    ]
  }' \
  --region us-east-1

SCALE_OUT_POLICY_ARN=$(aws application-autoscaling describe-scaling-policies \
  --policy-names ecs-advanced-scale-out \
  --service-namespace ecs \
  --resource-id service/ECSAdvancedCluster/ecs-advanced-service \
  --scalable-dimension ecs:service:DesiredCount \
  --region us-east-1 \
  --query 'ScalingPolicies[0].PolicyARN' \
  --output text)

# CloudWatch alarm that triggers the scale-out policy
aws cloudwatch put-metric-alarm \
  --alarm-name ecs-advanced-cpu-high \
  --alarm-description "Scale out ECS service when CPU > 60%" \
  --namespace ECS/ContainerInsights \
  --metric-name CpuUtilized \
  --dimensions Name=ClusterName,Value=ECSAdvancedCluster Name=ServiceName,Value=ecs-advanced-service \
  --statistic Average \
  --period 60 \
  --evaluation-periods 2 \
  --threshold 60 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions $SCALE_OUT_POLICY_ARN \
  --region us-east-1

# Step scaling: Scale IN when CPU < 20%
aws application-autoscaling put-scaling-policy \
  --policy-name ecs-advanced-scale-in \
  --service-namespace ecs \
  --resource-id service/ECSAdvancedCluster/ecs-advanced-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type StepScaling \
  --step-scaling-policy-configuration '{
    "AdjustmentType": "ChangeInCapacity",
    "Cooldown": 300,
    "MetricAggregationType": "Average",
    "StepAdjustments": [
      {
        "MetricIntervalUpperBound": 0,
        "ScalingAdjustment": -1
      }
    ]
  }' \
  --region us-east-1

SCALE_IN_POLICY_ARN=$(aws application-autoscaling describe-scaling-policies \
  --policy-names ecs-advanced-scale-in \
  --service-namespace ecs \
  --resource-id service/ECSAdvancedCluster/ecs-advanced-service \
  --scalable-dimension ecs:service:DesiredCount \
  --region us-east-1 \
  --query 'ScalingPolicies[0].PolicyARN' \
  --output text)

aws cloudwatch put-metric-alarm \
  --alarm-name ecs-advanced-cpu-low \
  --alarm-description "Scale in ECS service when CPU < 20%" \
  --namespace ECS/ContainerInsights \
  --metric-name CpuUtilized \
  --dimensions Name=ClusterName,Value=ECSAdvancedCluster Name=ServiceName,Value=ecs-advanced-service \
  --statistic Average \
  --period 60 \
  --evaluation-periods 5 \
  --threshold 20 \
  --comparison-operator LessThanThreshold \
  --alarm-actions $SCALE_IN_POLICY_ARN \
  --region us-east-1
```

---

## 9.4 Verify Scaling Configuration

```bash
# View the scalable target
aws application-autoscaling describe-scalable-targets \
  --service-namespace ecs \
  --resource-ids service/ECSAdvancedCluster/ecs-advanced-service \
  --region us-east-1

# View scaling policies
aws application-autoscaling describe-scaling-policies \
  --service-namespace ecs \
  --resource-id service/ECSAdvancedCluster/ecs-advanced-service \
  --scalable-dimension ecs:service:DesiredCount \
  --region us-east-1 \
  --query 'ScalingPolicies[*].{Name:PolicyName, Type:PolicyType}'

# View CloudWatch alarms
aws cloudwatch describe-alarms \
  --alarm-name-prefix ecs-advanced \
  --region us-east-1 \
  --query 'MetricAlarms[*].{Name:AlarmName, State:StateValue, Threshold:Threshold}'
```

---

## 9.5 Scaling Policy Comparison

| Policy Type | How It Works | Best For |
|-------------|-------------|---------|
| **Target Tracking** | Set a target metric value; AWS manages alarms and steps automatically | Most use cases — simple and self-optimizing |
| **Step Scaling** | Define exact step adjustments per metric threshold band | When you need precise control over scaling increments |
| **Scheduled Scaling** | Scale to a fixed count at a set time | Predictable traffic patterns (e.g., scale up at 9am Mon–Fri) |

---

## Checkpoint

- [ ] Scalable target registered: min 1, max 4 tasks
- [ ] Target tracking or step scaling policies are active
- [ ] CloudWatch alarms exist for `ecs-advanced-cpu-high` and/or `ecs-advanced-cpu-low`
- [ ] Service still shows 2 running tasks (no scaling triggered yet)

---

**Next:** [Step 10 — Monitoring and Logging](./10-monitoring-logging.md)
