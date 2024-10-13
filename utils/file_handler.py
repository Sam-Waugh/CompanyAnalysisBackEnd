import json
import os
import time
from clients.api_calls.chatgpt_client import ItemList

def save_to_json(data, filename=f"output/articles{int(time.time())}.json"):
    def convert_to_serializable(obj, seen=None):
        if seen is None:
            seen = set()  # Keep track of seen objects to detect circular references

        obj_id = id(obj)
        if obj_id in seen:
            return f"<Circular reference to {obj}>"  # Handle circular references
        seen.add(obj_id)
#def convert_to_serializable(obj):
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
    
# #write to json file
# with open(filename, 'w') as json_file:
#     json.dump(convert_to_serializable(data), json_file, indent=4) # indent4 for pretty printing 

# Ensure the output directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    try:
        # Write to json file with UTF-8 encoding and error handling
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(convert_to_serializable(data), json_file, ensure_ascii=False, indent=4)  # Pretty print with indent=4
        print(f"Data successfully saved to {filename}")         
    except Exception as e:
        print(f"Error saving data to {filename}: {e}")     