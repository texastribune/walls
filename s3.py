from datetime import datetime, timedelta
import gzip
from io import BytesIO
import boto3

from config import HOURS_TO_EXPIRE, BUCKET


def push_to_s3(filename=None, contents=None):
    """
    Save a file to the the configured bucket with name and contents
    specified in the call.

    It compresses the data.

    This sets the contents to be publicly readable, cacheable by
    intermediaries with an expiration date a specified number
    of hours from when this job is run. (See above.)
    """
    contents = bytes(contents, "utf-8")
    out = BytesIO()
    with gzip.GzipFile(fileobj=out, mode="w") as f:
        f.write(contents)
    out.seek(0)

    expires = datetime.utcnow() + timedelta(hours=HOURS_TO_EXPIRE)
    expires = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")

    s3 = boto3.client("s3")
    s3.upload_fileobj(
        out,
        BUCKET,
        filename,
        ExtraArgs={
            "ContentType": "application/json",
            "ACL": "public-read",
            "CacheControl": "public",
            "Expires": expires,
            "ContentEncoding": "gzip",
        },
    )
