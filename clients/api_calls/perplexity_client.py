import os
from openai import OpenAI

class PerplexityClient():
    
    def __init__(self):

        self.client = OpenAI(
            api_key=os.environ.get("PERPLEXITY_API_KEY"),
            base_url="https://api.perplexity.ai"
        )

    def ask_question(self, question: str):
        chat_completion = self.client.chat.completions.create(
            messages = [
                {
                    "role": "system",
                    "content": "You are an AI assistant. Provide helpful and detailed responses."
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            model="llama-3.1-sonar-small-128k-online",
            # return_citations=True,
        )
        return chat_completion.choices[0].message.content