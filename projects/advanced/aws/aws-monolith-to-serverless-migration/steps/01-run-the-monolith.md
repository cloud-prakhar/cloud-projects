# Step 1 — Run the Monolith on EC2 (the "before")

Before you migrate anything, you need the thing you're migrating *from*. In this step you run
the bookstore monolith on a single EC2 instance, exactly the way a small team often starts:
one Flask app, one SQLite file, one box. Then you'll name — out loud — the limits that make
serverless attractive. **You can't appreciate the destination until you've felt the start.**

---

## 1.1 What You're Creating

| Thing | Value |
|-------|-------|
| Instance name | `bookstore-monolith` |
| AMI | Amazon Linux 2023 |
| Type | `t3.micro` (free-tier eligible) |
| Inbound | TCP 5000 from your IP (app), 22 from your IP *or* use SSM |
| App | `src/monolith/app.py` (Flask + SQLite) |

> **Why one box on purpose?** The monolith isn't a strawman — it's a perfectly reasonable
> v1. The lesson is *when* its shape stops serving you, not that it was wrong to start here.

---

## 1.2 Console — Launch the Instance

1. **EC2 → Instances → Launch instances.**
2. **Name:** `bookstore-monolith`.
3. **AMI:** Amazon Linux 2023. **Type:** `t3.micro`.
4. **Key pair:** pick one you own (or choose **Proceed without a key pair** if you'll use SSM).
5. **Network settings → Edit → Security group**, add inbound rules:
   | Type | Port | Source |
   |------|------|--------|
   | Custom TCP | 5000 | My IP |
   | SSH | 22 | My IP (skip if using SSM) |
6. **Advanced details → IAM instance profile:** attach a role named `BookstoreMonolithRole`
   with `AmazonSSMManagedInstanceCore` if you want Session Manager access (no SSH key needed).
   Create it first in **IAM → Roles → Create role → AWS service → EC2**. Step 2 and Step 7
   add two small inline policies to this same role, so the box can write the migrated data
   and its final snapshot.
7. **Launch instance.** Note the **Public IPv4** once it's running.

### CLI alternative

```bash
MYIP=$(curl -s https://checkip.amazonaws.com)
VPC=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query "Vpcs[0].VpcId" --output text)
SUBNET=$(aws ec2 describe-subnets --filters Name=vpc-id,Values=$VPC Name=availability-zone,Values=us-east-1a \
  --query "Subnets[0].SubnetId" --output text)
AMI=$(aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --query Parameter.Value --output text)

# Instance role for Session Manager (no SSH key, no port 22)
cat > ec2-trust.json <<'JSON'
{ "Version": "2012-10-17",
  "Statement": [{ "Effect": "Allow",
    "Principal": {"Service": "ec2.amazonaws.com"},
    "Action": "sts:AssumeRole" }] }
JSON
aws iam create-role --role-name BookstoreMonolithRole --assume-role-policy-document file://ec2-trust.json
aws iam attach-role-policy --role-name BookstoreMonolithRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
aws iam create-instance-profile --instance-profile-name BookstoreMonolithRole
aws iam add-role-to-instance-profile --instance-profile-name BookstoreMonolithRole \
  --role-name BookstoreMonolithRole

SG=$(aws ec2 create-security-group --group-name bookstore-monolith-sg \
  --description "bookstore monolith" --vpc-id $VPC --query GroupId --output text)
aws ec2 authorize-security-group-ingress --group-id $SG --protocol tcp --port 5000 --cidr $MYIP/32

sleep 10   # a brand-new instance profile takes a few seconds to become usable
IID=$(aws ec2 run-instances --image-id $AMI --instance-type t3.micro --subnet-id $SUBNET \
  --security-group-ids $SG --iam-instance-profile Name=BookstoreMonolithRole \
  --associate-public-ip-address \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=bookstore-monolith}]' \
  --query "Instances[0].InstanceId" --output text)
aws ec2 wait instance-running --instance-ids $IID
IP=$(aws ec2 describe-instances --instance-ids $IID \
  --query "Reservations[0].Instances[0].PublicIpAddress" --output text)
echo "IID=$IID  SG=$SG  IP=$IP"   # keep these: Steps 6–8 use them
```

> Session Manager needs a minute or two after launch before **Connect** works (the SSM agent
> has to register).

> **If the launch fails with "instance type not supported in your requested Availability
> Zone":** some AZs don't offer `t3.micro` — `us-east-1e` is the usual culprit. This bites
> mainly on the CLI, where picking the "first" subnet can land you in that AZ. Either let AWS
> choose (omit the subnet) or pick a different one:
>
> ```bash
> SUBNET=$(aws ec2 describe-subnets \
>   --filters Name=vpc-id,Values=<your-vpc> Name=availability-zone,Values=us-east-1a \
>   --query "Subnets[0].SubnetId" --output text)
> ```
>
> `t3.micro` is fine in `us-east-1a/b/c/d/f`.

---

## 1.3 Install and Run the App

Connect (`ssh ec2-user@<public-ip>` or **EC2 → Connect → Session Manager**), then:

```bash
sudo dnf install -y python3-pip git sqlite
python3 -m pip install --user flask==3.1.0

mkdir -p ~/bookstore && cd ~/bookstore
# paste src/monolith/app.py here (scp it, or copy-paste into: nano app.py)

nohup python3 app.py > app.log 2>&1 &
sleep 2 && curl -s localhost:5000/health
# {"status":"ok","version":"monolith-1.0"}
```

> **Why `nohup … &`?** If you run `python3 app.py` in the foreground, the app dies when you
> close the Session Manager tab, and Steps 2–7 need it alive. **Why `sqlite`?** Amazon Linux
> 2023 ships the SQLite *library* but not the `sqlite3` command, and Step 7's reconciliation
> uses that command.

> **If you use Session Manager:** you're logged in as `ssm-user`, not `ec2-user`, so `~` is
> `/home/ssm-user`. That's fine. Just run every step from the same `~/bookstore` folder.

From your laptop, hit it:

```bash
IP=<public-ip>
curl http://$IP:5000/health
curl http://$IP:5000/books
# grab a book id from the output, then:
curl -X POST http://$IP:5000/orders \
  -H 'content-type: application/json' \
  -d '{"book_id":"<paste-id>","qty":2}'
```

You should see the seeded books and a `201` with an order id.

---

## 1.4 Feel the Limits (write these down)

While it's running, reason about each of these — they are the migration's *why*:

| You ask… | Monolith answer | Serverless answer (later) |
|----------|-----------------|----------------------------|
| Orders traffic 10×, catalog flat — scale just orders? | No — scale the whole box | Yes — `bookstore-orders` scales alone |
| Idle overnight — what does it cost? | Full instance-hour, every hour | ~$0 (pay per request) |
| Ship a catalog bug — what breaks? | The whole store (orders too) | Only `bookstore-catalog` |
| Box dies — where's the order data? | In one SQLite file on one disk | In DynamoDB, replicated across AZs |
| Patch the OS — who does it? | You, on a schedule | Nobody — no servers |

> Keep the instance running for now — Step 2 reads its SQLite data to migrate it.

---

## Checkpoint

- [ ] `bookstore-monolith` EC2 instance is **running**
- [ ] `curl http://<ip>:5000/books` returns the three seeded books
- [ ] `POST /orders` returns `201` with an order id
- [ ] You can name at least 3 concrete limits of the monolith shape

---

**Next:** [Step 2 — DynamoDB Tables + Data Migration](./02-dynamodb-tables.md)
