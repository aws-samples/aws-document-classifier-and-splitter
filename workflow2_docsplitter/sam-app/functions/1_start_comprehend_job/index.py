import json
import os
import boto3
from io import BytesIO
from datetime import datetime


s3 = boto3.client("s3")
textract = boto3.client("textract")
comprehend = boto3.client("comprehend")

OUTPUT_BUCKET = os.getenv("outputBucket")
COMPREHEND_ROLE_ARN = os.getenv("comprehendRoleArn")


def is_pdf(s3_key):
    file_ext = s3_key.split(".")[-1]
    return file_ext.lower() == "pdf"


def start_classifier_job(model_arn, input_s3_object_uri, output_s3_uri):
    start_job_response = comprehend.start_document_classification_job(
        InputDataConfig={
            "S3Uri": input_s3_object_uri,
            "InputFormat": "ONE_DOC_PER_FILE",
            "DocumentReaderConfig": {
                "DocumentReadAction": "TEXTRACT_DETECT_DOCUMENT_TEXT"
            },
        },
        OutputDataConfig={"S3Uri": output_s3_uri},
        DataAccessRoleArn=COMPREHEND_ROLE_ARN,
        DocumentClassifierArn=model_arn,
    )
    return start_job_response


def lambda_handler(event, context):
    """
    Triggered when an PDF is uploaded to an S3 bucket
    1. download from S3
    2. extract text from pdf
    3. send text to comprehend for classification
    4. return job ids
    """
    model_arn = "arn:aws:comprehend:ap-southeast-2:819998446679:document-classifier/Classifier-20230206140257"

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    s3_bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    s3_pdf_key = event["Records"][0]["s3"]["object"]["key"]

    if not is_pdf(s3_pdf_key):
        raise Exception("The uploaded object is not a PDF file: %s" % s3_pdf_key)

    # key is class name; value is list of page numbers belonging to the key class
    job = start_classifier_job(
        model_arn=model_arn,
        input_s3_object_uri=f"s3://{s3_bucket_name}/{s3_pdf_key}",
        output_s3_uri=f"s3://{OUTPUT_BUCKET}/{timestamp}/{s3_pdf_key}",
    )

    return {"job": job}
