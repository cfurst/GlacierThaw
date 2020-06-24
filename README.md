# GlacierThaw
A way to recursively request S3 objects to be transfered out of the Glacier storage tier.

## Warning: AWS S3 and Glacier cost $$ to use. We are not responsible for any charges you incur through use of this software!
By downloading and using this software you hereby indemnify the author and all contributors from any and all responsibilities and liabilities regarding costs, and fees associated with the use of any AWS services. It's your account, you pay for it. So use it wisely and carefully.

Any changes to this software under the MIT License terms does not terminate the License terms nor the indemnity heretofore described. 

## Synopsis:
```python
python GlacierThaw <Bucket> [Prefix or key]
```
will create a bulk request to move all objects in `Bucket` with `Prefix` or file with name `key` from the glacier storage tier to standard tier temporarily for 14 days.

If you leave out the `prefix or key` option, it will make a request for all objects in the bucket. Please use carefully.

## Retreiving files from s3

**From the console:**

Once the transfer request has been expedited, your files will be ready to view. The timing as to when the request completes depends on what type of request you make (deafult is bulk). You can find out more about the type of Glacier restore requests and their timing [here](https://docs.aws.amazon.com/AmazonS3/latest/dev/restoring-objects.html#restoring-objects-retrieval-options).

If you go to the console and select a file that was transfered from the Glacier teir, you will see that you can now open the file and download it. You should see a `Restore Expiration` date and time when viewing the file's details. You will be able to download the file until that date, after which the file will be returned to the Glacier storage tier.

**AWS CLI**

If you would like to recursively download your files that you've just moved out of Glacier you can try the following command:

```bash
$ aws cli s3 cp --recursive --force-glacier-transfer s3://bucket-name/prefix/name .
```

You will need the `--force-glacier-transfer` option because of an issue with the s3 api as documented [here](https://github.com/aws/aws-cli/issues/5268)

**Restoring an object to the standard storage teir**

If you want to move an object out of Glacier and back into the standard tier (or any other storage tier, really) you can review [this blog post](https://aws.amazon.com/premiumsupport/knowledge-center/restore-s3-object-glacier-storage-class/) for more information. You basically have to use a method of s3 copying to basically copy the file in place.