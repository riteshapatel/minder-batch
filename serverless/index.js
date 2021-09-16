console.log('Loading function');

const aws = require('aws-sdk');

const s3 = new aws.S3({ apiVersion: '2006-03-01' });
const batch = new aws.Batch({ apiVersion: '2016-08-10' })

exports.handler = async (event, context) => {
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
        const data = JSON.parse(Body.toString('ascii'))
        console.log('data ', data)

        const { files_location, worker_location, bucket } = data
        if (files_location && worker_location) {
            const ts = Date.now()
            const fullname = files_location.substring(files_location.lastIndexOf('/') + 1)
            const name = fullname.split(".")[0]
            const params = {
                jobDefinition: 'minder-job-definition-v1',
                jobName: 'bioformat-job-' + name + '-' + ts,
                jobQueue: 'minder-parse-job-queue',
                containerOverrides: {
                    command: [
                        'python3',
                        './manager.py',
                        worker_location,
                        files_location
                    ]
                }
            }

            console.log('job params ', params)
            await batch.submitJob(params).promise()
        }

        return { ContentType, Body }
    } catch (err) {
        console.log(err);
        const message = `Error getting object ${key} from bucket ${bucket}. Make sure they exist and your bucket is in the same region as this function.`;
        console.log(message);
        throw new Error(message);
    }
};
