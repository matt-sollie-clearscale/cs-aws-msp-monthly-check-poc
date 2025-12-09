aws cloudformation deploy --stack-name cs-aws-msp-funding-poc --template-file stack.yaml
cd aws-cur-parser-lambda
mkdir package
pip install -r requirements.txt -t ./package
cd package
zip -r ../../lambda-code.zip .
cd ..
zip ../lambda-code.zip lambda_function.py service_map.yml
cd ..
aws s3 cp lambda-code.zip s3://cs-aws-msp-funding-data/lambda-code.zip
aws cloudformation deploy --stack-name cs-aws-msp-lambda-cur-poc --template-file lambda.yaml --capabilities CAPABILITY_IAM