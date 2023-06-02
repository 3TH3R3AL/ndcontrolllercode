from controllers import Caen, MHV4
import json
import time

with open('config.json','r') as f:
    config = json.loads(f.read())

