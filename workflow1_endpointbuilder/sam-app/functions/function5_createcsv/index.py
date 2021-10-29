
import csv
import boto3
from io import StringIO


def create_csv(datetime_id, bucket_name):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(f'DatasetCSVTable_{datetime_id}_{bucket_name}_')

    scan_kwargs = {
        'ProjectionExpression': "#cls, #txt",
        'ExpressionAttributeNames': {"#cls": "class", "#txt": "text"}
    }

    f = StringIO()
    writer = csv.writer(f)
    done = False
    start_key = None
    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = start_key
        response = table.scan(**scan_kwargs)
        documents = response.get('Items', [])
        for doc in documents:
            writer.writerow([doc['class'], doc['text']])
        start_key = response.get('LastEvaluatedKey', None)
        done = start_key is None
    return f


def lambda_handler(event, context):
    datetime_id = event["datetime_id"]
    bucket_name = event["bucket_name"]

    f = create_csv(datetime_id, bucket_name)
    s3 = boto3.client("s3")
    s3.put_object(Body=f.getvalue(), Bucket=bucket_name, Key=f"comprehend_dataset_{datetime_id}.csv")

    return {
        "datetime_id": datetime_id,
        "bucket_name": bucket_name
    }
