
import boto3


def build_endpoint(classifier_arn, datetime_id):
    comprehend = boto3.client("comprehend")
    endpoint_response = comprehend.create_endpoint(
        EndpointName=f"Classifier-{datetime_id}",
        ModelArn=classifier_arn,
        DesiredInferenceUnits=10,
    )
    endpoint_arn = endpoint_response["EndpointArn"]
    return endpoint_arn


def lambda_handler(event, context):
    datetime_id = event["datetime_id"]
    classifier_arn = event["classifier_arn"]

    endpoint_arn = build_endpoint(classifier_arn, datetime_id)

    return {
        'endpoint_arn': endpoint_arn
    }
