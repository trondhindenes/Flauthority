import os
import datetime
import random, string
import boto
from boto.s3.key import Key

def randomword(length):
   return ''.join(random.choice(string.lowercase) for i in range(length))

def sign(bucket, path, access_key, secret_key, https, expiry, aws_s3_host_name=None):
    c = boto.S3Connection(access_key, secret_key)
    return c.generate_url(
        expires_in=long(expiry),
        method='GET',
        bucket=bucket,
        key=path,
        query_auth=True,
        force_http=(not https)
    )

def upload_to_s3(access_key, access_key_secret, file_path, dest_file_name, bucket_name, aws_s3_host_name=None, sign=False):
    conn = boto.connect_s3(aws_access_key_id=access_key, aws_secret_access_key=access_key_secret, host=aws_s3_host_name)
    bucket = conn.get_bucket(bucket_name, validate=True)

    k = Key(bucket)
    k.key = dest_file_name
    sent = k.set_contents_from_filename(file_path)
    if sign is True:
        url = k.generate_url(expires_in=300)
    return url

def download_from_s3(access_key, access_key_secret, dest_file_name, dest_file_path,  bucket_name, src_file_name, aws_s3_host_name=None):
    conn = boto.connect_s3(aws_access_key_id=access_key, aws_secret_access_key=access_key_secret, host=aws_s3_host_name)
    bucket = conn.get_bucket(bucket_name, validate=True)
    for l in bucket.list():
        key_string = str(l.key)
        if key_string == src_file_name:
            l.get_contents_to_filename(os.path.join(dest_file_path,dest_file_name))

def get_utc_string():
    now = datetime.datetime.utcnow().isoformat()
    now = now.replace(":","_")
    return now


