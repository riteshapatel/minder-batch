import sys 
import boto3 
from botocore.exceptions import ClientError 
import json 
import glob, os
import shlex, subprocess

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

def main(files_location):
    session = boto3.Session()
    s3 = session.client('s3')

    # get zarr file location on S3
    print("parsing mrxs file s3 url...")
    bucket, key = parseS3Url(files_location)

    # parse bucket / key from s3 url
    print("downloading mrxs files from s3 bucket...")
    s3.download_file(bucket, key, key)
    cwd = os.getcwd()

    # download files for processing
    if os.path.exists(os.path.join(cwd, key)):
        objects = s3.list_objects(Bucket=bucket)['Contents']
        print("downloading objects...", objects)
        for obj in objects:
            filename = obj["Key"]
            if (filename[-1] == "/"):
                if not os.path.exists(os.path.join(cwd, filename)):
                    print('creating directory ')
                    os.makedirs(cwd + '/' + filename, exist_ok=True)
            else:
                s3.download_file(bucket, filename, cwd + '/' + filename)

        # list files in current working directory (just for reporting)
        cmd = shlex.split("ls -all")
        subprocess.run(cmd) 

        print("processing file: ", key)
        arr = key.split(".")
        justname = arr[0]  
        
        print("making zarr directory...")
        cmd = shlex.split("mkdir zarr")
        subprocess.run(cmd)

        print("processing zarr conversion...")
        # let zarr conversion complete
        print("waiting for zarr conversion to complete...")
        cmd = shlex.split("/opt/bioformats/bioformats2raw/bin/bioformats2raw  -r5 -c blosc ./" + key + " ./zarr/" + justname + ".zarr")
        result = subprocess.run(cmd)
        returncode = result.returncode

        cmd = shlex.split("ls -all")
        subprocess.run(cmd) 

        if (returncode == 0):
            print("zarr conversion complete!")
            # upload directory to S3
            print("pushing files to s3...")            
            for dirpath, dirs, files in os.walk("zarr"):
                for filename in files:
                    filepath = os.path.join(dirpath, filename) 
                    s3.upload_file(filepath, "3dhistec-panno250--anno", filepath)      

            print("files pushed to s3!")
            return True
        else:
            print("error in zarr conversion")
            return False        

    else:
        print("Error downloading mrxs files from s3")
        return False

