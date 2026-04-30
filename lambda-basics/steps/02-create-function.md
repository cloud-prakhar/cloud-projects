# Step 2 — Create and Deploy Your First Lambda Function

In this step you create the Lambda function in the Console, upload the code, and verify it is ready to run.

---

## 2.1 Review the Handler Code

Open `src/hello_world.py` before deploying. The key things to notice:

```python
def handler(event, context):
```

- **`event`** — a Python dict containing the trigger's input data. For a manual test invocation, you control the shape.
- **`context`** — injected by the Lambda runtime. Contains:
  - `context.function_name` — the function's name as deployed
  - `context.aws_request_id` — unique ID for this invocation (use it in logs for tracing)
  - `context.memory_limit_in_mb` — the configured memory
  - `context.get_remaining_time_in_millis()` — milliseconds before timeout

---

## 2.2 Package the Code

Open a terminal and run:

```bash
cd /path/to/lambda-basics

# The -j flag strips directory prefixes so hello_world.py lands at the root of the ZIP
zip -j hello_world.zip src/hello_world.py
```

> **Why `-j` matters:** Lambda looks for `hello_world.py` at the ZIP root. If the file is nested under `src/hello_world.py` inside the archive, Lambda cannot find it and returns `Runtime.ImportModuleError`.

---

## 2.3 Create the Function in the Console

1. In the AWS Console, search for **Lambda** and open it.
2. Click **Create function**.
3. Select **Author from scratch**.

Fill in the fields:

| Field | Value |
|-------|-------|
| Function name | `HelloWorldLambda` |
| Runtime | **Python 3.14** |
| Architecture | x86_64 |

Under **Permissions → Change default execution role**:

| Field | Value |
|-------|-------|
| Execution role | **Use an existing role** |
| Existing role | `LambdaBasicsExecutionRole` |

Click **Create function**.

---

## 2.4 Upload the Code

On the function page, scroll to the **Code source** panel:

1. Click **Upload from** → **.zip file**
2. Select `hello_world.zip`
3. Click **Save**

After the upload, confirm the handler string is correct:

1. Click the **Configuration** tab → **General configuration** → **Edit**
2. Verify **Handler** is set to `hello_world.handler`

   > The handler format is `<filename_without_.py>.<function_name>`. Since the file is `hello_world.py` and the function inside it is `handler`, the string is `hello_world.handler`.

3. While here, set:

   | Setting | Value |
   |---------|-------|
   | Memory | 128 MB |
   | Timeout | 10 sec |

4. Click **Save**.

---

## 2.5 Verify the Function is Active

In the top banner of the function page, the **State** badge should show **Active**. If it shows **Pending**, wait 10–15 seconds and refresh.

### Via AWS CLI

```bash
aws lambda get-function \
  --function-name HelloWorldLambda \
  --query 'Configuration.{State:State,Runtime:Runtime,Handler:Handler}' \
  --output table
```

Expected:

```
+----------------------+--------------+---------+
|  hello_world.handler |  python3.14  |  Active |
+----------------------+--------------+---------+
```

---

## Checkpoint

- [ ] Function `HelloWorldLambda` exists in the Lambda console
- [ ] State is **Active**
- [ ] Runtime is **Python 3.14**
- [ ] Handler is `hello_world.handler`
- [ ] Execution role is `LambdaBasicsExecutionRole`

---

**Next:** [Step 3 — Test, Invoke, and Read CloudWatch Logs](./03-test-invoke.md)
