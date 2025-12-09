# AWS MSP Funding Stack Clearscale POC

This project implements a Proof of Concept (POC) for an AWS Managed Service Provider (MSP) funding stack. It automates the processing of usage data from AWS Cost and Usage Reports (CUR) to categorize AWS services used by accounts, aiding in MSP funding calculations for AWS categorized by MSP, Client, and Account in the following format

```
{
    "Clearscale": {
        "ExampleCustomer": {
            "921888033920": {"advanced": 1, "basic": 6, "medium": 1}
            "921888033921": {"advanced": 2, "basic": 12, "medium": 5}
        },
        "Customer2": {
            "511888033920": {"advanced": 1, "basic": 6, "medium": 1}
            "761888033921": {"advanced": 2, "basic": 12, "medium": 5}
        }
    },
     "MSP2": {
        "ExampleCustomer": {
            "20188033920": {"advanced": 1, "basic": 6, "medium": 1}
            "021888033921": {"advanced": 2, "basic": 12, "medium": 5}
        },
        "Customer2": {
            "1051888033920": {"advanced": 1, "basic": 6, "medium": 1}
            "0761888033921": {"advanced": 2, "basic": 12, "medium": 5}
        }
    }
}
```

## AWS Architecture

The AWS-side of the POC consists of the following AWS resources:

*   **S3 Bucket (`cs-aws-msp-funding-data`)**: Stores the raw CUR data and the generated JSON reports.
*   **Lambda Function (`aws-msp-cur-parser`)**: A Python 3.13 function that:
    *   Reads CUR files from the S3 bucket.
    *   Decompresses and parses the CSV data.
    *   Classifies services based on a configurable `service_map.yml`.
    *   Aggregates service usage by account and category.
    *   Generates a JSON report and saves it back to S3.
*   **EventBridge Scheduler (`MonthlyCURInvocationRule`)**: Triggers the Lambda function on a scheduled basis (currently set to every 10 minutes for testing purposes, intended for monthly execution).

## Client Account Architecture

The client-side of the POC consists of the following AWS resources:
*   **CUR 2.0 Data Export**: A Cost and Usage Report (CUR) report definition that exports data to an S3 bucket in the AWS-side of the Architecture.

## Exported Data

In each client account (as of this POC), or implemented at an Organization CUR level, Only the `product_servicecode` field is exported. This is a string that contains the service code for the AWS service used such as:

```
AWSELB
AWSCloudTrail
AmazonS3
AmazonCloudWatch
AmazonVPC
AmazonEC2
AmazonECS
AmazonEKS
AWSLambda
AWSBedrock
```

The data is currently exported to an S3 bucket in the AWS-side of the Architecture that may only be written to by the data export services. 

## Prerequisites

*   AWS CLI installed and configured.
*   Python 3.13 installed.
*   `zip` utility for packaging the Lambda function.

## Project Structure

```
.
├── aws-msp-funding-stack
│   ├── aws-cur-parser-lambda
│   │   ├── lambda_function.py  # Main Lambda logic
│   │   ├── service_map.yml     # Service classification configuration
│   │   ├── requirements.txt    # Python dependencies
│   │   ├── event.json          # Test event for local execution
│   ├── stack.yaml              # CloudFormation template for S3 bucket for CUR data and reports
│   ├── lambda.yaml             # CloudFormation template for Lambda & Scheduler
│   └── deploy.sh               # Deployment script
└── client-onboarding-single-account
│   ├── stack.yaml              # CloudFormation template for S3 bucket for CUR data and reports
│   ├── lambda.yaml             # CloudFormation template for Lambda & Scheduler
│   └── deploy.sh               # Deployment script for client account
```

## Configuration

### Service Map (`service_map.yml`)

The `service_map.yml` file defines how AWS services are categorized. You can modify this file to adjust the classification logic.

Example:
```yaml
basic:
  - AmazonS3
  - AmazonEC2
medium:
  - AmazonECS
advanced:
  - AmazonEKS
  - AWSLambda
```

## Deployment

The project includes a `deploy.sh` script in `aws-msp-funding-stack/` to facilitate deployment.

1.  **Navigate to the stack directory:**
    ```bash
    cd aws-msp-funding-stack
    ```

2.  **Run the deployment script:**
    ```bash
    ./deploy.sh
    ```

    **Note:** You might need to uncomment lines in `deploy.sh` to perform the full build and deploy process, which typically involves:
    1.  Installing dependencies to a `package` directory.
    2.  Zipping the package and function code.
    3.  Uploading the zip to S3.
    4.  Deploying the CloudFormation stack.

    Currently, the active line in `deploy.sh` only deploys the `lambda.yaml` stack:
    ```bash
    aws cloudformation deploy --stack-name cs-aws-msp-lambda-cur-poc --template-file lambda.yaml --capabilities CAPABILITY_IAM
    ```

## Usage

Once deployed, the system runs automatically based on the EventBridge Schedule, with a monthyl-named report put in the S3 bucket under the `reports/` prefix.


### Output

The Lambda function generates a JSON report stored in the S3 bucket under the `reports/` prefix:
`s3://cs-aws-msp-funding-data/reports/YYYY-MM.json`

The JSON structure aggregates service counts per account and category:

```json
{
  "account_id": {
    "bill_payer_account_id": {
      "billing_period": {
        "basic": 5,
        "medium": 2,
        "advanced": 1
      }
    }
  }
}
```
