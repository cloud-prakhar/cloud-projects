# Step 7 — ALB: Application Load Balancer and Target Group

An **Application Load Balancer (ALB)** distributes incoming HTTP traffic across all running ECS tasks. You get a single DNS name for your application regardless of how many tasks are running.

---

## 7.1 What You're Creating

```
Security Group: alb-sg
  └── Inbound: port 80 from 0.0.0.0/0

Security Group: ecs-sg
  └── Inbound: port 5000 from alb-sg only (not from the internet)

Target Group: ecs-advanced-tg
  └── Type: IP
  └── Port: 5000
  └── Health check: GET /health

Application Load Balancer: ecs-advanced-alb
  └── Internet-facing
  └── Listener: port 80 → forward to ecs-advanced-tg
  └── Subnets: ecs-advanced-public-a, ecs-advanced-public-b
```

**Why security group separation?**  
`alb-sg` allows anyone on the internet to reach the ALB. `ecs-sg` allows only the ALB (via its security group ID) to reach the containers. This means your containers are never directly reachable from the internet — all traffic flows through the ALB.

---

## 7.2 Console — Create Security Groups

### ALB Security Group

1. Open **EC2** → **Security Groups** → **Create security group**.

   | Field | Value |
   |-------|-------|
   | Name | `alb-sg` |
   | Description | `Allow HTTP from internet to ALB` |
   | VPC | `ecs-advanced-vpc` |

2. Add **Inbound rules**:

   | Type | Protocol | Port | Source | Description |
   |------|----------|------|--------|-------------|
   | HTTP | TCP | 80 | `0.0.0.0/0` | Allow HTTP from internet |

3. Click **Create security group**.

### ECS Tasks Security Group

1. Create another security group:

   | Field | Value |
   |-------|-------|
   | Name | `ecs-sg` |
   | Description | `Allow traffic from ALB to ECS tasks on port 5000` |
   | VPC | `ecs-advanced-vpc` |

2. Add **Inbound rules**:

   | Type | Protocol | Port | Source | Description |
   |------|----------|------|--------|-------------|
   | Custom TCP | TCP | 5000 | `alb-sg` (select the security group, not a CIDR) | Allow from ALB only |

   > When you set **Source** to a security group ID, only resources in that security group can send traffic. This is called a **security group reference** and is more robust than CIDR-based rules.

3. Click **Create security group**.

---

## 7.3 Console — Create the Target Group

1. Open **EC2** → **Target Groups** → **Create target group**.
2. Fill in:

   | Field | Value |
   |-------|-------|
   | Target type | **IP addresses** |
   | Target group name | `ecs-advanced-tg` |
   | Protocol | HTTP |
   | Port | 5000 |
   | IP address type | IPv4 |
   | VPC | `ecs-advanced-vpc` |
   | Protocol version | HTTP1 |

3. Under **Health checks**:

   | Field | Value |
   |-------|-------|
   | Health check protocol | HTTP |
   | Health check path | `/health` |
   | Healthy threshold | 2 |
   | Unhealthy threshold | 3 |
   | Timeout | 5 seconds |
   | Interval | 30 seconds |
   | Success codes | `200` |

4. Click **Next** → **Create target group** (do not register any targets — ECS Service does this automatically).

   > **Why IP type?** Fargate tasks use `awsvpc` networking — each task gets a unique IP. ECS registers and deregisters task IPs in the target group automatically. If you chose "Instance" type, it wouldn't work with Fargate.

---

## 7.4 Console — Create the Application Load Balancer

1. Open **EC2** → **Load Balancers** → **Create load balancer**.
2. Choose **Application Load Balancer** → **Create**.

   | Field | Value |
   |-------|-------|
   | Name | `ecs-advanced-alb` |
   | Scheme | **Internet-facing** |
   | IP address type | IPv4 |

3. Under **Network mapping**:

   | Field | Value |
   |-------|-------|
   | VPC | `ecs-advanced-vpc` |
   | Mappings | Select **both** `ecs-advanced-public-a` and `ecs-advanced-public-b` |

4. Under **Security groups**:
   - Remove the default security group
   - Add `alb-sg`

5. Under **Listeners and routing**:

   | Field | Value |
   |-------|-------|
   | Protocol | HTTP |
   | Port | 80 |
   | Default action | Forward to `ecs-advanced-tg` |

6. Click **Create load balancer**.
7. Wait 2–3 minutes for the ALB to become **Active**.
8. **Copy the ALB DNS name** (e.g., `ecs-advanced-alb-1234567890.us-east-1.elb.amazonaws.com`).

---

## 7.5 CLI — Create Everything

```bash
# ---- Security Groups ----

# 1. ALB security group
ALB_SG=$(aws ec2 create-security-group \
  --group-name alb-sg \
  --description "Allow HTTP from internet to ALB" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text \
  --region us-east-1)
echo "ALB_SG=$ALB_SG"

aws ec2 authorize-security-group-ingress \
  --group-id $ALB_SG \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0 \
  --region us-east-1

# 2. ECS tasks security group
ECS_SG=$(aws ec2 create-security-group \
  --group-name ecs-sg \
  --description "Allow traffic from ALB to ECS tasks on port 5000" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text \
  --region us-east-1)
echo "ECS_SG=$ECS_SG"

aws ec2 authorize-security-group-ingress \
  --group-id $ECS_SG \
  --protocol tcp \
  --port 5000 \
  --source-group $ALB_SG \
  --region us-east-1

# ---- Target Group ----

TG_ARN=$(aws elbv2 create-target-group \
  --name ecs-advanced-tg \
  --protocol HTTP \
  --port 5000 \
  --target-type ip \
  --vpc-id $VPC_ID \
  --health-check-protocol HTTP \
  --health-check-path /health \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --health-check-timeout-seconds 5 \
  --health-check-interval-seconds 30 \
  --matcher HttpCode=200 \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text \
  --region us-east-1)
echo "TG_ARN=$TG_ARN"

# ---- Application Load Balancer ----

ALB_ARN=$(aws elbv2 create-load-balancer \
  --name ecs-advanced-alb \
  --subnets $SUBNET_A $SUBNET_B \
  --security-groups $ALB_SG \
  --scheme internet-facing \
  --type application \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text \
  --region us-east-1)
echo "ALB_ARN=$ALB_ARN"

# Create the HTTP listener
LISTENER_ARN=$(aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN \
  --query 'Listeners[0].ListenerArn' \
  --output text \
  --region us-east-1)
echo "LISTENER_ARN=$LISTENER_ARN"

# Wait for ALB to become active
aws elbv2 wait load-balancer-available \
  --load-balancer-arns $ALB_ARN \
  --region us-east-1

# Get the ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --load-balancer-arns $ALB_ARN \
  --query 'LoadBalancers[0].DNSName' \
  --output text \
  --region us-east-1)
echo "ALB DNS: http://$ALB_DNS"
```

---

## 7.6 Checkpoint

- [ ] Security group `alb-sg` allows inbound port 80 from `0.0.0.0/0`
- [ ] Security group `ecs-sg` allows inbound port 5000 from `alb-sg` only
- [ ] Target group `ecs-advanced-tg` is created with `/health` health check on port 5000
- [ ] ALB `ecs-advanced-alb` is **Active** in both subnets
- [ ] Listener on port 80 forwards to `ecs-advanced-tg`
- [ ] ALB DNS name is copied

---

**Next:** [Step 8 — Create the ECS Service](./08-ecs-service.md)
