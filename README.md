# GlacierThaw
A way to recursively request S3 objects to be transfered out of the Glacier storage tier.

## Warning: AWS S3 and Glacier cost $$ to use. We are not responsible for any charges you incur through use of this software!
By downloading and using this software you hereby indemnify the author and all contributors from any and all responsibilities and liabilities regarding costs, and fees associated with the use of any AWS services. It's your account, you pay for it. So use it wisely and carefully.

Any changes to this software under the MIT License terms does not terminate the License terms nor the indemnity heretofore described. 

## Installation:

This project is not yet released so you basically clone it and then use `pip` to install `boto3`, the AWS sdk for python.

```bash
$ git clone https://github.com/cfurst/GlacierThaw.git
$ pip install boto3
```

## Synopsis:
```python
python GlacierThaw.py [-h] --bucket BUCKET [--prefix PREFIX] [--request-tier {Bulk,Standard,Expedited}]
                      [--duration DURATION] [--queue-name QUEUE_NAME]
```
Will create a bulk request to move all objects in `BUCKET` with `PREFIX` from the glacier storage tier to standard tier temporarily for `DURATION` number of days, defaults to 14.

If you leave out the `PREFIX` option, it will make a request for all objects in the bucket. Please use carefully.

If you wish to just make a request for one file you can specify the prefix as the file name. In this case, since its only one file you might want to expedite the request:

```bash
$ python GlacierThaw.py --bucket bucket_name --prefix path/to/file.txt --request-tier Expedite
```
Please review the AWS S3 documentation for more information about the limitations and capabilities of expedited requests.

**Options**
```
 -h, --help            show this help message and exit
  --bucket BUCKET       The name of the s3 bucket that is to be the root of your request. Ex. if your files live at
                        s3://my-awesome-bucket/foo/bar the bucket name would be 'my-awsome-bucket'
  --prefix PREFIX       A prefix or key to use as the base URL for your request. Ex. if your files live in the
                        'foo/bar' directory, then 'foo/bar' is the prefix. If you want to just request one file to be
                        moved, use the path of the file as the prefix Ex. foo/bar/myFile.txt. If you leave out a
                        prefix, you will make a request for the entire bucket. Please be careful. Ctrl-C is your
                        friend.
  --request-tier {Bulk,Standard,Expedited}
                        The type of glacier request you would like to make, Choices are 'Standard', 'Expedited' and
                        'Bulk' (default). Each has purposes and limitations, please consult the AWS documentation for
                        more information
  --duration DURATION   The number of days you wish to have the object available before being returned to Glacier
                        storage; defaults to two weeks.
  --queue-name QUEUE_NAME
                        The name of the queue you have set up to receive restore notifications. Only one message per
                        request will be displayed. It is recommended to just use the Object Restore notification. If
                        you configure your bucket to send 'Restore initiated' and 'Restore complete' messages, you
                        might not get both read for every object
```

## Retreiving files from s3

**From the console:**

Once the transfer request has been expedited, your files will be ready to view. The timing as to when the request completes depends on what type of request you make using the `--request-tier` option (default is `Bulk`). You can find out more about the type of Glacier restore requests and their timing [here](https://docs.aws.amazon.com/AmazonS3/latest/dev/restoring-objects.html#restoring-objects-retrieval-options).

If you go to the console and select a file that was transfered from the Glacier tier, you will see that you can now open the file and download it. You should see a `Restore Expiration` date and time when viewing the file's details. You will be able to download the file until that date, after which the file will be returned to the Glacier storage tier.

**AWS CLI**

If you would like to recursively download your files that you've just moved out of Glacier you can try the following command:

```bash
$ aws cli s3 cp --recursive --force-glacier-transfer s3://bucket-name/prefix/name .
```

You will need the `--force-glacier-transfer` option because of an issue with the s3 api as documented [here](https://github.com/aws/aws-cli/issues/5268)

**Restoring an object to the standard storage tier**

If you want to move an object out of Glacier and back into the standard tier (or any other storage tier, really) you can review [this blog post](https://aws.amazon.com/premiumsupport/knowledge-center/restore-s3-object-glacier-storage-class/) for more information. You basically have to use a method of s3 copying to basically copy the file in place. Via the api, you can use Meta-data to set the storage tier, see the AWS S3 documentation for more information.