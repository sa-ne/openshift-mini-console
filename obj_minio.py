# pylint: disable=redefined-outer-name
'''
Functions to Interact with S3 via minio.
'''
import io
import json
import sys
from minio import Minio
from minio.error import S3Error
from flask import jsonify

check_bucket_count = 20


def create_client(**kwargs):
    '''creates s3 client'''
    client = Minio(**kwargs)
    return client


def check_bucket_exists(client, bucket_name):
    '''Check bucket exists'''
    return client.bucket_exists(bucket_name)


def create_bucket_ifnotexists(client, bucket_name):
    '''Creates bucket if not exists'''
    found = client.bucket_exists(bucket_name)
    if not found:
        client.make_bucket(bucket_name)
    return client.bucket_exists(bucket_name)


def list_objects(client, bucket_name):
    '''Return a list of objects information in bucket'''
    if check_bucket_exists(client=client, bucket_name=bucket_name):
        temp_list = []
        objects = client.list_objects(bucket_name)
        for obj in objects:
            temp_list.append(obj)
        return temp_list


def get_all_objects_python(client, bucket_name):
    '''Returns a list of all objects in the bucket'''
    # Get list of Objects
    temp_list = list_objects(client=client, bucket_name=bucket_name)
    temp_response = []
    for item in temp_list:
        try:
            response = client.get_object(bucket_name, item.object_name)
            obj = json.loads(response.data)
            temp_response.append(obj)
            # Read data from response.
        finally:
            response.close()
            response.release_conn()
    return temp_response


def put_objects_binary(client, bucket_name, object_name, cluster_info):
    '''Put non file data into bucket by converting to binary'''
    count = 0
    # Adding loop while to add some delay, while testing with s3 , noticed aws delay before bucket was ready
    while check_bucket_exists(client=client,
                              bucket_name=bucket_name) and count != check_bucket_count:
        count += 1
    if check_bucket_exists(client=client, bucket_name=bucket_name):
        str_cluster_info = json.dumps(cluster_info)
        data = io.BytesIO(str.encode(str_cluster_info))
        length = len(data.getvalue())
        result = client.put_object(bucket_name, object_name, data, length)
        return result


if __name__ == "__main__":
    client = create_client(endpoint="endpoint",
                           access_key="accesskey", secret_key="secretkey")
    check = client.bucket_exists(client, "test")
