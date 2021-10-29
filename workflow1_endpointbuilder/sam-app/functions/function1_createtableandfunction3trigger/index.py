
import boto3
import datetime
from urllib.parse import urlparse


def create_dataset_table(datetime_id, bucket_name):
    dynamodb_resource = boto3.resource('dynamodb')
    dynamodb_resource.create_table(
        TableName=f'DatasetCSVTable_{datetime_id}_{bucket_name}_',
        KeySchema=[
            {
                'AttributeName': 'objectKey',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'objectKey',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 1000,
            'WriteCapacityUnits': 1000
        },
        StreamSpecification={
            'StreamEnabled': True,
            'StreamViewType': 'NEW_AND_OLD_IMAGES'
        }
    )


def create_function3_trigger(stream_arn):
    lambda_client = boto3.client('lambda')
    lambda_client.create_event_source_mapping(
        EventSourceArn=stream_arn,
        FunctionName='EndpointBuilder-Function3-ProcessObjects',
        Enabled=True,
        BatchSize=1000,
        ParallelizationFactor=10,
        StartingPosition='TRIM_HORIZON',
        BisectBatchOnFunctionError=True,
        MaximumRetryAttempts=3,
        FunctionResponseTypes=[
            'ReportBatchItemFailures',
        ]
    )


def lambda_handler(event, context):
    folder_uri = event["folder_uri"]
    bucket_name = urlparse(folder_uri).hostname
    datetime_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    create_dataset_table(datetime_id, bucket_name)

    dynamodb_client = boto3.client('dynamodb')
    while True:
        response = dynamodb_client.describe_table(
            TableName=f'DatasetCSVTable_{datetime_id}_{bucket_name}_'
        )
        status = response["Table"]["TableStatus"]
        if status == "ACTIVE":
            stream_arn = response['Table']['LatestStreamArn']
            break

    create_function3_trigger(stream_arn)

    return {
        'datetime_id': datetime_id,
        'folder_uri': folder_uri
    }
