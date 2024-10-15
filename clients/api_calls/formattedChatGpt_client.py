import json
import os
from chatgpt_client import ChatgptClient
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
load_dotenv()

openAPIClient = ChatgptClient()

class ItemList(BaseModel):
    items: List[str]

messages = [
{
    "role": "system", 
    "content": "You are an expert in proposing high level categories for evaluation criteria for a given task."
    },
{
    "role": "user", 
    "content": f"Please provide a list of high level categories of criteria for the task: types of events in a life '. For each category, include: - A description of the criterion."
    }
]


# def generate_response_with_model(messages, response_model):

#     try:
#         completion = openai.beta.chat.completions.parse(
#             model='gpt-4o-mini',  # Use 'gpt-4o-mini' as per your requirement
#             messages=messages,
#             response_format=response_model,
#         )
#         response = completion.choices[0].message.parsed
#         return response
#     except Exception as e:
#         print(f"Error generating response: {e}")
#         return None
    

response = openAPIClient.generate_response_with_model(messages, ItemList)

print(response)

if response:
    with open("output/test.json", 'w') as f:
        json.dump(response.dict(), f, indent=2)



#CAN REMOVE WHOLE FILE - LOGIC IN TESTING 