import json
import boto3
import tarfile
import gzip
import os
import io


s3 = boto3.client("s3")
SPLIT_BUCKET = os.getenv("splitBucket")
OUTPUT_BUCKET = os.getenv("outputBucket")


def lambda_handler(event, context):
    """
    Triggered when comprehend completes analysis and uploads a .tar.gz to the S3 bucket
    1. download from S3
    2. open tar.gz
    3. read in analysis
    4. use analysis to sort s3 files
    5. stitch together invoices
    """
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    comprehend_analysis_output_key = event["Records"][0]["s3"]["object"]["key"]
    # key is in the format: f"s3://{OUTPUT_BUCKET}/{timestamp}/f'{filename}/page_{page_index+1}.pdf'"

    # original_filename, page_num, comprehend_job_id, comprehend_output_key, comp

    (
        timestamp,
        original_filename,
        split_pdf_filename,
        comprehend_job_id,
        comprehend_folder,
        output_filename,
    ) = comprehend_analysis_output_key.split("/")

    comprehend_object = s3.get_object(
        Bucket=bucket_name, Key=comprehend_analysis_output_key
    )
    comprehend_object_contents = comprehend_object["Body"].read()
    
    gzip_file = gzip.GzipFile(
        fileobj=io.BytesIO(comprehend_object_contents)
    )

    tar_file = tarfile.TarFile(
        fileobj=io.BytesIO(gzip_file.read())
    )
    print(tar_file.list())
    print(comprehend_analysis_output_key)
    ex_file_object = tar_file.extractfile(f"{split_pdf_filename}.out")
    analysis = json.load(ex_file_object)

    classifications_by_confidence = sorted(
        analysis["Classes"], key=lambda classification: classification["Score"]
    )
    classification = classifications_by_confidence[0][
        "Name"
    ]  # choose the highest confidence one, TODO: flag low confidence classification
    submitted_comprehend_filename = analysis["File"]

    # page_number is: page_1.pdf

    s3.copy_object(
        Bucket=OUTPUT_BUCKET,
        Key=f"{original_filename}/{classification}/{split_pdf_filename}",
        CopySource={
            "Bucket": SPLIT_BUCKET,
            "Key": f"{original_filename}/{split_pdf_filename}",  # refactor s3 key bucket nto shared library
        },
    )

    return {"message": "SUCCESS"}
