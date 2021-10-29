
import boto3


def check_table(datetime_id, bucket_name):
    dynamodb_resource = boto3.resource('dynamodb')
    table = dynamodb_resource.Table(f'DatasetCSVTable_{datetime_id}_{bucket_name}_')

    scan_kwargs = {
        'Select': 'COUNT',
        'FilterExpression': 'attribute_not_exists(#cls)',
        'ExpressionAttributeNames': {'#cls': 'class'}
    }

    done = False
    start_key = None
    rows_not_filled = 0
    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = start_key
        response = table.scan(**scan_kwargs)
        rows_not_filled += response['Count']
        start_key = response.get('LastEvaluatedKey', None)
        done = start_key is None

    if rows_not_filled == 0:
        return True
    else:
        return False


def lambda_handler(event, context):
    datetime_id = event["datetime_id"]
    bucket_name = event["bucket_name"]

    is_complete = check_table(datetime_id, bucket_name)

    return {
        'is_complete': is_complete,
        'datetime_id': datetime_id,
        'bucket_name': bucket_name
    }
