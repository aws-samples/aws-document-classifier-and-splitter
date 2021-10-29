
import boto3
from io import BytesIO
from pdf2image import convert_from_bytes
from textractcaller.t_call import call_textract
from textractprettyprinter.t_pretty_print import get_lines_string


def process_file(key, datetime_id, bucket_name):
    _class = key.split("/")[1]
    s3 = boto3.client('s3')
    dynamodb = boto3.client('dynamodb')

    s3_response_object = s3.get_object(Bucket=bucket_name, Key=key)
    object_content = s3_response_object['Body'].read()

    if key.endswith(".pdf"):
        images = convert_from_bytes(object_content)
        all_raw_text = ""
        for i, image in enumerate(images):
            image_text = call_textract_for_pdf(image)
            all_raw_text += image_text
        update_dynamodb_row(key, _class, all_raw_text, datetime_id, bucket_name, dynamodb)

    else:
        image_text = call_textract_for_image(object_content)
        update_dynamodb_row(key, _class, image_text, datetime_id, bucket_name, dynamodb)


def call_textract_for_pdf(image):
    buf = BytesIO()
    image.save(buf, format='JPEG')
    byte_string = buf.getvalue()
    return call_textract_for_image(byte_string)


def call_textract_for_image(object_content):
    textract_json = call_textract(input_document=object_content)
    return get_lines_string(textract_json=textract_json)


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
