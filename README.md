# Intelligently Split Multi-Form Document Packages with Amazon Textract and Amazon Comprehend

## Workflow 1: Endpoint Builder

#### Description
Workflow 1 will take documents stored on Amazon S3 and send them through a series of steps to extract the data from the documents via Amazon Textract. 
Then, the extracted data will be used to create an Amazon Comprehend Custom Classification Endpoint.

#### Input:
The Amazon S3 URI of the **folder** containing the training dataset files (these can be images, single-page PDFs, and/or multi-page PDFs). 
The structure of the folder must be:

    root dataset directory
    ---- class directory
    -------- files

or 

    root dataset directory
    ---- class directory
    -------- nested subdirectories
    ------------ files
    
Note that the name of the class subdirectories (2nd directory level) become the names of the classes used in the Amazon Comprehend custom classification model. For example, see the file structure below; the class for "form123.pdf" would be "tax_forms".

    training_dataset
    ---- tax_forms
    -------- page_1
    ------------ form123.pdf


#### Output:
The ARN (Amazon Resource Number) of the model's endpoint, which can be used to classify documents in Workflow 2.

#### Usage:
You must have Docker installed, configured and running. You must also have the AWS CLI and AWS SAM CLI installed and configured with your AWS credentials.
Navigate to the workflow1_endpointbuilder/sam-app directory. 
Run 'sam build' and 'sam deploy --guided' in your CLI and provide the Stack Name and AWS Region (ensure that this is the same region as your Amazon S3 dataset folder). You must respond with "y" for the "Allow SAM CLI IAM role creation" and "Create managed ECR repositories for all functions?" prompts. 
This will deploy CloudFormation stacks that create the infrastructure for the Endpoint Builder state machine in Amazon Step Functions.
For example, see below the CLI input:
    
    (venv) Lambda_Topic_Classifier % cd workflow1_endpointbuilder/sam-app 
    (venv) sam-app % sam build
    Build Succeeded

    (venv) sam-app % sam deploy --guided
    Configuring SAM deploy
    =========================================
    Stack Name [sam-app]: endpointbuilder
    AWS Region []: us-east-1
    #Shows you resources changes to be deployed and require a 'Y' to initiate deploy
    Confirm changes before deploy [y/N]: n
    #SAM needs permission to be able to create roles to connect to the resources in your template
    Allow SAM CLI IAM role creation [Y/n]: y
    Save arguments to configuration file [Y/n]: n

    Looking for resources needed for deployment:
    Creating the required resources...
    Successfully created!
    Managed S3 bucket: {your_bucket}
    #Managed repositories will be deleted when their functions are removed from the template and deployed
    Create managed ECR repositories for all functions? [Y/n]: y
    
and CLI output:

    CloudFormation outputs from deployed stack
    -------------------------------------------------------------------------------------------------
    Outputs                                                                                         
    -------------------------------------------------------------------------------------------------
    Key                 StateMachineArn                                                             
    Description         Arn of the EndpointBuilder State Machine                                    
    Value              {state_machine_arn}                      
    -------------------------------------------------------------------------------------------------

Find the corresponding state machine in Amazon Step Functions and start a new execution, providing your Amazon S3 folder URI as a string in the `folder_uri` key-pair argument. 

    {
      "folder_uri": "s3://{your_bucket_name}"
    }

The state machine returns the Amazon Comprehend classifier's endpoint ARN as a string in the `endpoint_arn` key-pair:

    {
      "endpoint_arn": "{your_end_point_ARN}"
    }

## Workflow 2: Document Splitter API

#### Description
Workflow 2 will take the endpoint you created in Workflow 1 and split the documents based on the classes with which model has been trained. 

#### Input:
The endpoint ARN of the Amazon Comprehend custom classifier, the name of an existing Amazon S3 bucket you have access to, and one of the following:
- Amazon S3 URI of the multi-page PDF document that needs to be split
- local multi-page PDF file that needs to be split

#### Output:
The Amazon S3 URI of a ZIP file containing multi-class PDFs, each titled with their class name, containing the pages from the input PDF that belong to the same class.

#### Usage:
You must have Docker installed, configured and running. You must also have the AWS CLI and AWS SAM CLI installed and configured with your AWS credentials.
Navigate to the workflow2_docsplitter/sam-app directory. 
Run 'sam build' and 'sam deploy --guided' in your CLI and provide the Stack Name and AWS Region (ensure that this is the same region as your Amazon S3 bucket). You must respond with "y" for the "Allow SAM CLI IAM role creation" and "Create managed ECR repositories for all functions?" prompts. 
This will deploy CloudFormation stacks that create the infrastructure for the Application Load Balancer its Lambda Function Target where you can send document splitting requests.
For example, see below the CLI input:
    
    (venv) Lambda_Topic_Classifier % cd workflow2_docsplitter/sam-app 
    (venv) sam-app % sam build
    Build Succeeded

    (venv) sam-app % sam deploy --guided
    Configuring SAM deploy
    =========================================
    Stack Name [sam-app]: docsplitter
    AWS Region []: us-east-1
    #Shows you resources changes to be deployed and require a 'Y' to initiate deploy
    Confirm changes before deploy [y/N]: n
    #SAM needs permission to be able to create roles to connect to the resources in your template
    Allow SAM CLI IAM role creation [Y/n]: y
    Save arguments to configuration file [Y/n]: n

    Looking for resources needed for deployment:
    Managed S3 bucket: {bucket_name}
    #Managed repositories will be deleted when their functions are removed from the template and deployed
    Create managed ECR repositories for all functions? [Y/n]: y
    
