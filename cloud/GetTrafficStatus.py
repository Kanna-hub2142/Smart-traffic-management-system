import json
import boto3
import os
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('TABLE_NAME', 'SmartTrafficData'))

# DynamoDB returns Decimal types — convert to float for JSON serialization
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def lambda_handler(event, context):
    response = table.query(
        KeyConditionExpression=Key('node_id').eq('Intersection-A1'),
        ScanIndexForward=False,
        Limit=3
    )
    items = response.get('Items', [])
    if not items:
        return {'statusCode': 404, 'body': json.dumps({'error': 'No data'})}

    latest = items[0]
    recent_summaries = []
    for item in items:
        recent_summaries.append({
            'timestamp': item.get('timestamp'),
            'node_id': item.get('node_id'),
            'metrics': item.get('metrics', {}),
            'alerts': item.get('alerts', {})
        })

    body = {
        'status': 'online',
        'latest_readings': {
            'vehicle_count': latest.get('metrics', {}).get('average_vehicle_count', 0),
            'average_speed': latest.get('metrics', {}).get('average_speed_kmh', 0),
            'noise_level': latest.get('metrics', {}).get('average_noise_db', 0),
            'pollution_level': latest.get('metrics', {}).get('average_pollution_aqi', 0)
        },
        'recent_summaries': recent_summaries
    }

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }