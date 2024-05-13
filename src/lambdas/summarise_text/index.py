'''
Lambda function to generate summary for a given text file.
It uses Anthropic LLM to generate the summary.
It uses langchain_aws to invoke the Anthropic LLM.
It uses langchain to split the text into chunks and generate summary.
It uses s3 to store the summary in a new folder.
'''
import logging
import boto3
from langchain_aws import BedrockLLM
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain

BEDROCK_CLIENT = boto3.client(service_name='bedrock-runtime',region_name='us-east-1')
MODEL_ID = 'anthropic.claude-instant-v1'
s3 = boto3.client('s3')

logger = logging.getLogger()
logger.setLevel("INFO")

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

    inference_modifier = {
                      'max_tokens_to_sample':4096, 
                      "temperature":0.5,
                      "top_k":250,
                      "top_p":1,
                      "stop_sequences": ["\n\nHuman"]
                     }

    llm = BedrockLLM(model_id = MODEL_ID,
                     client = BEDROCK_CLIENT,
                     model_kwargs = inference_modifier)

    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n"], chunk_size=4000, chunk_overlap=100
    )

    docs = text_splitter.create_documents([file_content])
    summary_chain = load_summarize_chain(llm=llm, chain_type="map_reduce", verbose=False)

    output = summary_chain.invoke(docs)
    output_file = (file_key.split("/"))[-1]

    s3.put_object(
            Body=output.get('output_text'),
            Bucket=bucket_name,
            Key=f"output/summary/{output_file}"
        )
