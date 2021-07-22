# MINDER BATCH
___

### Description

This project is a POC for minder AWS Batch

## Pre-Requisites

### ECR 

Create an ECR repository in the sandbox environment. Script to push container is under `container.sh`. (below as well)

```
#!/bin/sh

# push image to ECR 
# get login 
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin {replace_vrtx_account_id}.dkr.ecr.us-east-1.amazonaws.com

# build docker image 
docker build --no-cache -t minder-batch .

# tag docker build
docker tag minder-batch:latest {replace_vrtx_account_id}.dkr.ecr.us-east-1.amazonaws.com/minder-batch:latest

# push docker image
docker push {replace_vrtx_account_id}.dkr.ecr.us-east-1.amazonaws.com/minder-batch:latest
```

### S3 Bucket 

Create an S3 bucket to upload file(s). A bucket for the POC is already created and added to IAM role(s).

### IAM Roles 

Two IAM roles are in place. 

1. ecsTaskExecutionRole
2. minderLambdaRole 

### AWS Batch

One set of each is already in-place for the POC. You may use these resources else create new ones as needed.

1. Compute Environment
2. Job Definition
3. Job Queue 

We submit job(s) to the queue via Lambda.

### Lambda 

Below is a sample JS function that gets invoked when a new file is uploaded onto s3. Also under `serverless/` directory. 

```
console.log('Loading function');

const aws = require('aws-sdk');

const s3 = new aws.S3({ apiVersion: '2006-03-01' });
const batch = new aws.Batch({ apiVersion: '2016-08-10' })

exports.handler = async (event, context) => {
    //console.log('Received event:', JSON.stringify(event, null, 2));

    // Get the object from the event and show its content type
    const bucket = event.Records[0].s3.bucket.name;
    const key = decodeURIComponent(event.Records[0].s3.object.key.replace(/\+/g, ' '));
    let params = {
        Bucket: bucket,
        Key: key,
    };
    try {
        const { ContentType, Body } = await s3.getObject(params).promise();
        console.log('CONTENT TYPE:', ContentType);
        console.log('CONTENT BODY:', Body.toString('ascii'))
        var fileData = Body.toString('ascii')
        const ts = Date.now()
        // submit a batch job 
        params = {
            jobDefinition: 'minder-parse-job-definition', /* required */
            jobName: 'minder-parse-data-job-' + ts, /* required */
            jobQueue: 'minder-parse-job-queue', /* required */
            containerOverrides: {
                command: [
                    'python',
                    './parse.py',
                    fileData
                ]
            }
        }
        const { data } = await batch.submitJob(params).promise()

        return { ContentType, Body, data }
    } catch (err) {
        console.log(err);
        const message = `Error getting object ${key} from bucket ${bucket}. Make sure they exist and your bucket is in the same region as this function.`;
        console.log(message);
        throw new Error(message);
    }
};
```

### Logs 

Logs get pushed onto CloudWatch.
