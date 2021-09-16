import sys 
import boto3 
from botocore.exceptions import ClientError 
import json 
import glob, os
import shlex, subprocess

def parseS3Url(url):
    arr = list()
    if "s3://" in url:
        arr = url.split("s3://")
        stripped = arr[1]
        arr = stripped.split("/", 1)
    return arr

def main(files_location):
    session = boto3.Session()
    s3 = session.client('s3')

    # parse files location to retrieve bucket / key...
    parsed = parseS3Url(files_location)
    bucket = parsed[0]
    key = parsed[1]

    # extract file name
    # TODO: make file name part of JSON payload and avoid the logic below
    if ("/" in key):
        tkey = key
        if (key[-1] == "/"):
            tkey = key[:-1]

        arr = tkey.split("/")
        filename = arr[-1]
        justname = filename.split(".")[0]
    else:
        justname = key.split(".")[0]

    # create a directory for zarr download
    if (os.path.exists(key) == False):
        os.makedirs(key)

    # using command line s3 api to pull all files with nested directories
    # TODO: use boto3 to pull file recursively (if important)
    cmd = shlex.split("aws s3 cp --recursive " + files_location + " " + key)
    result = subprocess.run(cmd)

    returncode = result.returncode

    if (returncode == 0):
        cwd = os.getcwd()

        if os.path.exists(os.path.join(cwd, key)):
            # create ometiff directory on the container
            cmd = shlex.split("mkdir ometiff") 
            result = subprocess.run(cmd) 

            # perform ometiff conversion
            cmd = shlex.split("/opt/bioformats/raw2ometiff/bin/raw2ometiff --quality=85 --compression=JPEG-2000 -p ./" + key + " ./ometiff/" + justname + ".tiff")

            # local container test
            # cmd = shlex.split("docker run -it -v /Users/patelr5/code/rap-batch/mrxs/workers/tiff/results:/results -v /Users/patelr5/code/rap-batch/mrxs/tiff:/tiff e32e383016b6 /opt/bioformats/raw2ometiff/bin/raw2ometiff --quality=85 --compression=JPEG-2000 -p /results/SJS_0011.zarr/ /tiff/SJS_0011.tiff")
            print("waiting for tiff conversion to complete...")
            result = subprocess.run(cmd)            
            returncode = result.returncode
            # let tiff conversion complete
 
            if (returncode == 0):
                print("tiff conversion complete!")

                cmd = shlex.split("ls -all")
                subprocess.run(cmd) 

                # upload directory to S3
                print("pushing files to s3...")
                if (returncode == 0):
                    for dirpath, dirs, files in os.walk("ometiff"):
                        for filename in files:
                            filepath = os.path.join(dirpath, filename) 
                            s3.upload_file(filepath, bucket, filepath)      

                    print("tiff files pushed to s3!")
                    return True
                else:
                    print("error pushing tiff files to s3!")
                    return False
            else:
                print("Error in tiff conversion")
                return False
        else:
            print("Error downloading zarr (" + key + ") resources from s3 bucket ", bucket)
            return False
    else:
        print("zarr resources not found on the container")
        return False
