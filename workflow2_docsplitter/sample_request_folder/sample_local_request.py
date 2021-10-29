
import requests

def split_local_pdf(dns_name, input_pdf_path, bucket_name, endpoint_arn):
    if dns_name.endswith("/"):
        path = "local_file"
    else:
        path = "/local_file"

    with open(input_pdf_path, "rb") as file:
        files = {
            "input_pdf_file": file
        }
        url = dns_name + f"{path}?bucket_name={bucket_name}&endpoint_arn={endpoint_arn}"
        response = requests.post(url, files=files)
        print(response.text)


if __name__ == "__main__":
    dns_name = "Enter your dns_name"
    bucket_name = "Enter your bucket_name "
    endpoint_arn = "Enter your endpoint arn"

    input_pdf_path = "~/sample.pdf"

    split_local_pdf(dns_name, input_pdf_path, bucket_name, endpoint_arn)
