
from __future__ import print_function
import urllib3
import json
import boto3


http = urllib3.PoolManager()

def send(event, context, responseStatus, responseData, physicalResourceId=None, noEcho=False, reason=None):
    responseUrl = event['ResponseURL']

    print(responseUrl)

    responseBody = {
        'Status': responseStatus,
        'Reason': reason or "See the details in CloudWatch Log Stream: {}".format(context.log_stream_name),
        'PhysicalResourceId': physicalResourceId or context.log_stream_name,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'NoEcho': noEcho,
        'Data': responseData
    }

    json_responseBody = json.dumps(responseBody)

    print("Response body:")
    print(json_responseBody)

    headers = {
        'content-type': '',
        'content-length': str(len(json_responseBody))
    }

    try:
        response = http.request('PUT', responseUrl, headers=headers, body=json_responseBody)
        print("Status code:", response.status)


    except Exception as e:

        print("send(..) failed executing http.request(..):", e)


def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    vpc_response = ec2.describe_vpcs(
        Filters=[
            {
                'Name': 'is-default',
                'Values': [
                    'true'
                ]
            }
        ]
    )
    vpc_id = vpc_response['Vpcs'][0]['VpcId']

    subnet_response = ec2.describe_subnets(
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [
                    vpc_id
                ]
            }
        ]
    )
    subnet_ids = [subnet['SubnetId'] for subnet in subnet_response['Subnets']]

    response_data = {
        'VpcId': vpc_id,
        'Subnets': subnet_ids
    }

    return send(event, context, "SUCCESS", response_data)
