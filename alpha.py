import requests
import os
from dotenv import load_dotenv
load_dotenv()

url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&apikey={os.getenv("ALPHA_VANTAGE_API_KEY")}'
r = requests.get(url)
data = r.json()

print(data)