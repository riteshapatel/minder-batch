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