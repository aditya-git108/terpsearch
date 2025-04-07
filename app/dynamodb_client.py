import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta

# Configure DynamoDB table
dynamodb = boto3.resource('dynamodb', region_name='us-east-1') 
table = dynamodb.Table('YourDynamoDBTableName')  # replace with  table name

def fetch_posts_for_last_n_weeks(weeks=4):
    now = datetime.utcnow()
    start_time = now - timedelta(weeks=weeks)

    # Scan posts by timestamp (assumes 'timestamp' is stored in ISO8601 format)
    response = table.scan()  
    items = response['Items']

    filtered = [item for item in items if datetime.fromisoformat(item['timestamp']) >= start_time]
    return [{"text": item["text"], "timestamp": item["timestamp"]} for item in filtered]
