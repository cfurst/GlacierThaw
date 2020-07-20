#!
import boto3
import argparse
import json
import botocore
import traceback



argument_parser = argparse.ArgumentParser()
argument_parser.add_argument("--bucket", help="The name of the s3 bucket that is to be the root of your request. Ex. if your files live at s3://my-awesome-bucket/foo/bar the bucket name would be 'my-awsome-bucket'", required=True, type=str)
argument_parser.add_argument("--prefix", help="A prefix or key to use as the base URL for your request. Ex. if your files live in the 'foo/bar' directory, then 'foo/bar' is the prefix. If you want to just request one file to be moved, use the path of the file as the prefix Ex. foo/bar/myFile.txt. If you leave out a prefix, you will make a request for the entire bucket. Please be careful. Ctrl-C is your friend.", default='')
argument_parser.add_argument("--request-tier", help="The type of glacier request you would like to make, Choices are 'Standard', 'Expedited' and 'Bulk' (default). Each has purposes and limitations, please consult the AWS documentation for more information", dest="tier", choices=['Bulk','Standard','Expedited'], default='Bulk')
argument_parser.add_argument("--duration", help="The number of days you wish to have the object available before being returned to Glacier storage; defaults to two weeks.", type=int, default=14)
argument_parser.add_argument("--queue-name", help="The name of the queue you have set up to receive restore notifications. Only one message per request will be displayed. It is recommended to just use the Object Restore notification. If you configure your bucket to send 'Restore initiated' and 'Restore complete' messages, you might not get both read for every object")

s3 = boto3.client('s3')
sqs = boto3.resource('sqs')

DEFAULT_NUMBER_OF_DAYS_AVAILABLE = 14
DEFAULT_TIER = 'Bulk'
paginator = s3.get_paginator('list_objects_v2')

def create_delete_entry_request(message):
    """
    creates an entry for a delete_messages request
    """
    return {
        "Id": message.message_id,
        "ReceiptHandle": message.receipt_handle
        }


def create_message_report(message):
    """
    This creates a message using the notification json about the status of the glacier restore for reporting.
    """
    message_body = json.loads(message.body)
    return f"{message_body['Records'][0]['s3']['object']['key']} has been restored and will be returned to Glacier at {message_body['Records'][0]['glacierEventData']['restoreEventData']['lifecycleRestorationExpiryTime']}"


def read_queue_for_notifications(queue, num_objects_requested):
    """
    This will poll for notifications from queue until it has received  num_objects_requested messages. 
    Since this is mostly asynchronous it is hard to tell if this really will be an accurate method for knowing if 
    we have completed the report. It will be up to the user to make sure that the queue is only receiving messages from the bucket
    where they are making restore requests.
    """
    try:
        queue_message_request = {
            "MaxNumberOfMessages": 10,
            "VisibilityTimeout": 10,
            "WaitTimeSeconds": 20
            }
        
        messages_received = 0
        while messages_received < num_objects_requested:
            messages = queue.receive_messages(**queue_message_request) 
            for message in messages:
                print(create_message_report(message))
                messages_received += 1
                message.delete()
    
    except Exception as e:
        print(f"could not read messages from queue: {e}")
        traceback.print_exc()
    

    
def make_glacier_request(aws_object, source_bucket, tier=DEFAULT_TIER, number_of_days_available=DEFAULT_NUMBER_OF_DAYS_AVAILABLE):
    """
    Creates a glacier request for a default period of 14 days
    """
    # TODO: implement destination bucket and prefix.
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
    
def main():
    try:
        input_args = argument_parser.parse_args()
        bucket = input_args.bucket
        key = input_args.prefix
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
        num_objects_requested = 0
        for page in object_iter:
            for awsObject in page['Contents']:
                if awsObject['StorageClass'] == 'GLACIER':
                  make_glacier_request(awsObject, bucket, **glacier_reqeuest_kwargs)
                  num_objects_requested += 1
                  
        if sqs_queue is not None:
            read_queue_for_notifications(sqs_queue, num_objects_requested)
    except KeyError:
        print(f'prefix: {key} did not return any objects.')
    except botocore.exceptions.ClientError as e:
        print(f"Client error encoutnered: {e}")
        
    
if __name__ == '__main__':
    main()