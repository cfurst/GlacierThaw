import sys

import boto3

s3 = boto3.client('s3')
DEFAULT_NUMBER_OF_DAYS_AVAILABLE = 14
DEFAULT_TIER = 'Bulk'


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


def getObjectList(bucket, key, continuationToken=None):
    """
    will return the list of stuff given the prefix of key
    """
    if not continuationToken:
            return s3.list_objects_v2(Bucket=bucket, Prefix=key)
    return s3.list_objects_v2(Bucket=bucket, Prefix=key, ContinuationToken=continuationToken)

    
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
    

try:
    bucket = sys.argv[1]
    key = None
    if len(sys.argv) >= 3:
        key = sys.argv[2]
    print("bucket: ", bucket, "key: ", key)
    if not key:
        key = ''
    objectList = getObjectList(bucket, key)
    for awsObject in objectList['Contents']:
        if awsObject['StorageClass'] == 'GLACIER':
            makeGlacierRequest(awsObject, bucket)
except IndexError:
    print('Invalid Arguments! I need a bucket at least')

