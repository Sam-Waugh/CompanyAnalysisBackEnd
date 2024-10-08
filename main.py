from models.question import Question
from clients.api_calls.chatgpt_client import ChatgptClient
from clients.api_calls.perplexity_client import PerplexityClient

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.state.chat_gpt_client = ChatgptClient()
app.state.perplexity_client = PerplexityClient()


origins = [
    "http://localhost",
    "http://localhost:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/question")
async def ask_question(question: Question):
    answer = app.state.chat_gpt_client.ask_question(question.question)
    return f"Answer is: {answer}"

@app.post("/questionPerplexity")
async def ask_question(question: Question):
    answer = app.state.perplexity_client.ask_question(question.question)
    return f"Answer is: {answer}"