and CLI output:

    CloudFormation outputs from deployed stack
    -------------------------------------------------------------------------------------------------
    Outputs                                                                                         
    -------------------------------------------------------------------------------------------------
    Key                 LoadBalancerDnsName                                                                                         
    Description         DNS Name of the DocSplitter application load balancer with the Lambda target group.                         
    Value               {ALB_DNS}                     
    -------------------------------------------------------------------------------------------------

Send a POST request to the outputted LoadBalancerDnsName, providing your Amazon Comprehend endpoint ARN, Amazon S3 bucket name, and either of the following:
- Amazon S3 URI of the multi-page PDF document that needs to be split
- local multi-page PDF file that needs to be split

See below for the POST request input format.

    # sample_s3_request.py
    dns_name = "{ALB_DNS}"
    bucket_name = "{Bucket_name}"
    endpoint_arn = "{Comprehend ARN}"
    input_pdf_uri = "{document_s3_uri}"

    # sample_local_request.py
    dns_name = "{ALB_DNS}"
    bucket_name = "{Bucket_name}"
    endpoint_arn = "{Comprehend ARN}"
    input_pdf_path = "{local_doc_path}"

The Load Balancer's response is the output ZIP file's Amazon S3 URI as a string in the `output_zip_file_s3_uri` key-pair:

    {
        "output_zip_file_s3_uri": "s3://{file_of_split_docs}.zip"
    }

## Workflow 3: Local Endpoint Builder and Doc Splitter

### Description

Workflow 3 follows a similar purpose to Workflow 1 and Workflow 2 to generate an Amazon Comprehend Endpoint; however, all processing will be done using the user’s local machine to generate an Amazon Comprehend compatible CSV file. 
This workflow was created for customers in highly regulated industries where persisting PDF documents on Amazon S3 may not be possible.

### Local Endpoint Builder

#### Input:
The absolute path of the local **folder** containing the training dataset files (these can be images, single-page PDFs, and/or multi-page PDFs). 
The structure of the folder must be the same as that shown in the "Input" section of "Workflow 1: EndpointBuilder".
The name of an existing Amazon S3 bucket you have access to must also be inputted, as this is where the training dataset CSV file is uploaded and accessed by Amazon Comprehend.

#### Output:
The ARN (Amazon Resource Number) of the model's endpoint, which can be used to classify documents in Workflow 2.

#### Usage:
Navigate to the local_endpointbuilder.py  file in the workflow3_local directory.
Run the file and follow the prompts to input your local dataset folder's absolute path and your Amazon S3 bucket's name.

When the program has finished running, the model's endpoint ARN is printed to the console.
See the final lines in local_endpointbuilder.py:

    print("Welcome to the local endpoint builder!\n")
    existing_bucket_name = input("Please enter the name of an existing S3 bucket you are able to access: ")
    local_dataset_path = input("Please enter the absolute local file path of the dataset folder: ")
    print("\nComprehend model endpoint ARN: " + main(existing_bucket_name, local_dataset_path))

### Local Doc Splitter

#### Input:
The endpoint ARN of the Amazon Comprehend custom classifier and one of the following:
- Amazon S3 URI of the multi-page PDF document that needs to be split
- local multi-page PDF file that needs to be split

#### Output:
A local output folder is created. It contains the multi-class PDFs, each titled with their class name, containing the pages from the input PDF that belong to the same class.

#### Usage:
Navigate to the local_docsplitter.py file in the workflow3_local directory.
Run the file and follow the prompts to input your endpoint ARN and either your input PDF's S3 URI or absolute local path.

When the program has finished running, the console displays the path of the output folder containing the multi-class PDFs.
See the final lines in local_docsplitter.py:

    print("Welcome to the local document splitter!")
    endpoint_arn = input("Please enter the ARN of the Comprehend classification endpoint: ")
    
    print("Would you like to split a local file or a file stored in S3?")
    choice = input("Please enter 'local' or 's3': ")
    if choice == 'local':
        input_pdf_info = input("Please enter the absolute local file path of the input PDF: ")
    elif choice == 's3':
        input_pdf_info = input("Please enter the S3 URI of the input PDF: ")
    
    main(endpoint_arn, choice, input_pdf_info)

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

