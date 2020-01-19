import boto3
import sys

def doesExist(bucket, key):
    """
    returns true when there is metadata available for the object
    """
    s3 = boto3.client('s3')
    try:
        metadata = s3.head_object(Bucket=bucket, Key=key)
    except:
        print('error encountered getting {key} from {bucket}: {error}'.format(key=key, bucket=bucket, error=sys.exc_info()))
        return False
    return True

bucket = sys.argv[1]
key = sys.argv[2]
print("bucket: {bucket}, key: {key}".format(bucket=bucket, key=key))
exists = doesExist(bucket, key)

if exists:
    print ("Yes {key} exists in {bucket}".format(key=key, bucket=bucket))
else:
    print ("I guess {key} doesn't exist in {bucket}".format(key=key, bucket=bucket))

