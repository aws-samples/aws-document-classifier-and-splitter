
import boto3


def check_endpoint(endpoint_arn):
    comprehend = boto3.client("comprehend")
    describe_response = comprehend.describe_endpoint(
        EndpointArn=endpoint_arn
    )

    endpoint_is_complete = False
    status = describe_response["EndpointProperties"]["Status"]
    if status != "IN_SERVICE":
        if status == "FAILED":
            message = describe_response["EndpointProperties"]["Message"]
            raise ValueError(f"The endpoint is in error:", message)
    else:
        endpoint_is_complete = True

    return endpoint_is_complete


def lambda_handler(event, context):
    endpoint_arn = event["endpoint_arn"]

    endpoint_is_complete = check_endpoint(endpoint_arn)

    return {
        'endpoint_is_complete': endpoint_is_complete,
        'endpoint_arn': endpoint_arn
    }
