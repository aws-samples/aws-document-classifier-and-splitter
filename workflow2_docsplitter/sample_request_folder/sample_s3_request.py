
import requests

def split_s3_pdf(dns_name, input_pdf_uri, bucket_name, endpoint_arn):
    if dns_name.endswith("/"):
        path = "s3_file"
    else:
        path = "/s3_file"

    queries = f"?bucket_name={bucket_name}&endpoint_arn={endpoint_arn}&input_pdf_uri={input_pdf_uri}"
    url = dns_name + path + queries
    response = requests.post(url)
    print(response.text)


if __name__ == "__main__":
    dns_name = "Enter your dns_name"
    bucket_name = "Enter your bucket_name "
    endpoint_arn = "Enter your endpoint arn"

    input_pdf_path = "s3://sample.pdf"

    split_s3_pdf(dns_name, input_pdf_path, bucket_name, endpoint_arn)
