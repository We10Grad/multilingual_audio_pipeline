import boto3
import os
import logging
from botocore.exceptions import ClientError


# Initialize AWS clients
s3 = boto3.client('s3')
polly = boto3.client('polly')
translate = boto3.client('translate')
transcribe = boto3.client('transcribe')

# Set environment variables
bucket_name = os.environ['S3_BUCKET']
region = os.environ['AWS_REGION']
prefix = os.environ.get('PREFIX', 'beta')

# Create function to upload file to S3
def upload_file(file_name, bucket, object_name=None):
    # Upload a file to an S3 bucket

    #param file_name: File to upload
    #param bucket: Bucket to upload to
    #param object_name: S3 object name. If not specified then file_name is used
    
    #return: True if file was uploaded, else False

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    try:
        response = s3.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def transcribe_audio(job_name, media_uri, media_format='mp3', language_code='en-US'):
    response = transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        LanguageCode=language_code,
        MediaFormat=media_format,
        Media={'MediaFileUri': media_uri}
    )