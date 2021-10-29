
import os
import boto3


def train_classifier(datetime_id, bucket_name, role_arn, classifier_name):
    comprehend = boto3.client("comprehend")

    # create classifier with the CSV training dataset's S3 URI and the ARN of the IAM role
    create_response = comprehend.create_document_classifier(
        InputDataConfig={
            'S3Uri': f"s3://{bucket_name}/comprehend_dataset_{datetime_id}.csv"
        },
        DataAccessRoleArn=role_arn,
        DocumentClassifierName=classifier_name,
        LanguageCode='en'
    )

    classifier_arn = create_response['DocumentClassifierArn']
    return classifier_arn


def lambda_handler(event, context):
    datetime_id = event["datetime_id"]
    bucket_name = event["bucket_name"]

    classifier_name = f"Classifier-{datetime_id}"

    role_arn = os.environ.get('FUNCTION6_TRAIN_CLASSIFIER_COMPREHEND_ROLE_ARN')
    classifier_arn = train_classifier(datetime_id, bucket_name, role_arn, classifier_name)

    return {
        'datetime_id': datetime_id,
        'classifier_arn': classifier_arn
    }