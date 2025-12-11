
import json
with open('config.json', 'r') as f:
    config = json.load(f)
    
for station in config['stations']:
    if station['name'] == 'פוקד':
        print(f"Poked ID: {station['id']}, Hidden: {station['hidden']}")