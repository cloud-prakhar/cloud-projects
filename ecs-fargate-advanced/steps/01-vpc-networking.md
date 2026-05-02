# Step 1 — VPC: Build the Network Foundation

Before creating any ECS resources, you need a VPC with at least two public subnets in different Availability Zones. The Application Load Balancer (added in Step 7) requires subnets in a minimum of 2 AZs.

---

## 1.1 What You're Creating

```
VPC:               ecs-advanced-vpc  (10.0.0.0/16)
├── Public Subnet A:  ecs-advanced-public-a  (10.0.1.0/24)  — us-east-1a
├── Public Subnet B:  ecs-advanced-public-b  (10.0.2.0/24)  — us-east-1b
├── Internet Gateway: ecs-advanced-igw
└── Route Table:      ecs-advanced-rt  (0.0.0.0/0 → IGW)

Security Groups (created later in Steps 7–8):
├── alb-sg:  Allow inbound 80 from 0.0.0.0/0
└── ecs-sg:  Allow inbound 5000 from alb-sg only
```

**Why public subnets (not private)?**  
Private subnets require a NAT Gateway (~$32/month) for Fargate to pull images from ECR. For this learning project, public subnets with a security group that blocks direct access from the internet are the cost-effective choice. Production workloads should use private subnets.

---

## 1.2 Console — Create the VPC

1. Open the AWS Console → search **VPC** → open the VPC Dashboard.
2. Click **Create VPC**.
3. Select **VPC only** (not "VPC and more" — you'll create subnets manually for learning purposes).

   | Field | Value |
   |-------|-------|
   | Name tag | `ecs-advanced-vpc` |
   | IPv4 CIDR | `10.0.0.0/16` |
   | Tenancy | Default |

4. Click **Create VPC**.

---

## 1.3 Console — Create Subnet A (AZ a)

1. In the VPC Dashboard, click **Subnets** → **Create subnet**.

   | Field | Value |
   |-------|-------|
   | VPC | Select `ecs-advanced-vpc` |
   | Subnet name | `ecs-advanced-public-a` |
   | Availability Zone | `us-east-1a` |
   | IPv4 CIDR | `10.0.1.0/24` |

2. Click **Create subnet**.

---

## 1.4 Console — Create Subnet B (AZ b)

1. Click **Create subnet** again.

   | Field | Value |
   |-------|-------|
   | VPC | Select `ecs-advanced-vpc` |
   | Subnet name | `ecs-advanced-public-b` |
   | Availability Zone | `us-east-1b` |
   | IPv4 CIDR | `10.0.2.0/24` |

2. Click **Create subnet**.

---

## 1.5 Console — Enable Auto-assign Public IP on Both Subnets

For each subnet (`ecs-advanced-public-a` and `ecs-advanced-public-b`):

1. Select the subnet → **Actions** → **Edit subnet settings**.
2. Check **Enable auto-assign public IPv4 address**.
3. Click **Save**.

> This ensures Fargate tasks launched in these subnets automatically get a public IP.

---

## 1.6 Console — Create the Internet Gateway

1. Click **Internet gateways** → **Create internet gateway**.

   | Field | Value |
   |-------|-------|
   | Name tag | `ecs-advanced-igw` |

2. Click **Create internet gateway**.
3. Click **Actions** → **Attach to VPC** → select `ecs-advanced-vpc` → **Attach**.

---

## 1.7 Console — Create and Configure the Route Table

1. Click **Route tables** → **Create route table**.

   | Field | Value |
   |-------|-------|
   | Name | `ecs-advanced-rt` |
   | VPC | `ecs-advanced-vpc` |

2. Click **Create route table**.
3. Select `ecs-advanced-rt` → **Routes** tab → **Edit routes**.
4. Click **Add route**:

   | Destination | Target |
   |-------------|--------|
   | `0.0.0.0/0` | Select **Internet Gateway** → `ecs-advanced-igw` |

5. Click **Save changes**.
6. Click **Subnet associations** tab → **Edit subnet associations**.
7. Select both `ecs-advanced-public-a` and `ecs-advanced-public-b`.
8. Click **Save associations**.

---

## 1.8 AWS CLI (Alternative — Full VPC Setup)

```bash
# 1. Create VPC
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --query 'Vpc.VpcId' \
  --output text \
  --region us-east-1)
aws ec2 create-tags --resources $VPC_ID --tags Key=Name,Value=ecs-advanced-vpc --region us-east-1
echo "VPC_ID=$VPC_ID"

# 2. Create Subnet A
SUBNET_A=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --query 'Subnet.SubnetId' \
  --output text \
  --region us-east-1)
aws ec2 create-tags --resources $SUBNET_A --tags Key=Name,Value=ecs-advanced-public-a --region us-east-1
aws ec2 modify-subnet-attribute --subnet-id $SUBNET_A --map-public-ip-on-launch --region us-east-1

# 3. Create Subnet B
SUBNET_B=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone us-east-1b \
  --query 'Subnet.SubnetId' \
  --output text \
  --region us-east-1)
aws ec2 create-tags --resources $SUBNET_B --tags Key=Name,Value=ecs-advanced-public-b --region us-east-1
aws ec2 modify-subnet-attribute --subnet-id $SUBNET_B --map-public-ip-on-launch --region us-east-1

# 4. Create Internet Gateway and attach
IGW_ID=$(aws ec2 create-internet-gateway \
  --query 'InternetGateway.InternetGatewayId' \
  --output text \
  --region us-east-1)
aws ec2 create-tags --resources $IGW_ID --tags Key=Name,Value=ecs-advanced-igw --region us-east-1
aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID --region us-east-1

# 5. Create route table with default route
RT_ID=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --query 'RouteTable.RouteTableId' \
  --output text \
  --region us-east-1)
aws ec2 create-tags --resources $RT_ID --tags Key=Name,Value=ecs-advanced-rt --region us-east-1
aws ec2 create-route \
  --route-table-id $RT_ID \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID \
  --region us-east-1

# 6. Associate subnets with the route table
aws ec2 associate-route-table --route-table-id $RT_ID --subnet-id $SUBNET_A --region us-east-1
aws ec2 associate-route-table --route-table-id $RT_ID --subnet-id $SUBNET_B --region us-east-1

echo "VPC setup complete"
echo "VPC_ID=$VPC_ID | SUBNET_A=$SUBNET_A | SUBNET_B=$SUBNET_B | IGW_ID=$IGW_ID"
```

> **Save these IDs.** You will need `VPC_ID`, `SUBNET_A`, and `SUBNET_B` in multiple later steps.

---

## Checkpoint

- [ ] VPC `ecs-advanced-vpc` (10.0.0.0/16) is created
- [ ] Subnet `ecs-advanced-public-a` (10.0.1.0/24) in `us-east-1a`
- [ ] Subnet `ecs-advanced-public-b` (10.0.2.0/24) in `us-east-1b`
- [ ] Both subnets have "Auto-assign public IP" enabled
- [ ] Internet Gateway `ecs-advanced-igw` is attached to the VPC
- [ ] Route table `ecs-advanced-rt` has route `0.0.0.0/0 → ecs-advanced-igw`
- [ ] Both subnets are associated with `ecs-advanced-rt`

---

**Next:** [Step 2 — IAM Roles and Permissions](./02-iam-roles-permissions.md)
