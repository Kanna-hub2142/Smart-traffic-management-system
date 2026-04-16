import json
import boto3
import os
import uuid
import logging
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TABLE_NAME', 'TrafficData')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """
    AWS Lambda handler to process messages from SQS and store them in DynamoDB.
    Expected event payload format (from API Gateway -> SQS):
    {
      "Records": [
        {
          "body": "{\"timestamp\": 1709320000, \"node_id\": \"Intersection-A1\", \"metrics\": {...}, \"alerts\": {...}}"
        }
      ]
    }
    """
    logger.info(f"Received {len(event.get('Records', []))} records from SQS")
    
    successful_processed = 0
    failed_processed = 0

    for record in event.get('Records', []):
        try:
            # SQS body contains the original JSON payload sent to API Gateway
            body_str = record.get('body', '{}')
            payload = json.loads(body_str, parse_float=Decimal)  # DynamoDB requires Decimal, not float
            
            # Additional validation can be done here.
            node_id = payload.get('node_id', 'UnknownNode')
            timestamp = payload.get('timestamp', 0)
            
            # Create a unique ID for the DB entry if needed, but usually a composite key
            # of node_id (Partition Key) and timestamp (Sort Key) is best for time-series data.
            item = {
                'node_id': node_id,          # Partition Key
                'timestamp': int(timestamp), # Sort Key
                'message_id': record.get('messageId', str(uuid.uuid4())),
                'metrics': payload.get('metrics', {}),
                'alerts': payload.get('alerts', {})
            }
            
            # Put item into DynamoDB
            table.put_item(Item=item)
            successful_processed += 1
            logger.info(f"Successfully stored item for node {node_id} at {timestamp}")
            
        except Exception as e:
            logger.error(f"Error processing record: {e}")
            logger.error(f"Failed Record Body: {record.get('body', 'No Body')}")
            failed_processed += 1
            # Depending on SQS configuration, you might want to raise the exception 
            # to trigger a DLQ (Dead Letter Queue) retry mechanism.
            # raise e 

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Processing complete',
            'successful': successful_processed,
            'failed': failed_processed
        })
    }
