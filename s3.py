from datetime import datetime, timedelta
import gzip
import StringIO

from boto.s3.connection import S3Connection, OrdinaryCallingFormat
from boto.s3.key import Key

# This value should be set to the frequency that this job is run. Right now I
# believe it will be called every 12 hours. If that changes this should too:
HOURS_TO_EXPIRE = 12


def push_to_s3(filename=None, contents=None):
    """
    Save a file to the the membership bucket with name and contents
    specified in the call.

    It compresses the data.

    This sets the contents to be publicly readable, cacheable by
    intermediaries with an expiration date a specified number
    of hours from when this job is run. (See above.)
    """

    out = StringIO.StringIO()
    with gzip.GzipFile(fileobj=out, mode="w") as f:
        f.write(contents)

    conn = S3Connection(calling_format=OrdinaryCallingFormat())
    bucket = conn.get_bucket('membership.texastribune.org')
    k = Key(bucket)
    k.key = filename
    expires = datetime.utcnow() + timedelta(hours=HOURS_TO_EXPIRE)
    expires = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
    k.set_contents_from_string(out.getvalue(),
            policy='public-read',
            headers={
                'Cache-Control': 'public',
                'Expires': '{}'.format(expires)
                })
    k.set_acl('public-read')
