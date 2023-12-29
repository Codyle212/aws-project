import boto3

'''
Create an S3 Bucket
'''
client = boto3.client('s3')
response = client.create_bucket(
    Bucket='demo-bucket-codyle212',
    # ACL='private'|'public-read'|'public-read-write'|'authenticated-read',
    # CreateBucketConfiguration={
    #     'LocationConstraint': 'af-south-1'|'ap-east-1'|'ap-northeast-1'|'ap-northeast-2'|'ap-northeast-3'|'ap-south-1'|'ap-south-2'|'ap-southeast-1'|'ap-southeast-2'|'ap-southeast-3'|'ca-central-1'|'cn-north-1'|'cn-northwest-1'|'EU'|'eu-central-1'|'eu-north-1'|'eu-south-1'|'eu-south-2'|'eu-west-1'|'eu-west-2'|'eu-west-3'|'me-south-1'|'sa-east-1'|'us-east-2'|'us-gov-east-1'|'us-gov-west-1'|'us-west-1'|'us-west-2',
    #     'Location': {
    #         'Type': 'AvailabilityZone',
    #         'Name': 'string'
    #     },
    #     'Bucket': {
    #         'DataRedundancy': 'SingleAvailabilityZone',
    #         'Type': 'Directory'
    #     }
    # },
    # GrantFullControl='string',
    # GrantRead='string',
    # GrantReadACP='string',
    # GrantWrite='string',
    # GrantWriteACP='string',
    # ObjectLockEnabledForBucket=True|False,
    # ObjectOwnership='BucketOwnerPreferred'|'ObjectWriter'|'BucketOwnerEnforced'
)

'''
Get S3 Bucket ACL
Sample Response:
    {
        'Owner': {
            'DisplayName': 'string',
            'ID': 'string'
        },
        'Grants': [
            {
                'Grantee': {
                    'DisplayName': 'string',
                    'EmailAddress': 'string',
                    'ID': 'string',
                    'Type': 'CanonicalUser'|'AmazonCustomerByEmail'|'Group',
                    'URI': 'string'
                },
                'Permission': 'FULL_CONTROL'|'WRITE'|'WRITE_ACP'|'READ'|'READ_ACP'
            },
        ]
    }
'''
client = boto3.client('s3')
response = client.get_bucket_acl(
    Bucket='demo-bucket-codyle212',
    ExpectedBucketOwner='string'
)

'''
