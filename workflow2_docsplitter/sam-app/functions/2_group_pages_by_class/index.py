import json
import boto3
import tarfile
import gzip
import os
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter


s3 = boto3.client("s3")
SPLIT_BUCKET = os.getenv("splitBucket")
OUTPUT_BUCKET = os.getenv("outputBucket")


def get_pdf_reader(s3_bucket, s3_key):
    s3_input_pdf = s3.get_object(Bucket=s3_bucket, Key=s3_key)
    pdf_content = s3_input_pdf["Body"].read()
    pdf_buffer = BytesIO(pdf_content)
    pdf_reader = PdfReader(pdf_buffer)
    return pdf_reader


def put_pdf_page(page, s3_bucket, s3_key):
    writer = PdfWriter()
    writer.add_page(page)
    with BytesIO() as bytes_stream:
        writer.write(bytes_stream)
        bytes_stream.seek(0)
        s3.put_object(
            Body=bytes_stream,
            Bucket=s3_bucket,
            Key=s3_key,
        )


def get_analysis_by_page(analysis):
    """
    Given a list of comprehend analysis, maps the page number with the classification
    """
    anaysis_by_page = {}
    for page in analysis:
        classifications_by_confidence = sorted(
            page["Classes"], key=lambda classification: classification["Score"], reverse=True
        )
        classification = classifications_by_confidence[0][
            "Name"
        ]  # choose the highest confidence one, TODO: flag low confidence classification
        page_number = page["DocumentMetadata"]["PageNumber"]
        anaysis_by_page[page_number] = classification
    return anaysis_by_page


def extract_analysis(s3_bucket, s3_key, original_filename):
    """
    Given an S3 Object of comprehend's output.tar.gz
    Unzips and untars the file into a list of analysis
    https://docs.aws.amazon.com/comprehend/latest/dg/outputs-class-async.html
    """
    analysis = []
    comprehend_s3_object = s3.get_object(Bucket=s3_bucket, Key=s3_key)
    comprehend_object_contents = comprehend_s3_object["Body"].read()
    gzip_file = gzip.GzipFile(fileobj=BytesIO(comprehend_object_contents))

    tar_file = tarfile.TarFile(fileobj=BytesIO(gzip_file.read()))
    print(tar_file.list())
    ex_file_object = tar_file.extractfile(f"{original_filename}.out")
    for line in ex_file_object:
        analysis.append(json.loads(line))
    return analysis


def lambda_handler(event, context):
    """
    TODO: rename to folder 2_0
    Triggered when comprehend completes analysis and uploads a .tar.gz to the S3 bucket
    1. download from S3
    2. open tar.gz
    3. read in analysis
    4. split original pdf in pages
    5. add pages to bucket based on analysis
    """
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    comprehend_analysis_output_key = event["Records"][0]["s3"]["object"]["key"]
    # S3 URI of analysis in the format: f"s3://{COMPREHEND_BUCKET}/{timestamp}/{original_filename}/{chunked_filename}.pdf/{job_id}/output/output.tar.gz"
    # s3://docksplitter-comprehendbucket-1evpwvck307vb/20230209005239/combined/page_8.pdf/819998446679-CLN-80900330fb00b7a8941af7ca9e6fbd6b/output/output.tar.gz
    (
        timestamp,
        original_filename,
        chunked_filename,
        comprehend_job_id,
        comprehend_folder,
        output_filename
    ) = comprehend_analysis_output_key.split("/")

    analysis = extract_analysis(
        bucket_name, comprehend_analysis_output_key, chunked_filename
    )
    analysis_by_page = get_analysis_by_page(analysis)

    chunked_pdf_reader = get_pdf_reader(
        s3_bucket=SPLIT_BUCKET, s3_key=f"{original_filename}/{chunked_filename}"
    )

    # f"s3://{OUTPUT_BUCKET}/{filename}/{classification}/{job_id}/output/output.tar.gz
    # S3 URI s3://docksplitter-outputpdfbucket-s77uwfogkc3p/NB/data/page_1.pdf
    for page_index, page in enumerate(chunked_pdf_reader.pages):
        page_num = page_index + 1
        classification = analysis_by_page[page_num]
        put_pdf_page(
            page,
            s3_bucket=OUTPUT_BUCKET,
            s3_key=f"{original_filename}/{classification}/page_{page_num}",
        )

    return {"message": "SUCCESS"}
