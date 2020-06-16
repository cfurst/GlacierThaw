# GlacierThaw
A way to recursively request S3 objects to be transfered out of the Glacier storage tier.

## Warning: AWS S3 and Glacier cost $$ to use. We are not responsible for any charges you incur through use of this software!
By downloading and using this software you hereby indemnify the author and all contributors from any and all responsibilities and liabilities regarding costs, and fees associated with the use of any AWS services. It's your account, you pay for it. So use it wisely and carefully.

Any changes to this software under the MIT License terms does not terminate the License terms nor the indemnity heretofore described. 

## Synopsis:
```python
python GlacierThaw <Bucket> [Prefix or key]
```
will create a bulk request to move all objects in `Bucket` with `Prefix` or file with name `key` from the glacier storage tier temporarily for 14 days.

If you leave out a prefix or key, it will make a request for all objects in the bucket. Please use carefully.