
import boto3
from urllib.parse import urlparse


def insert_table_rows(folder_uri, datetime_id, bucket_name):
    s3_resource = boto3.resource('s3')
    dynamodb = boto3.client("dynamodb")
    folder_name = folder_uri.split(bucket_name + "/", 1)[1]
    bucket = s3_resource.Bucket(bucket_name)
    s3_client = boto3.client("s3")

    for obj in bucket.objects.filter(Prefix=folder_name):
        key = obj.key
        # Skip files that are not PDFs, JPEGs, or PNGs
        object_content_type = s3_client.get_object(
            Bucket=bucket_name,
            Key=key
        )['ContentType']
        valid_content_types = {'application/pdf', 'image/jpeg', 'image/png'}
        if object_content_type in valid_content_types:
            dynamodb.put_item(
                TableName=f'DatasetCSVTable_{datetime_id}_{bucket_name}_',
                Item={
                    'objectKey': {
                        'S': key
                    }
                }
            )


def lambda_handler(event, context):
    folder_uri = event["folder_uri"]
    datetime_id = event["datetime_id"]
    bucket_name = urlparse(folder_uri).hostname

    insert_table_rows(folder_uri, datetime_id, bucket_name)

    return {
        'datetime_id': datetime_id,
        'bucket_name': bucket_name,
    }
