import os
from openai import OpenAI

class chatgpt_client():

    def __init__(self):

        self.client = OpenAI(
            # This is the default and can be omitted
            api_key=os.environ.get("OPENAI_API_KEY"),
        )

    def ask_question(self, question: str):
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": question,
                }
            ],
            model="gpt-4o-mini",
        )
        return chat_completion.choices[0].message.content