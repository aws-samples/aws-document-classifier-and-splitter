import json
import boto3
import tarfile
import gzip
import os
import io
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter

s3 = boto3.client("s3")
comprehend = boto3.client("comprehend")

CLASSIFIED_BUCKET = os.getenv("classifiedBucket")
OUTPUT_BUCKET = os.getenv("outputBucket")
COMPREHEND_ROLE_ARN = os.getenv("comprehendRoleArn")


def lambda_handler(event, context):
    """
    Triggered when a new file is added to the s3 bucket that groups PDF pages by classification
    1. Check comprehend that all analysis for the original PDF is completed
    2. Use the original PDF and create seperate documents for each
        or
    2. Use the chunked PDFs and stitch them together

    """
    s3_bucket = event["Records"][0]["s3"]["bucket"]["name"]
    s3_key = event["Records"][0]["s3"]["object"]["key"]
    print(event)

    return {"message": "SUCCESS"}
