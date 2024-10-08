import json
import time

def save_to_json(data, filename=f"output/articles{int(time.time())}.json"):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file)
