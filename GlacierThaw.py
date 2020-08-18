#!
import boto3
import argparse
import json
import botocore
import traceback
from concurrent.futures import ThreadPoolExecutor





argument_parser = argparse.ArgumentParser()
argument_parser.add_argument("--bucket", help="The name of the s3 bucket that is to be the root of your request. Ex. if your files live at s3://my-awesome-bucket/foo/bar the bucket name would be 'my-awsome-bucket'", required=True, type=str)
argument_parser.add_argument("--prefix", help="A prefix or key to use as the base URL for your request. Ex. if your files live in the 'foo/bar' directory, then 'foo/bar' is the prefix. If you want to just request one file to be moved, use the path of the file as the prefix Ex. foo/bar/myFile.txt. If you leave out a prefix, you will make a request for the entire bucket. Please be careful. Ctrl-C is your friend.", default='')
argument_parser.add_argument("--request-tier", help="The type of glacier request you would like to make, Choices are 'Standard', 'Expedited' and 'Bulk' (default). Each has purposes and limitations, please consult the AWS documentation for more information", dest="tier", choices=['Bulk','Standard','Expedited'], default='Bulk')
argument_parser.add_argument("--duration", help="The number of days you wish to have the object available before being returned to Glacier storage; defaults to two weeks.", type=int, default=14)
argument_parser.add_argument("--queue-name", help="The name of the queue you have set up to receive restore notifications. Only one message per request will be displayed. It is recommended to just use the Object Restore notification. If you configure your bucket to send 'Restore initiated' and 'Restore complete' messages, you might not get both read for every object")
argument_parser.add_argument("--restore-to-tier", help="Permanently transfer all objects restored to this storage tier. You need to specify a queue name to use this by setting '--queue-name'", choices=['STANDARD', 'REDUCED_REDUNDANCY', 'STANDARD_IA', 'ONEZONE_IA', 'INTELLIGENT_TIERING', 'GLACIER', 'DEEP_ARCHIVE'])
s3 = boto3.client('s3')
sqs = boto3.resource('sqs')

DEFAULT_NUMBER_OF_DAYS_AVAILABLE = 14
DEFAULT_TIER = 'Bulk'
paginator = s3.get_paginator('list_objects_v2')
thread_pool = ThreadPoolExecutor()

def create_delete_entry_request(message):
    """
    creates an entry for a delete_messages request
    """
    return {
        "Id": message.message_id,
        "ReceiptHandle": message.receipt_handle
        }


def create_message_report(message_body):
    """
    This creates a message using the notification json about the status of the glacier restore for reporting.
    """
    
    return f"{message_body['Records'][0]['s3']['object']['key']} has been restored and will be returned to Glacier at {message_body['Records'][0]['glacierEventData']['restoreEventData']['lifecycleRestorationExpiryTime']}"

def copy_action(bucket, key, restore_tier):
    try:
        print(f'copying object with {bucket} and {key}')
        s3_copy_resource = boto3.resource('s3')
        destination_object = s3_copy_resource.Object(bucket,key)
        destination_object.copy({'Bucket':  bucket, 'Key': key}, ExtraArgs={'StorageClass': restore_tier, 'MetadataDirective': 'COPY'})
        print(f"done copying {key}")
    except botocore.exceptions.ClientError as e:
        print(f"Couldn't copy {bucket}/{key} to tier {restore_tier}: {e}")
    except Exception as e:
        print(f"Exception in thread! {e}")
   
    
def read_queue_for_notifications(queue, set_of_files_restored, restore_tier=None):
    """
    This will poll for notifications from queue and process all mesages until the set_of_files_restored set is empty,
    removing each file it finds from the set. If the filename in the message is not in the set, it will not process it.
    """
    try:
        queue_message_request = {
            "MaxNumberOfMessages": 10,
            "VisibilityTimeout": 10,
            "WaitTimeSeconds": 20
            }
        print(f"reading queue: restore tier: {restore_tier}")
        while len(set_of_files_restored) > 0:
            messages = queue.receive_messages(**queue_message_request) 
            for message in messages:
                message_body = json.loads(message.body)
                if message_body['Records'][0]['s3']['object']['key'] in set_of_files_restored:
                    print(create_message_report(message_body))
                    bucket_name = message_body['Records'][0]['s3']['bucket']['name']
                    key_name = message_body['Records'][0]['s3']['object']['key']
                    
                    if restore_tier is not None:
                        message_body = json.loads(message.body)
                        thread_pool.submit(copy_action, bucket_name, key_name, restore_tier)
                    set_of_files_restored.remove(key_name) #  restored and processed..remove from set.
                message.delete()   
    
    except Exception as e:
        print(f"could not read messages from queue: {e}")
        traceback.print_exc()
    

    
def make_glacier_request(aws_object, source_bucket, tier=DEFAULT_TIER, number_of_days_available=DEFAULT_NUMBER_OF_DAYS_AVAILABLE):
    """
    Creates a glacier request for a default period of 14 days
    """
    try: 
        restore_request = {
            'GlacierJobParameters': {
                "Tier": tier
            },
            'Days': number_of_days_available
        }
        # TODO: Specify a queue to read restore notifications from. 
        s3.restore_object(Bucket=source_bucket, Key=aws_object['Key'], RestoreRequest=restore_request)
    except (s3.exceptions.ObjectAlreadyInActiveTierError, botocore.exceptions.ClientError) as e:
        print("Couldn't restore:", aws_object['Key'], " possibly already restored...", e)
    else:
        print(aws_object['Key'], f" will be restored for {number_of_days_available} days.")
        
        
def test_args(input_args):
    """
    checks to make sure that a restore tier request has a queue
    """
    if input_args.restore_to_tier and not input_args.queue_name:
       return (False, "You need to specify a queue name by setting '--queue_name' if you want to restore files to a different tier")
         
    else:
        return (True, "") 
        
    
def main():
    set_of_files_to_restore = set()
    input_args = argument_parser.parse_args()
    (valid_args, bad_args_message) = test_args(input_args)
    if valid_args:
        try:
            bucket = input_args.bucket
            key = input_args.prefix
            restore_tier = input_args.restore_to_tier
            print(f"got restore tier: {restore_tier}")
            queue_name = input_args.queue_name
            glacier_reqeuest_kwargs = {
                "tier": input_args.tier,
                "number_of_days_available": input_args.duration
            }
            sqs_queue = None
            print(f"Initiating restore request for bucket: {bucket} and key: {key}")
            
            #  check for the queue first before initiating requests.
            if input_args.queue_name is not None:
                print(f"trying to fetch url for {input_args.queue_name}")
                sqs_queue = sqs.get_queue_by_name(QueueName = input_args.queue_name)
            
            object_iter = paginator.paginate(Bucket=bucket, Prefix=key)
            
            for page in object_iter:
                for awsObject in page['Contents']:
                    if awsObject['StorageClass'] == 'GLACIER':
                      make_glacier_request(awsObject, bucket, **glacier_reqeuest_kwargs)
                      set_of_files_to_restore.add(awsObject['Key'])
                      
            if sqs_queue is not None:
                read_queue_for_notifications(sqs_queue, set_of_files_to_restore, restore_tier)
            thread_pool.shutdown()
        except KeyError:
            print(f'prefix: {key} did not return any objects.')
        except botocore.exceptions.ClientError as e:
            print(f"Client error encoutnered: {e}")
    else:
        raise Exception(f"Arguments not valid {bad_args_message}")
        
    
if __name__ == '__main__':
    main()