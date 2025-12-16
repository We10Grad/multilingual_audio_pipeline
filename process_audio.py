import boto3
import os
import time
import json
import requests

bucket_name = os.environ['S3_BUCKET']
region = os.environ['AWS_REGION']
prefix = os.environ.get('PREFIX', 'beta')

transcribe = boto3.client('transcribe')
translate = boto3.client('translate')
polly = boto3.client('polly')
s3 = boto3.client('s3')

def upload_to_s3(bucket_name, file_name, object_name=None):
    if object_name is None:
        object_name = file_name
    s3.upload_file(file_name, bucket_name, object_name)

def transcribe_audio(job_name, media_uri, media_format='mp3', language_code='en-US'):
    response = transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': media_uri},
        MediaFormat=media_format,
        LanguageCode=language_code
    )
    return response

def translate_text(text, source_lang='en', target_lang='es'):
    response = translate.translate_text(
        Text=text,
        SourceLanguageCode=source_lang,
        TargetLanguageCode=target_lang
    )
    return response['TranslatedText']

def synthesize_speech(text, output_format='mp3', voice_id='Matthew'):
    response = polly.synthesize_speech(
        Text=text,
        OutputFormat=output_format,
        VoiceId=voice_id
    )
    return response['AudioStream'].read()

def get_mp3_files(folder):
    files = os.listdir(folder)
    mp3_files = []
    for file in files:
        if file.endswith('.mp3'):
            mp3_files.append(file)
    return mp3_files

def wait_for_transcription(job_name):
    job_done = False
    while job_done == False:
        time.sleep(10)
        status_response = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        job_status = status_response['TranscriptionJob']['TranscriptionJobStatus']
        if job_status == 'COMPLETED':
            job_done = True
            print('Transcription completed')
        elif job_status == 'FAILED':
            print('Transcription failed')
            break
    return status_response

def get_transcript_text(transcript_uri):
    response = requests.get(transcript_uri)
    transcript_data = response.json()
    transcript_text = transcript_data['results']['transcripts'][0]['transcript']
    return transcript_text

def save_text_file(filename, text):
    with open(filename, 'w') as f:
        f.write(text)

def save_audio_file(filename, audio_data):
    with open(filename, 'wb') as f:
        f.write(audio_data)

def main():
    target_language = os.environ.get('TARGET_LANG', 'es')
    audio_folder = 'audio_inputs'
    
    mp3_files = get_mp3_files(audio_folder)
    
    for mp3_file in mp3_files:
        print(f'Processing {mp3_file}')
        
        file_path = os.path.join(audio_folder, mp3_file)
        base_name = mp3_file.replace('.mp3', '')
        
        s3_key = f'{prefix}/audio_inputs/{mp3_file}'
        upload_to_s3(bucket_name, file_path, s3_key)
        print(f'Uploaded to S3: {s3_key}')
        
        media_uri = f's3://{bucket_name}/{s3_key}'
        job_name = f'{base_name}_{int(time.time())}'
        
        transcribe_audio(job_name, media_uri)
        print(f'Started transcription job: {job_name}')
        
        status_response = wait_for_transcription(job_name)
        
        job_status = status_response['TranscriptionJob']['TranscriptionJobStatus']
        if job_status == 'FAILED':
            continue
        
        transcript_uri = status_response['TranscriptionJob']['Transcript']['TranscriptFileUri']
        transcript_text = get_transcript_text(transcript_uri)
        print(f'Transcript: {transcript_text[:100]}...')
        
        transcript_filename = f'{base_name}.txt'
        save_text_file(transcript_filename, transcript_text)
        transcript_s3_key = f'{prefix}/transcripts/{transcript_filename}'
        upload_to_s3(bucket_name, transcript_filename, transcript_s3_key)
        print(f'Uploaded transcript to S3: {transcript_s3_key}')
        
        translated_text = translate_text(transcript_text, 'en', target_language)
        print(f'Translated text: {translated_text[:100]}...')
        
        translation_filename = f'{base_name}_{target_language}.txt'
        save_text_file(translation_filename, translated_text)
        translation_s3_key = f'{prefix}/translations/{translation_filename}'
        upload_to_s3(bucket_name, translation_filename, translation_s3_key)
        print(f'Uploaded translation to S3: {translation_s3_key}')
        
        audio_data = synthesize_speech(translated_text, 'mp3', 'Miguel')
        
        output_audio_filename = f'{base_name}_{target_language}.mp3'
        save_audio_file(output_audio_filename, audio_data)
        output_audio_s3_key = f'{prefix}/audio_outputs/{output_audio_filename}'
        upload_to_s3(bucket_name, output_audio_filename, output_audio_s3_key)
        print(f'Uploaded output audio to S3: {output_audio_s3_key}')
        
        print(f'Finished processing {mp3_file}')

if __name__ == '__main__':
    main()