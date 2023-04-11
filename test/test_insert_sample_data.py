import pandas as pd
import requests
import json
import uuid

cars = requests.get(
    "https://raw.githubusercontent.com/vega/vega/main/docs/data/cars.json"
).json()

cars = {uuid.uuid4().hex: i for i in cars}

BASE_URL = "http://127.0.0.1:8000"
result = requests.put(f"{BASE_URL}/cars.json", json.dumps(cars))
print(result.status_code)
