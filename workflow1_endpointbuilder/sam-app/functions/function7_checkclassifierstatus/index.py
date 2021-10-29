
import boto3


def check_classifier(classifier_arn):
    comprehend = boto3.client("comprehend")
    describe_response = comprehend.describe_document_classifier(
        DocumentClassifierArn=classifier_arn
    )

    is_trained = False
    status = describe_response['DocumentClassifierProperties']['Status']
    if status != "TRAINED":
        if status == "IN_ERROR":
            message = describe_response["DocumentClassifierProperties"]["Message"]
            raise ValueError(f"The classifier is in error:", message)
    else:
        is_trained = True

    return is_trained


def lambda_handler(event, context):
    datetime_id = event["datetime_id"]
    classifier_arn = event["classifier_arn"]

    is_trained = check_classifier(classifier_arn)

    return {
        'is_trained': is_trained,
        'datetime_id': datetime_id,
        'classifier_arn': classifier_arn
    }
