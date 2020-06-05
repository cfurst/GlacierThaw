import sys

import boto3

s3 = boto3.client('s3')
DEFAULT_NUMBER_OF_DAYS_AVAILABLE = 14
DEFAULT_TIER = 'Bulk'
paginator = s3.get_paginator('list_objects_v2')

def getMetadata(bucket, key):
    """
    returns true when there is metadata available for the object
    """
    try:
        metadata = s3.head_object(Bucket=bucket, Key=key)
    except:
        print('error encountered getting {key} from {bucket}: {error}'.format(key=key, bucket=bucket, error=sys.exc_info()))
        return None
    return metadata
    

    
def makeGlacierRequest(awsObject, sourceBucket, tier=DEFAULT_TIER, numberOfDaysAvailable=DEFAULT_NUMBER_OF_DAYS_AVAILABLE, destinationBucket='', destinationPrefix=''):
    try: 
        restore_request = {
            'GlacierJobParameters': {
                "Tier": tier
            },
            'Days': numberOfDaysAvailable,
        }
        s3.restore_object(Bucket=bucket, Key=awsObject['Key'], RestoreRequest=restore_request)
    except s3.exceptions.ObjectAlreadyInActiveTierError as e:
        print("Couldn't restore:", awsObject['Key'], e)
    
def main():
    try:
        bucket = sys.argv[1]
        key = None
        if len(sys.argv) >= 3:
            key = sys.argv[2]
        print("bucket: ", bucket, "key: ", key)
        if not key:
            key = ''
        paginator.paginate(Bucket=bucket, Prefix=key)
        for page in paginator:
            for awsObject in page['Contents']:
                if awsObject['StorageClass'] == 'GLACIER':
                    makeGlacierRequest(awsObject, bucket)
    except IndexError:
        print('Invalid Arguments! I need a bucket at least')

if __name__ == '__main__':
    main()