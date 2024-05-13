'''
This lambda function is triggered by an S3 event. It will download the file from S3,
convert it to mp3 using Amazon Polly, and then upload the mp3 to another path in the
S3 bucket.
'''
import logging
import boto3

logger = logging.getLogger()
logger.setLevel("INFO")
s3 = boto3.client('s3')
polly = boto3.client('polly')

def handler(event, _):
    '''Lambda function entry point'''

    bucket_name = event['Records'][0]['s3']['bucket']['name']
    file_key = event['Records'][0]['s3']['object']['key']

    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        file_content = response['Body'].read().decode('utf-8')
    except Exception as e:
        logger.error("Error getting object: %s", e)
        return

    response = polly.synthesize_speech(
        Text=file_content,
        OutputFormat='mp3',
        VoiceId='Joanna'
    )

    # Get the audio stream
    audio_stream = response['AudioStream']
    audio_name = (file_key.split("/"))[-1]
    audio_key = f"output/audio/{audio_name.split('.')[0]}.mp3"

    s3.upload_fileobj(audio_stream, bucket_name, audio_key)
