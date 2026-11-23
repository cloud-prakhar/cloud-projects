# Step 7 — Decommission the Monolith

The fig has taken over; the host tree can rot. In a real migration this is the **most
disciplined** step — retiring the old system too early loses data, too late wastes money and
keeps two systems alive. You verify nothing depends on the monolith, take a final data
snapshot, **stop** it (reversible) before you **terminate** it (not), and only then declare
the migration done.

---

## 7.1 Prove nothing still uses it

1. **Traffic:** In EC2 → the instance → **Monitoring**, confirm `NetworkIn` has flatlined
   since the cutover. If you used the security group rule for port 5000, check there are no
   recent connections.
2. **Front door:** Confirm `bookstore-api` has **no** route still pointing at the monolith
   (no `HTTP_PROXY` catch-all left over from Step 6).
3. **Data:** Confirm `Orders` in DynamoDB contains every order the monolith had (compare
   counts with the SQLite `orders` table). Re-run the Step 2 exporter once more — it's
   idempotent — to catch any orders placed on the monolith *after* your first export.

First re-run the exporter on the EC2 box, then check the result:

```bash
python3 migrate_data.py     # idempotent — safe to run again
```

**Don't compare raw counts.** It's tempting to run `COUNT(*)` on both sides and expect the same
number, but after cutover that comparison will *always* fail — and it's not a bug. DynamoDB now
holds two kinds of orders:

- orders that came from the monolith (these came across in the export), **plus**
- orders placed through the new API since cutover, which **never existed in SQLite at all**

So DynamoDB is legitimately *larger* than SQLite. What you actually need to prove is that
nothing was **lost**: every order id in SQLite must exist in DynamoDB. That's a subset check,
not an equality check.

```bash
# on the EC2 box — every monolith order id
sqlite3 bookstore.db "SELECT id FROM orders;" | sort > /tmp/sqlite_ids.txt

# every order id now in DynamoDB
aws dynamodb scan --table-name Orders --query "Items[].id.S" --output text \
  | tr '\t' '\n' | sort > /tmp/ddb_ids.txt

# anything listed here was LOST — the list must be empty
comm -23 /tmp/sqlite_ids.txt /tmp/ddb_ids.txt
```

An empty result means zero data loss and you're safe to retire the box. If ids *do* appear,
re-run the exporter and check its output for errors before going any further.

> **Why reconcile twice?** Between your first export (Step 2) and the `/orders*` cutover (Step 6, Vine 2), the
> monolith may have taken more orders. The final idempotent re-export guarantees **zero data
> loss** — the cardinal rule of any migration.

> **Why the counts drift, concretely.** In a real run of this lab: SQLite ended with 2 orders,
> DynamoDB with 5. The 3 extra were placed through the new API after cutover. Counts differed;
> the subset check passed. Both facts were correct.

---

## 7.2 Take a final snapshot (safety net)

Before you delete anything, keep a copy of the monolith's data in case you must roll back.
The instance role can't write S3 yet (you'd get `AccessDenied … s3:PutObject`), so first create
a bucket and grant **only** `PutObject` on one prefix. Do this from your laptop:

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BKT=bookstore-monolith-snapshot-${ACCOUNT_ID}
aws s3api create-bucket --bucket $BKT
cat > snapshot-policy.json <<JSON
{ "Version": "2012-10-17",
  "Statement": [{ "Effect": "Allow", "Action": "s3:PutObject",
    "Resource": "arn:aws:s3:::${BKT}/monolith-final/*" }] }
JSON
aws iam put-role-policy --role-name BookstoreMonolithRole \
  --policy-name BookstoreSnapshotWrite --policy-document file://snapshot-policy.json
```

| Permission | Service | Why It's Needed |
|------------|---------|-----------------|
| `s3:PutObject` on `<bucket>/monolith-final/*` | S3 | Upload the final `bookstore.db`, and nothing else: no read, list, or delete |

```bash
# on the EC2 box — copy the SQLite file somewhere durable
aws s3 cp bookstore.db s3://bookstore-monolith-snapshot-<account-id>/monolith-final/bookstore.db
```

Optionally create an **AMI** of the instance (EC2 → Actions → Image and templates → Create
image) so you could relaunch the exact monolith if the migration is reverted.

---

## 7.3 Stop first (reversible), then terminate

1. **Stop** the instance: EC2 → Instance state → **Stop instance**. A stopped instance costs
   only EBS storage and can be restarted — your reversible rollback point. Leave it stopped
   for a cool-down period (a day in real life; minutes in the lab) while you watch the
   serverless side in production.
2. Once you're confident, **Terminate**: EC2 → Instance state → **Terminate instance**.

```bash
# CLI: stop, observe, then terminate
aws ec2 stop-instances  --instance-ids <id>
aws ec2 terminate-instances --instance-ids <id>
```

> **Stop ≠ Terminate.** Stop is pause (keep the disk, restart anytime). Terminate is delete
> (instance and, by default, its root volume are gone). The two-phase retire — stop, observe,
> terminate — is how you decommission without burning the bridge prematurely.

---

## 7.4 You've migrated

The bookstore now runs entirely on **API Gateway + Lambda + DynamoDB**. No servers to patch,
each domain scales on its own, and the bill is ~$0 when nobody's shopping. That's the
serverless payoff the monolith couldn't give you — earned through a controlled, route-by-route
**Refactor**, not a big-bang rewrite.

---

## Checkpoint

- [ ] Monolith network traffic has flatlined; no front-door route targets it
- [ ] Every SQLite order id exists in DynamoDB (subset check is empty — counts need **not** match)
- [ ] A final copy of `bookstore.db` is safe in S3 (and/or an AMI exists)
- [ ] Instance **stopped**, observed, then **terminated**
- [ ] The API URL serves the whole bookstore with no EC2 in the path

---

**Next:** [Step 8 — Cleanup](./08-cleanup.md)
