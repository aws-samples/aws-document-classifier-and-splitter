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
# customer uploads a file exceeding lambda memory limit of 512MB
# filename contains / - unlikely given windows and linux file naming restrictuions
# file name containts a space
# Comprehend creates 2 jobs at the exact same time
# Error handling for service errors

s3 = boto3.client("s3")

SPLIT_BUCKET = os.getenv("outputBucket")


def is_pdf(s3_key):
    file_ext = s3_key.split(".")[-1]
    return file_ext.lower() == "pdf"


def is_last_page(pdf_reader, page_num):
    return page_num >= len(pdf_reader.pages)


def lambda_handler(event, context):
    """
    Triggered when an PDF is uploaded to an S3 bucket
    1. download from S3
    2. Spit the PDF into 100page PDFs
    3. Save to S3
    """
    bucket_name = event["Records"][0]["s3"]["bucket"][
        "name"
    ]  # Event is not an S3 event, throw exception if Key Error
    input_pdf_key = event["Records"][0]["s3"]["object"]["key"]

    if not is_pdf(input_pdf_key):
        raise Exception("The uploaded object is not a PDF file: %s" % input_pdf_key)

    print(bucket_name, input_pdf_key)

    # Read PDF into memory
    s3_input_pdf = s3.get_object(Bucket=bucket_name, Key=input_pdf_key)
    input_pdf_content = s3_input_pdf[
        "Body"
    ].read()  # S3 could return an empty object with no body
    input_pdf_buffer = BytesIO(input_pdf_content)
    input_pdf_reader = PdfReader(input_pdf_buffer)

    # Save the file after 100 pages are added
    writer = PdfWriter()
    for page_index, page in enumerate(input_pdf_reader.pages):
        page_num = page_index + 1
        writer.add_page(page)

        if len(writer.pages) == 100 or is_last_page(input_pdf_reader, page_num):
            with BytesIO() as bytes_stream:
                writer.write(bytes_stream)
                bytes_stream.seek(0)
                filename = input_pdf_key.replace(".pdf", "")
                s3.put_object(
                    Body=bytes_stream,
                    Bucket=SPLIT_BUCKET,
                    Key=f"{filename}/page_{page_num}.pdf",
                )
            writer = PdfWriter()

    return {"message": "SUCCESS"}
