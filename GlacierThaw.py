import boto3
import sys


s3 = boto3.client('s3')
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

def getObjectList(bucket, key, continuationToken = None):
    """
    will return the first level of stuff in the key
    """
    if not bucket and key:
        return {}
    else:
        if not continuationToken:
            return s3.list_objects_v2(Bucket=bucket, Prefix=key)
        return s3.list_objects_v2(Bucket=bucket, Prefix=key, ContinuationToken=continuationToken)
try:
    bucket = sys.argv[1]
    key = None
    if len(sys.argv) >= 3:
        key = sys.argv[2]
    print("bucket: {bucket}, key: {key}".format(bucket=bucket, key=key))
    print(getObjectList(bucket, key));
       
    

except IndexError:
    print('Invalid Arguments! I need a bucket at least')



