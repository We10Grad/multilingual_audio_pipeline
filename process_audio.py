import boto 3

transcribe = boto3.client('transcribe')
translate = boto3.client('translate')
polly = boto3.client('polly')
s3 - boto3.client('s3')

def upload_to_s3(bucket_name, file_name, object_name=None):
    if object_name is None:
        object_name = file_name
    s3.upload_file(file_name, bucket_name, object_name)

def transcribe_audio(job_name, media_uri, media_format='mp3', language_code='en-US'):
    response = transcribe.start_transcription_job(**)





def synthesize_speech(text, output_format='mp3', voice_id='Matthew'):
    response = polly.sythesize_speech(**)