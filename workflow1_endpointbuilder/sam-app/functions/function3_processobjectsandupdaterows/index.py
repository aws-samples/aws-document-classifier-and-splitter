
import boto3

dynamodb = boto3.client('dynamodb')
textract = boto3.client('textract')

def process_file(key, datetime_id, bucket_name):
    print(f'processing bucker {bucket_name} with key {key} at {datetime_id}')
    _class = key.split("/")[0]  
    textract_response = textract.detect_document_text(Document={'S3Object': {'Bucket': bucket_name, 'Name': key}})
    #print(textract_response)
    raw_text = " ".join([ block['Text'] for block in textract_response['Blocks'] if 'Text' in block ])
    update_dynamodb_row(key, _class, raw_text, datetime_id, bucket_name, dynamodb)

def update_dynamodb_row(key, _class, raw_text, datetime_id, bucket_name, dynamodb):
    dynamodb.update_item(
        TableName=f'DatasetCSVTable_{datetime_id}_{bucket_name}_',
        Key={
            'objectKey': {
                'S': key
            }
        },
        ExpressionAttributeNames={
            '#cls': 'class',
            '#txt': 'text',
        },
        ExpressionAttributeValues={
            ':c': {
                'S': _class,
            },
            ':t': {
                'S': raw_text,
            },
        },
        UpdateExpression='SET #cls = :c, #txt = :t'
    )


def parse_info(event_source_arn):
    info = event_source_arn.split("_")
    datetime_id = info[1]
    bucket_name = info[2]
    return datetime_id, bucket_name


def lambda_handler(event, context):

    for record in event["Records"]:
        if record["eventName"] == "INSERT":
            new_image = record["dynamodb"]["NewImage"]
            key = new_image["objectKey"]["S"]
            datetime_id, bucket_name = parse_info(record["eventSourceARN"])

            process_file(key, datetime_id, bucket_name)
