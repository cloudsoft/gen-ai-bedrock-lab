'''
Lambda function to generate an email from the feedback received from the customer
'''
import boto3
from langchain_aws import BedrockLLM
from langchain.prompts import PromptTemplate

BEDROCK_CLIENT = boto3.client(service_name='bedrock-runtime',region_name='us-east-1')
MODEL_ID = 'anthropic.claude-instant-v1'
CONTENT_TYPE = 'application/json'

def handler(event, _):
    '''Lambda function entry point'''
    customer_feedback = event.get('customer_feedback')
    customer_name =  event.get('customer_name')
    service_manager = event.get('service_manager')

    inference_modifier = {
                      'max_tokens_to_sample':4096, 
                      "temperature":0.5,
                      "top_k":250,
                      "top_p":1,
                      "stop_sequences": ["\n\nHuman"]
                     }

    textgen_llm = BedrockLLM(model_id = MODEL_ID,
                            client = BEDROCK_CLIENT,
                            model_kwargs = inference_modifier)

    multi_var_prompt = PromptTemplate(
        input_variables=["customerServiceManager", "customerName", "feedbackFromCustomer"],
        template="""

    Human: Create an apology email from the Service Manager {customerServiceManager} to {customerName}
    in response to the following feedback that was received from the customer: 
    <customer_feedback>
    {feedbackFromCustomer}
    </customer_feedback>
    Do not mention any concrete actions, neither the company name.
    Try to emphasise our commitment in improving the situation.

    Assistant:"""
    )

    # Pass in values to the input variables
    prompt = multi_var_prompt.format(customerServiceManager=service_manager,
                                     customerName=customer_name,
                                     feedbackFromCustomer=customer_feedback)

    response = textgen_llm.invoke(prompt)

    email = response[response.index('\n')+1:]

    print(email)
    return email
