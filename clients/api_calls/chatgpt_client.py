import os
from openai import OpenAI

class ChatgptClient():
   

    def __init__(self):

        self.client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )

    def ask_question(self, question: str):
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": question,
                },
            ],
            model="gpt-4o-mini",
        )
        return chat_completion.choices[0].message.content
    

    def generate_response_with_model(self, messages, response_model):
        try:
            completion = self.client.beta.chat.completions.parse(
                model='gpt-4o-mini',  # Use 'gpt-4o-mini' as per your requirement
                messages=messages,
                response_format=response_model,
            )
            response = completion.choices[0].message.parsed
            return response
        except Exception as e:
            print(f"Error generating response: {e}")
            return None
