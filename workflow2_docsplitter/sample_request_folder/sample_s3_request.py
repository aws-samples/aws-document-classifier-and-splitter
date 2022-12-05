
import requests
import json

def split_s3_pdf(dns_name, input_pdf_uri, bucket_name, endpoint_arn):
    if dns_name.endswith("/"):
        path = "s3_file"
    else:
        path = "/s3_file"

    data = {"bucket_name":bucket_name, "endpoint_arn":endpoint_arn, "input_pdf_uri": input_pdf_uri} 
    response = requests.post(f'{dns_name}/s3_file', data=json.dumps(data))
    print(response.text)


if __name__ == "__main__":
    dns_name = "http://docsp-LoadB-1NUITP4X14QFQ-1294184009.ap-southeast-2.elb.amazonaws.com"
    bucket_name = "kechn-adapt-apps-src"
    endpoint_arn = "arn:aws:comprehend:ap-southeast-2:819998446679:document-classifier-endpoint/Classifier-20221123042904"
    input_pdf_uri = "s3://kechn-adapt-apps-src/combined.pdf"
    split_s3_pdf(dns_name, input_pdf_uri, bucket_name, endpoint_arn)
