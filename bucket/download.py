from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import io
import json
import shutil
import argparse

import ibm_boto3
from botocore.client import Config
from dotenv import load_dotenv
load_dotenv('.credentials')

from bucket import prepare_data

parser = argparse.ArgumentParser()
parser.add_argument('--bucket', type=str)
parser.add_argument('--endpoint', type=str, default='https://s3-api.us-geo.objectstorage.softlayer.net')
args = parser.parse_args()


################################################################################
# Credentials
################################################################################
credentials_1 = {
  'bucket': args.bucket,
  'iam_url': 'https://iam.ng.bluemix.net/oidc/token',
  'api_key': os.getenv('0KqEjmyWRAs8P0Zl0_QYEYXHZyav7ikVaE5ODLLL3_ZY'),
  'resource_instance_id': os.getenv('crn:v1:bluemix:public:cloud-object-storage:global:a/3386c4d9560f406c8901e67f0c0cfe06:f7e29f38-761c-4dc5-aeb2-83c1084f4715::'),
  'url': args.endpoint
}


################################################################################
# Initialize Cloud Object Storage
################################################################################
cos = ibm_boto3.resource('s3',
    ibm_api_key_id=credentials_1['0KqEjmyWRAs8P0Zl0_QYEYXHZyav7ikVaE5ODLLL3_ZY'],
    ibm_service_instance_id=credentials_1['crn:v1:bluemix:public:cloud-object-storage:global:a/3386c4d9560f406c8901e67f0c0cfe06:f7e29f38-761c-4dc5-aeb2-83c1084f4715::'],
    ibm_auth_endpoint=credentials_1['iam_url'],
    config=Config(signature_version='oauth'),
    endpoint_url=credentials_1['url']
)


################################################################################
# Choose Bucket
################################################################################
def askForBucket():
    bucket_list = []
    for i, bucket in enumerate(cos.buckets.all()):
        bucket_list.append(bucket.name)
        print('  {}) {}'.format(i + 1, bucket.name))

    bucket_id_name = input("Bucket: objects-detection")

    if bucket_id_name in bucket_list:
        credentials_1['objects-detection'] = bucket_id_name
    else:
        try:
           bucket_id_name = int(bucket_id_name)
           if bucket_id_name <= len(bucket_list):
               credentials_1['objects-detection'] = bucket_list[bucket_id_name - 1]
           else:
               print('\nPlease choose a valid bucket:objects-detection')
               askForBucket()
        except ValueError:
            print('\nPlease choose a valid bucket:objects-detection')
            askForBucket()

if credentials_1['bucket'] == None:
    print('\nPlease choose a bucket:objects-detection')
    askForBucket()


################################################################################
# Prepare Output Directories
################################################################################
output_dir = '.tmp'
if os.path.exists(output_dir) and os.path.isdir(output_dir):
    shutil.rmtree(output_dir)
os.makedirs(output_dir)


################################################################################
# Download Data
################################################################################
annotations = cos.Object(credentials_1['bucket'], '_annotations.json').get()['Body'].read()
annotations = json.loads(annotations.decode('utf-8'))['annotations']

cos.Object(credentials_1['bucket'], '_annotations.json').download_file(os.path.join(output_dir, '_annotations.json'))

# Download training images.
image_files = [image for image in annotations.keys()]
for file in image_files:
    filename = os.path.join(output_dir, file)
    print('saving: {}'.format(file))
    print('to: {}'.format(filename))
    cos.Object(credentials_1['bucket'], file).download_file(filename)

prepare_data.main(output_dir, output_dir)
