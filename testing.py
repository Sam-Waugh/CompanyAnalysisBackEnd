from dotenv import load_dotenv
from utils.file_handler import save_to_json
from clients.scrapers.deloitte_scraper import scrape_deloitte
#from clients.api_calls.formattedChatGpt_client import response
from clients.api_calls.chatgpt_client import ChatgptClient, ItemList

load_dotenv()


#Deloitte data scraping print title & save to file
data = scrape_deloitte()
# titles = data["titles"]
# print(titles)
headlines = data["headlines"]

save_to_json(data)

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

chatgptClient = ChatgptClient()

#ChatGPT formatted prompt response save to file 
response = chatgptClient.generate_response_with_model(messages, ItemList)

#print(response)
#save_to_json(response)