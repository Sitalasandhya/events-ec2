**Project Title**

Serverless AWS EC2 Actions API using Lambda



**Contents**



* Project Overview
* Architectural Components
* Architectural Diagram
* Prerequisites
* Manual Setup Instruction
* Automation setup Instruction
* Testing Instruction



**Project Overview**

* This project implements a RESTful API using AWS Lambda to manage AWS EC2 instances, enabling users to perform operations such as create, start, stop and terminate instances.
* The API is exposed via AWS API Gateway, which serves as the entry point for all client requests. While creating an EC2 instance, it also returns all the information needed to connect to the instance via SSH.


Authentication & Authorization:

* Internal Users - Authenticated using IAM-based authorization, ensuring secure access through AWS identity policies.
* External Users - Authenticated using Lambda Authorizer, which validates custom tokens or credentials before granting access.

This architecture enables a scalable, secure and serverless approach to manage EC2 instances, leveraging AWS native services.


**Architectural Components**



These are the components and their purpose mentioned below used in the project.
* IAM Role: Grants Lambda permission to manage EC2
* Lambda function: Handles logic to manage EC2 instance and returns all the details to connect via ssh
* S3: Provides presigned url for the users to download the PEM file to connect to ec2 instance 
* API Gateway: Exposes REST API endpoints for users to call
* Lambda Authorizer: Handles logic for custom authentication






**Architectural Diagram**



Please refer the path - `docs/architectural_diagram_aws.png` to view the overall architecural diagram for this project.



**Prerequisites**

* AWS account
* Python code editor installed in system



**Manual Setup Instruction**



Clone the Repository

- git clone git@github.com:Sitalasandhya/events-ec2.git
- cd events-ec2


AWS account setup

* IAM Role and policy: 

create an IAM policy with the below permissions.

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:TerminateInstances",
                "ec2:StartInstances",
                "ec2:RunInstances",
                "ec2:StopInstances",
                "ec2:DescribeInstanceStatus",
                "ssm:GetParameter",
                "ec2:CreateKeyPair",
                "ec2:DescribeKeyPairs",
                "s3:PutObject",
                "s3:GetObject"
            ],
            "Resource": "*"
        }
    ]
}

create an IAM role and attach the above policy and AWSLambdaBasicExecutionRole to it.


* Lambda function: 

create an AWS Lambda function with Python 3.13 runtime.

Attach the IAM role created in the permissions section.

In the environment variables section of the lambda function, put all the environment variables. The details are present in the .env file.

Please refer the lambda_function.py to get the detailed code.


* S3:

create an S3 bucket with default configuration. Whenever an user access the API endpoint for creating an ec2 instance, a dynamic ec2 key pair will be generated and the pem file will be stored in the S3 bucket. 

The lambda function handles the logic to generate a presigned url and the api response provides the presigned url (valid for 1 hour) and users can download the respective pem file and connect to ec2 instances.
 

* API Gateway: 

Create an Restful API, which should have 2 resources. Make sure to enable 'Proxy integration' while creating the api endpoints.

1. For internal users - The resource path is /actions and create a 'POST' method. The Authorization in the method request settings should be chosen as 'AWS_IAM' and deploy the api properly.

2. For external users - The resource path is /events and create a 'POST' method.

Create an Authorizer with Authorizer type as 'Lambda' and it should have 'Token-source' as 'auth-token'.

The Authorization in the method request settings should be chosen as 'aws-lambda-name' and deploy the api properly.


* Lambda Authorizer: 

Create a lambda function with similar role attached.

Please refer lambda_authorizer.py to get the details.

After any successful operation, we can see the ec2 instance actions in the EC2 Manageent console.



**Automation Setup Instruction**

The complete project setup can be done using Terraform autiomation script.

Before proceeding, please clone the Repository.

- git clone git@github.com:Sitalasandhya/events-ec2.git
- cd events-ec2

Steps to execute the Terraform code:

1. Install Terraform in your system using the below url -

               https://developer.hashicorp.com/terraform/install

2. Once installed, please open your cmd and run the below command to check whether it is installed properly or not.

               terraform --version

3. Update your system environment variables to include the terraform path.
4. Create a directory for terraform and keep these below files.
       1. main.tf
       2. provider.tf
       3. var.tf
       4. lambda_function_payload.zip
5. Open gitbash or cmd and navigate to your terraform directory.
6. Configure AWS CLI using aws configure or the the credentials can be exported like below.

           export AWS_ACCESS_KEY_ID = your_key
           export AWS_SECRET_ACCESS_KEY = your_secret
           export AWS_DEFAULT_REGION = us-east-1 # provide the region name where you want the setup and mention the same region name in the var.tf file.
7. Initialize the terraform script using the below command.

           terraform init

8. Preview the changes using the below Terraform command.

           terraform plan

9. Apply the changes using the below Terraform command.

            terraform apply

Once this command is run, it will be prompted to confirm about the changes. Once confirmed, This provisions the infrastructure on AWS.

10. Please refer Terraform documentation for any queries regarding this.




**Testing Instruction**

For testing the api endpoints, we can follow the below steps.

1. Manual Testing: It can be done using API Platform like Postman.

2. Automation Testing: This can be done using any Python code editor.

In the code editor, please follow the below steps.

* Clone the repository and open the folder. Make sure you have python installed in your machine.

* Create a virtual environment in the terminal using below command.

    python -m venv .venv

* Activate the virtual environment using the below command.

    .\.venv\Scripts\Activate.ps1

* Install the below packages present in the requirements.txt.

    pip install -r requirements.txt

* The different testcase scenarios are validated using the test_api_authorizer_based.py and test_api_iam_based.py.

Please refer Testcases_aws_ec2_actions_api.docx to check different testcases for this project.


NOTE - Please update the api endpoints in the python testing files if the project setup is done using Terraform code.


