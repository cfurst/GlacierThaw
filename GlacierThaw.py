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
    

    
def makeGlacierRequest(awsObject, source_bucket, tier=DEFAULT_TIER, numberOfDaysAvailable=DEFAULT_NUMBER_OF_DAYS_AVAILABLE, destinationBucket='', destinationPrefix=''):
    try: 
        restore_request = {
            'GlacierJobParameters': {
                "Tier": tier
            },
            'Days': numberOfDaysAvailable,
        }
        s3.restore_object(Bucket=source_bucket, Key=awsObject['Key'], RestoreRequest=restore_request)
    except s3.exceptions.ObjectAlreadyInActiveTierError as e:
        print("Couldn't restore:", awsObject['Key'], " possibly already restored...")
    
def main():
    try:
        bucket = sys.argv[1].strip()
        key = None
        if len(sys.argv) >= 3:
            key = sys.argv[2].strip()
        print("bucket: ", bucket, "key: ", key)
        if not key:
            key = ''
        object_iter = paginator.paginate(Bucket=bucket, Prefix=key)
    
        for page in object_iter:
            for awsObject in page['Contents']:
                if awsObject['StorageClass'] == 'GLACIER':
                  makeGlacierRequest(awsObject, bucket)
                  print(awsObject['Key'], " will be restored for 14 days.")
    except IndexError:
        print('Invalid Arguments! I need a bucket at least')
    except KeyError:
        print('prefix: {} did not return any objects.'.format(key))
    
if __name__ == '__main__':
    main()