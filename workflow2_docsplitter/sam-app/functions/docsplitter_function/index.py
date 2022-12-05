
import json
import base64
import boto3
import zipfile
from io import BytesIO
from datetime import datetime
from pdf2image import convert_from_bytes
from PyPDF2 import PdfFileReader, PdfFileWriter
from textractcaller.t_call import call_textract
from textractprettyprinter.t_pretty_print import get_lines_string

s3 = boto3.client('s3')
textract = boto3.client('textract')
comprehend = boto3.client('comprehend')

class PdfFileWriterWithStreamAttribute(PdfFileWriter):
    def __init__(self):
        super().__init__()
        self.stream = BytesIO()
        
def call_textract_on_image(textract, image, i):
    # return JSON response containing the text extracted from the image
    print(f"Inputting image {i} into Textract")
    buf = BytesIO()
    image.save(buf, format='JPEG')
    byte_string = buf.getvalue()
    return call_textract(input_document=byte_string, boto3_textract_client=textract)


def call_comprehend(text, comprehend, endpoint_arn):
    # send in raw text for a document as well as the Comprehend custom classification model ARN
    # returns JSON response containing the document's predicted class
    print("Inputting text into Comprehend model")
    return comprehend.classify_document(
        Text=text,
        EndpointArn=endpoint_arn
    )


def add_page_to_class(i, _class, pages_by_class):
    # appends a page number (integer) to list of page numbers (value in key-value pair)
    # stores information on how the original multi-page input PDF file is divided by class
    # stores page numbers in order, so the final outputted multi-class PDF pages will be in order
    if _class in pages_by_class:
        pages_by_class[_class].append(i)
    else:
        pages_by_class[_class] = [i]
    print(f"Added page {i} to {_class}\n")


def create_pdfs_classified_data(input_pdf_content, pages_by_class):
    # loops through each class in the pages_by_class dictionary to get all of the input PDF page numbers
    # creates new PDF for each class using the corresponding input PDF's pages
    # Edited: now only print a PDF document for each page that has been classified "data"

    input_pdf_buffer = BytesIO(input_pdf_content)
    input_pdf = PdfFileReader(input_pdf_buffer, strict=False)
    output_zip_buffer = BytesIO()
    if 'data' not in pages_by_class:
        raise Exception('Data not found in document') 
        
    # Create a zip file
    with zipfile.ZipFile(output_zip_buffer, "w") as zip_archive:

        # create a PDF for each page
        for i, page_num in enumerate(pages_by_class['data']):
            data_page = input_pdf.getPage(page_num)
            output_buffer = BytesIO()
            writer = PdfFileWriterWithStreamAttribute()
            writer.addPage(data_page)
            writer.write(output_buffer)
            # add i.pdf to zip file
            with zip_archive.open(f"{i}.pdf", 'w') as output_pdf:
                output_pdf.write(output_buffer.getvalue())
            print(f"Created PDF for {i}")

    return output_zip_buffer


def split_input_pdf_by_class(input_pdf_content, endpoint_arn, _id):
    # loops through each page of the inputted multi-page PDF
    # converts single-page PDF into an image and uploads it to the S3 bucket
    # image in S3 is inputted into the Textract API; text is extracted, JSON is parsed
    # raw text is inputted into the Comprehend model API using its endpoint ARN
    # JSON response is parsed to find the predicted class
    # the input PDF's page number is assigned to the predicted class in the pages_by_class dictionary
    pages_by_class = {}

    # converts PDF into images
    images = convert_from_bytes(input_pdf_content)

    # process each image
    for i, image in enumerate(images):
        textract_response = call_textract_on_image(textract, image, i)
        raw_text = get_lines_string(textract_json=textract_response)[:4500]
        comprehend_response = call_comprehend(raw_text, comprehend, endpoint_arn)
        _class = comprehend_response['Classes'][0]['Name']
        add_page_to_class(i, _class, pages_by_class)

    print("Input PDF has been split up and classified\n")
    return pages_by_class


def lambda_handler(event, context):
    if event['path'] == '/':
        return {
            "statusCode": 200,
            "statusDescription": "200 OK",
            "isBase64Encoded": False,
            "headers": {
                "Content-Type": "text/html"
            },
            "body": "This is the Document Splitter API."
        }

    request_body = json.loads(base64.b64decode(event['body']))
    endpoint_arn = request_body['endpoint_arn']
    bucket_name = request_body['bucket_name']

    _id = datetime.now().strftime("%Y%m%d%H%M%S")

    input_pdf_uri = request_body['input_pdf_uri']
    input_pdf_key = input_pdf_uri.split(bucket_name + "/", 1)[1]

    # pages_by_class is a dictionary
    # key is class name; value is list of page numbers belonging to the key class
    s3_input_pdf = s3.get_object(Bucket=bucket_name, Key=input_pdf_key)
    input_pdf_content = s3_input_pdf['Body'].read()
    
    # pages_by_class is a dictionary
    # key is class name; value is list of page numbers belonging to the key class
    pages_by_class = split_input_pdf_by_class(input_pdf_content, endpoint_arn, _id)
    
    output_zip_buffer = create_pdfs_classified_data(input_pdf_content, pages_by_class)

    output_key_name = f"workflow2_output_documents_{_id}.zip"
    s3.put_object(Body=output_zip_buffer.getvalue(), Bucket=bucket_name, Key=output_key_name, ContentType='application/zip')

    output_zip_file_s3_uri = f"s3://{bucket_name}/{output_key_name}"
    return {
        "statusCode": 200,
        "statusDescription": "200 OK",
        "isBase64Encoded": False,
        "headers": {
            "Content-Type": "text/html"
        },
        "body": json.dumps(
            {
                'output_zip_file_s3_uri': output_zip_file_s3_uri
            }
        )
    }
