import json
import time
from clients.api_calls.chatgpt_client import ItemList

def save_to_json(data, filename=f"output/articles{int(time.time())}.json"):
    def convert_to_serializable(obj):
        if isinstance(obj, ItemList):  # If it's an ItemList, convert to list of dictionaries
            return [convert_to_serializable(item) for item in obj]  # Recursive to handle nested objects
        elif isinstance(obj, tuple):  # If it's a tuple, convert to a list
            return [convert_to_serializable(item) for item in obj]  
        elif hasattr(obj, '__dict__'):  # If it has a __dict__ attribute, use that
            return {key: convert_to_serializable(value) for key, value in obj.__dict__.items()}  # Recursively convert object attributes
        elif isinstance(obj, list):  # Handle list if it's a nested structure
            return [convert_to_serializable(item) for item in obj]  
        elif isinstance(obj, dict):  # Handle dicts if it's a nested structure
            return {key: convert_to_serializable(value) for key, value in obj.items()}  
        else:
            return obj  # Return object directly if it's already serializable
        
    #write to json file
    with open(filename, 'w') as json_file:
        json.dump(convert_to_serializable(data), json_file, indent=4) # indent4 for pretty printing 
