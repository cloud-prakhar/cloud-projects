import boto3

sqs = boto3.client('sqs', region_name='us-east-1')
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/279150584486/testqueue"

for i in range(1, 11):
    response = sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=f'{{"test": "message {i}"}}'
    )
    print(f"Sent message {i}: {response['MessageId']}")
