import os
import logging
import csv
import json
import yaml
import boto3
import re
import gzip
import io
from datetime import datetime

REGION = os.environ.get('AWS_REGION', 'us-west-2')
CUR_BUCKET_NAME = os.environ.get('CUR_BUCKET_NAME', 'cs-aws-msp-funding-data')
S3_CLIENT = boto3.client('s3', region_name=REGION)

def decompress_gzip_content(gzipped_content):
    if gzipped_content is None:
        return None
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(gzipped_content), mode='rb') as f:
            decompressed_content = f.read().decode('utf-8')  # Assuming UTF-8 encoding
            return decompressed_content
    except Exception as e:
        print(f"Error decompressing GZIP content: {e}")
        return None

def process_cur_file(s3_key):
    gzipped_data = S3_CLIENT.get_object(Bucket=CUR_BUCKET_NAME, Key=s3_key)['Body'].read()
    services = []
    if gzipped_data:
        decompressed_text = decompress_gzip_content(gzipped_data)
        if decompressed_text:
            reader = csv.DictReader(decompressed_text.splitlines())
            for row in reader:
                services.append(row['product_servicecode'])
    return list(set(services))

def classify_services(services, map):
    service_map = {}
    account_services =  {}
    for category in map.keys():
        print(category)
        account_services[category] = 0
        for service in map[category]:
            service_map[service] = category
    for acct_service in services:
        if acct_service in service_map:
            account_services[service_map[acct_service]] += 1
    return account_services
    
def lambda_handler(event, context):
    with open('service_map.yml', 'r') as f:
        service_map = yaml.safe_load(f)
    today = datetime.now()
    cur_date_str = today.strftime("%Y-%m")
    print(cur_date_str)
    client_cur = S3_CLIENT.list_objects_v2(Bucket=CUR_BUCKET_NAME, Prefix='msp-service-data/')
    msp_data = {}
    pattern = r'msp-service-data\/(\w+)\/(\w+)\/(\d+)\/data\/BILLING_PERIOD\=' + cur_date_str
    for obj in client_cur['Contents']:
        print(obj)
        m = re.search(pattern, obj['Key'])
        if m:
            if m.group(1) not in msp_data:
                msp_data[m.group(1)] = {}
            services = process_cur_file(obj['Key'])
            account_status = classify_services(services, service_map)
            try:
                msp_data[m.group(1)][m.group(2)][m.group(3)] = account_status
            except KeyError:
                msp_data[m.group(1)][m.group(2)] = {}
                msp_data[m.group(1)][m.group(2)][m.group(3)] = account_status
    print(msp_data)
    S3_CLIENT.put_object(Bucket=CUR_BUCKET_NAME, Key=f'reports/{cur_date_str}.json', Body=json.dumps(msp_data))
    return {
        'statusCode': 200,
        'body': json.dumps(msp_data)
    }

if __name__ == "__main__":
    with open('event.json', 'r') as f:
            event = json.load(f)
    lambda_handler(event, None)
