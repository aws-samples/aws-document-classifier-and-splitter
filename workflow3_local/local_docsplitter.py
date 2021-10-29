
import os
import boto3
from shutil import rmtree
from datetime import datetime
from pdf2image import convert_from_path
from PyPDF2 import PdfFileReader, PdfFileWriter
from textractcaller.t_call import call_textract
from textractprettyprinter.t_pretty_print import get_lines_string


def call_textract_on_image(textract, image_path):
    # return JSON response containing the text extracted from the image
    print(f"Inputting {image_path} into Textract")
    # send in local image file content (is base64-encoded by API)
    with open(image_path, "rb") as f:
        return call_textract(input_document=f.read(), boto3_textract_client=textract)


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
    print(f"Added page {i + 1} to {_class}\n")


def create_directories(dirs_list):
    for dir_name in dirs_list:
        try:
            os.mkdir(dir_name)
        except FileExistsError:
            pass
    print("Created directories")


def create_output_pdfs(input_pdf_path, pages_by_class, output_dir_path, output_dir_name):
    # loops through each class in the pages_by_class dictionary to get all of the input PDF page numbers
    # creates new PDF for each class using the corresponding input PDF's pages
    # outputted multi-class PDFs are located in the output folder

    with open(input_pdf_path, "rb") as f:
        for _class in pages_by_class:
            output = PdfFileWriter()
            page_numbers = pages_by_class[_class]
            input_pdf = PdfFileReader(f)

            for page_num in page_numbers:
                output.addPage(input_pdf.getPage(page_num))
            with open(f"{output_dir_path}/{_class}.pdf", "wb") as output_stream:
                output.write(output_stream)

            print(f"Created PDF for {_class}")


def split_input_pdf_by_class(input_pdf_path, temp_dir_path, endpoint_arn, _id):
    # loops through each page of the inputted multi-page PDF
    # converts single-page PDF into an image and uploads it to the S3 bucket
    # image in S3 is inputted into the Textract API; text is extracted, JSON is parsed
    # raw text is inputted into the Comprehend model API using its endpoint ARN
    # JSON response is parsed to find the predicted class
    # the input PDF's page number is assigned to the predicted class in the pages_by_class dictionary
    textract = boto3.client('textract')
    comprehend = boto3.client('comprehend')
    pages_by_class = {}

    # converts PDF into images
    image_paths = convert_from_path(
        pdf_path=input_pdf_path,
        fmt='jpeg',
        paths_only=True,
        output_folder=temp_dir_path
    )

    # process each image
    for i, image_path in enumerate(image_paths):
        textract_response = call_textract_on_image(textract, image_path)
        raw_text = get_lines_string(textract_json=textract_response)
        comprehend_response = call_comprehend(raw_text, comprehend, endpoint_arn)
        _class = comprehend_response['Classes'][0]['Name']
        add_page_to_class(i, _class, pages_by_class)

    print("Input PDF has been split up and classified\n")
    return pages_by_class


def main(endpoint_arn, choice, input_pdf_info):
    root_path = os.path.dirname(os.path.abspath(__file__))
    _id = datetime.now().strftime("%Y%m%d%H%M%S")
    temp_dir_name = f"workflow2_temp_documents-{_id}"
    temp_dir_path = f"{root_path}/{temp_dir_name}"
    output_dir_name = f"workflow2_output_documents-{_id}"
    output_dir_path = f"{root_path}/{output_dir_name}"
    create_directories([temp_dir_path, output_dir_path])
    s3 = boto3.client('s3')

    if choice == "s3":
        input_pdf_uri = input_pdf_info
        bucket_name = input_pdf_uri.split("/")[2]
        input_pdf_key = input_pdf_uri.split(bucket_name + "/", 1)[1]
        input_pdf_path = f"{temp_dir_path}/input.pdf"
        with open(input_pdf_path, "wb") as data:
            s3.download_fileobj(bucket_name, input_pdf_key, data)
    elif choice == "local":
        input_pdf_path = input_pdf_info

    # pages_by_class is a dictionary
    # key is class name; value is list of page numbers belonging to the key class
    pages_by_class = split_input_pdf_by_class(input_pdf_path, temp_dir_path, endpoint_arn, _id)

    create_output_pdfs(input_pdf_path, pages_by_class, output_dir_path, output_dir_name)
    rmtree(temp_dir_path)
    print("Multi-class PDFs have been created in the output folder, " + output_dir_path)


print("Welcome to the local document splitter!")
endpoint_arn = input("Please enter the ARN of the Comprehend classification endpoint: ")

print("Would you like to split a local file or a file stored in S3?")
choice = input("Please enter 'local' or 's3': ")
if choice == 'local':
    input_pdf_info = input("Please enter the absolute local file path of the input PDF: ")
elif choice == 's3':
    input_pdf_info = input("Please enter the S3 URI of the input PDF: ")

main(endpoint_arn, choice, input_pdf_info)
