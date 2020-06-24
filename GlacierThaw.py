#!
import boto3
import argparse
from symbol import argument
import botocore



argument_parser = argparse.ArgumentParser()
argument_parser.add_argument("bucket", help="The name of the s3 bucket that is to be the root of your request. Ex. if your files live at s3://my-awesome-bucket/foo/bar the bucket name would be 'my-awsome-bucket'")
argument_parser.add_argument("--prefix", help="A prefix or key to use as the base URL for your request. Ex. if your files live in the 'foo/bar' directory, then 'foo/bar' is the prefix. If you want to just request one file to be moved, use the path of the file as the prefix Ex. foo/bar/myFile.txt. If you leave out a prefix, you will make a request for the entire bucket. Please be careful. Ctrl-C is your friend.", default='')
argument_parser.add_argument("--request-tier", help="The type of glacier request you would like to make, Choices are 'Standard', 'Expedited' and 'Bulk' (default). Each has purposes and limitations, please consult the AWS documentation for more information", dest="tier", choices=['Bulk','Standard','Expedited'], default='Bulk')
argument_parser.add_argument("--duration", help="The number of days you wish to have the object available before being returned to Glacier storage; defaults to two weeks.", type=int, default=14)

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
    

    
def makeGlacierRequest(aws_object, source_bucket, tier=DEFAULT_TIER, number_of_days_available=DEFAULT_NUMBER_OF_DAYS_AVAILABLE):
    """
    Creates a glacier request for a default period of 14 days
    """
    # TODO: implement destination bucket and prefix.
    try: 
        restore_request = {
            'GlacierJobParameters': {
                "Tier": tier
            },
            'Days': number_of_days_available,
        }
        # TODO: Specify a queue to read restore notifications from. 
        s3.restore_object(Bucket=source_bucket, Key=aws_object['Key'], RestoreRequest=restore_request)
    except (s3.exceptions.ObjectAlreadyInActiveTierError, botocore.exceptions.ClientError) as e:
        print("Couldn't restore:", aws_object['Key'], " possibly already restored...", e)
    else:
        print(aws_object['Key'], " will be restored for {} days.".format(number_of_days_available))
    
def main():
    try:
        input_args = argument_parser.parse_args()
        bucket = input_args.bucket
        key = input_args.prefix
        kwargs = {
            "tier": input_args.tier,
            "number_of_days_available": input_args.duration
        }
        
        print("bucket: ", bucket, "key: ", key)
        
        object_iter = paginator.paginate(Bucket=bucket, Prefix=key)
    
        for page in object_iter:
            for awsObject in page['Contents']:
                if awsObject['StorageClass'] == 'GLACIER':
                  makeGlacierRequest(awsObject, bucket, **kwargs)
                  
    except KeyError:
        print('prefix: {} did not return any objects.'.format(key))
    
if __name__ == '__main__':
    main()