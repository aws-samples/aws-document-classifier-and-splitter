import json
import os
import base64
import boto3
import zipfile
from io import BytesIO
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter

# Edge cases:
# when customer upload file with the same filename
# customer uploads a file exceeding memory limit
# filename contains / - unlikely given windows and linux file naming restrictuions
# file name containts a space

s3 = boto3.client("s3")

SPLIT_BUCKET = os.getenv("outputBucket")


def lambda_handler(event, context):
    """
    Triggered when an PDF is uploaded to an S3 bucket
    1. download from S3
    2. Save back into key splt by page
    """
    _id = datetime.now().strftime("%Y%m%d%H%M%S")
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    input_pdf_key = event["Records"][0]["s3"]["object"]["key"]

    file_ext = input_pdf_key.split(".")[-1]
    if not file_ext.lower() == "pdf":
        raise Exception("The uploaded object is not a PDF file: %s" % input_pdf_key)
        
    print(bucket_name, input_pdf_key)
    print('hello world')

    # Read PDF into memory
    s3_input_pdf = s3.get_object(Bucket=bucket_name, Key=input_pdf_key)
    input_pdf_content = s3_input_pdf["Body"].read()
    input_pdf_buffer = BytesIO(input_pdf_content)

    # For each page in the PDF
    input_pdf_reader = PdfReader(input_pdf_buffer)
    for page_index, page in enumerate(input_pdf_reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        with BytesIO() as bytes_stream:
            writer.write(bytes_stream)
            bytes_stream.seek(0)
            filename = input_pdf_key.replace(".pdf", "")
            s3.put_object(
                Body=bytes_stream,
                Bucket=SPLIT_BUCKET,
                Key=f"{filename}/page_{page_index+1}.pdf",
            )

    return {"message": "SUCCESS"}
