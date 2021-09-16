##############################################################################
# STEPS:
#   1) push files to s3
#   2) push manifest to s3 with url of the worker script
#   3) s3 action will pass in mrxs file name, script location to Batch
#   4) batch job will spin up a container with manager.py file
#   5) manager.py will pull script from s3 location for processing
#   6) manager.py will download mrxs resources from s3 and make it available
#      to worker.py
#   7) worker.py will perform zarr conversion and push converted files to s3
#   8) s3 action will spin off a second batch
#   9) batch job will spin up a container with manager.py file 
#  10) manager.py will pull script from s3 location for tiff conversion 
#  11) manager.py will download zarr resources from s3 and make it available
#      to worker.py
#  12) worker.py will perform tiff conversion and push converted files to s3
#  13) worker.py will send some sort of payload to minder / couch / pulsar
#############################################################################
import sys 
import boto3 
from botocore.exceptions import ClientError 
import json 
import glob, os
import shlex, subprocess


session = boto3.Session()
s3 = session.client('s3')
s3_res = boto3.resource('s3')

'''
parses s3 url
@param string - url
@return arr(string) - key and bucket
'''
def parseS3Url(url):
    arr = list()
    if "s3://" in url:
        arr = url.split("s3://")
        stripped = arr[1]
        arr = stripped.split("/")
    return arr

'''
downloads worker script and mrxs file from s3 locations  
'''
def processFiles():
    print("processing arguments...")
    if len(sys.argv) < 3:
        print("Missing worker and/or files location!")
        sys.exit()

    worker_location = sys.argv[1]
    files_location = sys.argv[2]

    print("script location set to: ", worker_location)
    print("files location set to: ", files_location)

    bucket, key = parseS3Url(worker_location)
    
    print("downloading worker script from ", bucket)
    s3.download_file(bucket, key, "worker.py")

    if (os.path.exists("worker.py")):
        from worker import main 
        result = main(files_location)

        if (result == True):
            print("File processing complete. Converted files pushed to S3")
            sys.exit() 
        else:
            print("Failure processing files")
            sys.exit()        
    else:
        print("Error downloading worker file from s3 bucket :(")
        sys.exit()
        
processFiles()
